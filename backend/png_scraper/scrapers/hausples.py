"""
png_scraper/scrapers/hausples.py
─────────────────────────────────────────────────────────────────────────────
HausplesScraper  —  Adaptive scraper for Hausples-powered portals.
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

DEFAULT_BASE_URL = "https://www.hausples.com.pg"
DEFAULT_SOURCE   = "Hausples"

CARD_SELECTORS = [
    "article",
    "article.property-card",
    "div[data-testid='property-card']",
    ".property-card",
    "[class*='PropertyCard']",
    "li[class*='listing']",
]

TITLE_SELECTORS = [
    ".copy-wrapper .heading",
    "h2.property-card__title",
    ".listing-title",
    "h2",
    "h3",
]

PRICE_SELECTORS = [
    ".price .value",
    ".price",
    ".property-card__price",
    "span[class*='Price']",
]

LOCATION_SELECTORS = [
    ".address",
    ".property-card__location",
    ".location",
]

LINK_SELECTORS = [
    "a.carousel-wrap",
    "a.property-card__link",
    "a[href*='/property/']",
    "a",
]

NEXT_PAGE_SELECTORS = [
    "a[rel='next']",
    "a.next",
    "button[aria-label='Next']",
    ".pagination-next",
]

async def _first_text(element, selectors: list[str]) -> str:
    for sel in selectors:
        try:
            el = await element.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                if txt: return txt
        except Exception: pass
    return ""

async def _first_attr(element, selectors: list[str], attr: str) -> str:
    for sel in selectors:
        try:
            el = await element.query_selector(sel)
            if el:
                val = (await el.get_attribute(attr) or "").strip()
                if val: return val
        except Exception: pass
    return ""

class HausplesScraper(PNGScraper):
    IS_VERIFIED = True

    def __init__(self, base_url: str = DEFAULT_BASE_URL, source_site: str = DEFAULT_SOURCE, max_pages: int = 5, headless: bool = True, mode: str = "rent"):
        super().__init__(headless)
        self.base_url = base_url.rstrip("/")
        self.SOURCE_SITE = source_site
        self.max_pages = max_pages
        self.mode = mode

    async def _parse_card(self, card) -> Optional[Listing]:
        title    = await _first_text(card, TITLE_SELECTORS)
        price_r  = await _first_text(card, PRICE_SELECTORS)
        location = await _first_text(card, LOCATION_SELECTORS)
        href     = await _first_attr(card, LINK_SELECTORS, "href")

        if not href: return None
        url = href if href.startswith("http") else f"{self.base_url}{href}"
        raw_text = await card.inner_text()

        if not title:
            slug = href.strip("/").split("/")[-1]
            title = slug.replace("-", " ").title() if slug else f"{self.SOURCE_SITE} Listing"

        if location:
            location = location.replace("", "").strip()

        return make_listing(
            source_site = self.SOURCE_SITE,
            title       = title,
            price_raw   = price_r,
            location    = location,
            listing_url = url,
            is_verified = True,
            raw_text    = raw_text,
        )

    async def scrape(self, context, on_progress=None) -> list[Listing]:
        page = self._page
        results: list[Listing] = []
        seen_ids: set[str] = set()
        base_search_url = f"{self.base_url}/{self.mode}/"

        await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2,ttf}", lambda r: r.abort())

        for page_num in range(1, self.max_pages + 1):
            url = base_search_url if page_num == 1 else f"{base_search_url}?page={page_num}"
            log.info(f"[{self.SOURCE_SITE}] {self.mode.upper()} Page {page_num}/{self.max_pages} → {url}")

            if not await self._goto(url, wait_until="load"):
                break

            # Wait for lazy content
            await asyncio.sleep(3)
            await scroll_page(page, scrolls=random.randint(3, 5))
            await move_mouse(page)

            cards = []
            for sel in CARD_SELECTORS:
                try:
                    await page.wait_for_selector(sel, timeout=15_000)
                    cards = await page.query_selector_all(sel)
                    if cards:
                        log.info(f"[{self.SOURCE_SITE}] Selector '{sel}' matched {len(cards)} cards")
                        break
                except Exception: pass

            if not cards:
                log.warning(f"[{self.SOURCE_SITE}] No cards found on page {page_num}")
                break

            new_count = 0
            for card in cards:
                try:
                    listing = await self._parse_card(card)
                    if listing and listing.listing_id not in seen_ids:
                        if "/new-developments/" in listing.listing_url: continue
                        seen_ids.add(listing.listing_id)
                        results.append(listing)
                        new_count += 1
                except Exception as e:
                    log.debug(f"[{self.SOURCE_SITE}] Card parse error: {e}")

            log.info(f"[{self.SOURCE_SITE}] Running total: {len(results)} listings")
            if on_progress: on_progress(new_count, page_num)

            has_next = False
            for sel in NEXT_PAGE_SELECTORS:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=2_000):
                        has_next = True
                        break
                except Exception: pass

            if not has_next: break
            await sleep_human(1.5, 3.5)

        return results
