"""
png_scraper/scrapers/professionals.py
─────────────────────────────────────────────────────────────────────────────
ProfessionalsScraper  —  https://theprofessionals.com.pg/rent/

The Professionals PNG uses a WordPress/Elementor-based real estate theme
(typically RealHomes or similar). Cards are rendered server-side, so no
JS-wait headaches — but we still use Playwright for stealth.

Selector strategy:
    Cards  : article.property-item | .property_item | [class*="property"]
    Title  : .item-title h2 | .listing_title | h2[class*="title"] a
    Price  : .item-price | .price | [class*="price"]
    Location: .item-address | .location | [class*="address"] | [class*="location"]
    Beds   : .rh_meta__bedrooms | .bedrooms | [class*="bed"]
    Link   : article a[href]:first-of-type | .item-title a
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

log = logging.getLogger("png_scraper.professionals")

BASE_URL    = "https://theprofessionals.com.pg"
RENT_URL    = f"{BASE_URL}/rent/"
SOURCE_SITE = "The Professionals"

# ── selectors (ordered by specificity – most reliable first) ─────────────────

CARD_SELECTORS = [
    "article.property-item",
    ".property_item",
    "article[class*='property']",
    "div[class*='PropertyListing']",
    "div[class*='property-listing']",
    ".listings-container article",
    "ul.properties-list li",
    "div.item-body",                   # RealHomes theme
]

TITLE_SELECTORS = [
    ".item-title h2 a",
    ".item-title h3 a",
    ".listing_title a",
    "h2[class*='title'] a",
    "h3[class*='title'] a",
    ".rh_prop_card__title a",         # RealHomes
    "h2 a",
    "h3 a",
]

PRICE_SELECTORS = [
    ".item-price span",
    ".item-price",
    ".price",
    "[class*='price']",
    ".rh_prop_card__price",
    "[data-price]",
    "span[class*='amount']",
]

LOCATION_SELECTORS = [
    ".item-address",
    ".location",
    "[class*='address']",
    "[class*='location']",
    ".rh_prop_card__location",
    "[itemprop='address']",
    ".suburb",
    "span[class*='city']",
]

BEDS_SELECTORS = [
    ".rh_meta__bedrooms",
    ".bedrooms",
    "[class*='bed']",
    ".meta-bedrooms",
    "[title*='Bedroom']",
    "li[class*='bed']",
]

LINK_SELECTORS = [
    ".item-title a",
    "h2 a[href*='/property/']",
    "h3 a[href*='/property/']",
    "a.rh_prop_card__link",
    "a[href*='/listing']",
    "a[href*='/rent/']",
    "article > a",
]

NEXT_SELECTORS = [
    "a.next",
    "a[rel='next']",
    ".pagination .next",
    "[class*='pagination'] a[aria-label='Next']",
    "[class*='nav-next'] a",
    "a:has-text('Next')",
    "a:has-text('›')",
]


async def _first_text(el, selectors: list[str]) -> str:
    for sel in selectors:
        try:
            child = await el.query_selector(sel)
            if child:
                txt = (await child.inner_text()).strip()
                if txt:
                    return txt
        except Exception:
            pass
    return ""


async def _first_attr(el, selectors: list[str], attr: str) -> str:
    for sel in selectors:
        try:
            child = await el.query_selector(sel)
            if child:
                val = (await child.get_attribute(attr) or "").strip()
                if val:
                    return val
        except Exception:
            pass
    return ""


async def _parse_card(card, page_base: str = BASE_URL) -> Optional[Listing]:
    title    = await _first_text(card, TITLE_SELECTORS)
    price_r  = await _first_text(card, PRICE_SELECTORS)
    location = await _first_text(card, LOCATION_SELECTORS)
    href     = await _first_attr(card, LINK_SELECTORS, "href")

    if not href:
        # Last resort: grab any <a> in the card
        try:
            a = await card.query_selector("a[href]")
            if a:
                href = (await a.get_attribute("href") or "").strip()
        except Exception:
            pass

    if not href:
        return None

    url = href if href.startswith("http") else f"{page_base}{href}"

    # Beds from dedicated element
    beds_text = await _first_text(card, BEDS_SELECTORS)

    # Full card raw text for suburb/bedroom fallback
    raw = f"{title} {price_r} {location} {beds_text}"

    if not title:
        title = f"Property — {location}" if location else "The Professionals Listing"

    return make_listing(
        source_site = SOURCE_SITE,
        title       = title,
        price_raw   = price_r,
        location    = location,
        listing_url = url,
        is_verified = True,
        raw_text    = raw,
    )


class ProfessionalsScraper(PNGScraper):
    """
    Dedicated scraper for https://theprofessionals.com.pg/rent/

    Features:
    • WordPress/RealHomes theme selector strategy
    • Handles both grid and list layout variants
    • Pagination via wp-pagenavi or standard WordPress pagination
    • Property image blocking for bandwidth efficiency
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

        await page.route("**/*.{png,jpg,jpeg,gif,webp,woff,woff2,ttf}", lambda r: r.abort())

        for page_num in range(1, self.max_pages + 1):
            # WordPress pagination: /rent/page/2/ or ?paged=2
            if page_num == 1:
                url = RENT_URL
            else:
                url = f"{RENT_URL}page/{page_num}/"

            log.info(f"[Professionals] Page {page_num}/{self.max_pages} → {url}")

            if not await self._goto(url):
                break

            await scroll_page(page, scrolls=random.randint(2, 4))
            await move_mouse(page)

            # Detect working card selector
            cards = []
            for sel in CARD_SELECTORS:
                try:
                    await page.wait_for_selector(sel, timeout=7_000)
                    cards = await page.query_selector_all(sel)
                    if cards:
                        log.info(f"[Professionals] '{sel}' → {len(cards)} cards")
                        break
                except Exception:
                    pass

            if not cards:
                log.warning(f"[Professionals] No cards on page {page_num}")
                break

            for card in cards:
                try:
                    listing = await _parse_card(card)
                    if listing and listing.listing_id not in seen_ids:
                        seen_ids.add(listing.listing_id)
                        results.append(listing)
                except Exception as e:
                    log.debug(f"[Professionals] Parse error: {e}")

            log.info(f"[Professionals] Running total: {len(results)}")

            # WordPress next-page detection
            has_next = False
            for sel in NEXT_SELECTORS:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2_000):
                        has_next = True
                        break
                except Exception:
                    pass

            if not has_next:
                log.info("[Professionals] No next page — done")
                break

            await sleep_human(2.5, 5.0)

        return results
