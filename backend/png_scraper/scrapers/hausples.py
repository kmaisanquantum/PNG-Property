"""
png_scraper/scrapers/hausples.py
─────────────────────────────────────────────────────────────────────────────
HausplesScraper  —  https://www.hausples.com.pg/rent/

Hausples is built on a React SPA. Strategy:
    1. Navigate the /rent/ listing grid.
    2. Wait for JS to render the property cards.
    3. Extract card-level data (title, price, location, href).
    4. Optionally deep-dive each listing for extra fields.
    5. Paginate via the "next page" button until exhausted.

Selector notes (valid as of 2024 — update if site redesigns):
    Cards  : article.property-card  |  div[data-testid="property-card"]
    Title  : h2.property-card__title  |  .listing-title
    Price  : .property-card__price  |  [class*="price"]
    Location: .property-card__location  |  [class*="location"]
    Link   : a.property-card__link  |  a[href*="/property/"]
"""

from __future__ import annotations

import asyncio
import random
import logging
from typing import Optional

from png_scraper.engine import (
    PNGScraper,
    Listing,
    make_listing,
    sleep_human,
    scroll_page,
    move_mouse,
)

log = logging.getLogger("png_scraper.hausples")

BASE_URL    = "https://www.hausples.com.pg"
RENT_URL    = f"{BASE_URL}/rent/"
SOURCE_SITE = "Hausples"

# ── selector groups (try in order until one matches) ─────────────────────────

CARD_SELECTORS = [
    "article.property-card",
    "div[data-testid='property-card']",
    ".property-card",
    "[class*='PropertyCard']",
    "li[class*='listing']",
]

TITLE_SELECTORS = [
    "h2.property-card__title",
    "h2[class*='title']",
    "h3[class*='title']",
    ".listing-title",
    "[data-testid='listing-title']",
    "h2",
    "h3",
]

PRICE_SELECTORS = [
    ".property-card__price",
    "[class*='price']",
    "[data-testid='property-price']",
    "span[class*='Price']",
    "[class*='listing-price']",
]

LOCATION_SELECTORS = [
    ".property-card__location",
    "[class*='location']",
    "[class*='suburb']",
    "[class*='address']",
    "[data-testid='property-location']",
    ".location",
]

LINK_SELECTORS = [
    "a.property-card__link",
    "a[href*='/property/']",
    "a[href*='/listing/']",
    "a[class*='card']",
    "a",
]

NEXT_PAGE_SELECTORS = [
    "a[rel='next']",
    "a[aria-label='Next page']",
    "button[aria-label='Next']",
    ".pagination-next",
    "[class*='pagination'] a:last-child",
    "[data-testid='pagination-next']",
]


async def _first_text(element, selectors: list[str]) -> str:
    """Try each CSS selector, return the first non-empty inner_text."""
    for sel in selectors:
        try:
            el = await element.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                if txt:
                    return txt
        except Exception:
            pass
    return ""


async def _first_attr(element, selectors: list[str], attr: str) -> str:
    """Try each CSS selector, return the first non-empty attribute value."""
    for sel in selectors:
        try:
            el = await element.query_selector(sel)
            if el:
                val = (await el.get_attribute(attr) or "").strip()
                if val:
                    return val
        except Exception:
            pass
    return ""


async def _parse_card(card, page_url: str) -> Optional[Listing]:
    """Extract one Listing from a Hausples property card element."""
    title    = await _first_text(card, TITLE_SELECTORS)
    price_r  = await _first_text(card, PRICE_SELECTORS)
    location = await _first_text(card, LOCATION_SELECTORS)
    href     = await _first_attr(card, LINK_SELECTORS, "href")

    if not href:
        return None
    url = href if href.startswith("http") else f"{BASE_URL}{href}"

    # Pull any additional text for suburb / bedroom detection
    raw_text = await _first_text(card, ["*"])   # full card text

    if not title:
        title = f"Property — {location}" if location else "Hausples Listing"

    return make_listing(
        source_site = SOURCE_SITE,
        title       = title,
        price_raw   = price_r,
        location    = location,
        listing_url = url,
        is_verified = True,
        raw_text    = raw_text,
    )


class HausplesScraper(PNGScraper):
    """
    Dedicated scraper for https://www.hausples.com.pg/rent/

    Features:
    • Multiple fallback card selectors (handles site redesigns)
    • Automatic pagination (up to max_pages)
    • Lazy-load scroll trigger before extracting cards
    • Block image/font requests for speed
    """

    SOURCE_SITE = SOURCE_SITE
    IS_VERIFIED = True

    def __init__(self, max_pages: int = 5, headless: bool = True):
        super().__init__(headless)
        self.max_pages = max_pages

    async def scrape(self, context) -> list[Listing]:
        page = self._page
        results: list[Listing] = []
        seen_ids: set[str] = set()

        # Block heavy assets we don't need
        await page.route(
            "**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf,otf,eot}",
            lambda r: r.abort()
        )

        for page_num in range(1, self.max_pages + 1):
            url = RENT_URL if page_num == 1 else f"{RENT_URL}?page={page_num}"
            log.info(f"[Hausples] Page {page_num}/{self.max_pages} → {url}")

            if not await self._goto(url):
                break

            # Scroll to trigger lazy-loaded cards
            await scroll_page(page, scrolls=random.randint(3, 5))
            await move_mouse(page)

            # Detect which card selector works on this page
            cards = []
            for sel in CARD_SELECTORS:
                try:
                    await page.wait_for_selector(sel, timeout=8_000)
                    cards = await page.query_selector_all(sel)
                    if cards:
                        log.info(f"[Hausples] Selector '{sel}' matched {len(cards)} cards")
                        break
                except Exception:
                    pass

            if not cards:
                log.warning(f"[Hausples] No cards found on page {page_num} — stopping pagination")
                break

            for card in cards:
                try:
                    listing = await _parse_card(card, url)
                    if listing and listing.listing_id not in seen_ids:
                        seen_ids.add(listing.listing_id)
                        results.append(listing)
                except Exception as e:
                    log.debug(f"[Hausples] Card parse error: {e}")

            log.info(f"[Hausples] Running total: {len(results)} listings")

            # Check for next page
            has_next = False
            for sel in NEXT_PAGE_SELECTORS:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2_000):
                        has_next = True
                        break
                except Exception:
                    pass

            if not has_next:
                log.info("[Hausples] No next-page button found — pagination complete")
                break

            await sleep_human(2.0, 4.5)

        return results
