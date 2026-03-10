"""
png_scraper/scrapers/general_agency.py
─────────────────────────────────────────────────────────────────────────────
GeneralAgencyScraper  —  Adaptive scraper for remaining PNG agency sites:

    • https://marketmeri.com/real-estate
    • http://www.sre.com.pg
    • https://www.century21.com.pg
    • https://www.raywhitepng.com
    • http://www.pacificpalmsproperty.com.pg
    • http://www.dac.com.pg
    • http://www.aaaproperties.com.pg
    • http://www.arthurstrachan.com.pg

Strategy: Try a ranked cascade of generic CSS selectors that cover the
most common real estate WordPress themes (RealHomes, Estatik, Easy
Property Listings, WP Property, AgentPress Pro, etc.).

If a site has a known quirk, override it via the SITE_OVERRIDES dict.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass
from typing import Optional

from png_scraper.engine import (
    PNGScraper,
    Listing,
    make_listing,
    sleep_human,
    scroll_page,
    move_mouse,
)

log = logging.getLogger("png_scraper.general")

# ── generic selector cascades ─────────────────────────────────────────────────

GENERIC_CARD = [
    "article.property-item",       # RealHomes
    "article[class*='property']",
    "div[class*='property-card']",
    "div[class*='listing-card']",
    ".listing-item",
    ".property-listing",
    "li.listing",
    "div[class*='epl-listing']",   # Easy Property Listings
    "article[class*='listing']",
    "[data-component='PropertyCard']",
    ".rh_list_card",
    "div.item",                    # generic last-resort
]

GENERIC_TITLE = [
    "h2.property-title a", "h3.property-title a",
    ".listing-title a", ".item-title a",
    "h2[itemprop='name']", "h3[itemprop='name']",
    "[class*='epl-listing-heading'] a",
    ".rh_list_card__heading a",
    "h2 a", "h3 a",
]

GENERIC_PRICE = [
    "[class*='price']", "[class*='Price']",
    ".epl-price", ".property-price",
    "[itemprop='price']", "[data-price]",
    ".rh_list_card__price",
    "span[class*='amount']", "p[class*='price']",
]

GENERIC_LOCATION = [
    "[class*='location']", "[class*='Location']",
    "[class*='address']", "[itemprop='addressLocality']",
    ".epl-suburb", ".suburb", ".city",
    ".rh_list_card__location",
    "span[class*='suburb']", "p[class*='address']",
]

GENERIC_LINK = [
    "h2 a[href]", "h3 a[href]",
    ".property-title a[href]",
    "a[href*='/property/']", "a[href*='/listing']",
    "a[href*='/rent']", "a[href*='/real-estate']",
    "article > a[href]", ".item > a[href]",
]

GENERIC_NEXT = [
    "a[rel='next']", "a.next", ".next-page a",
    "[class*='pagination'] a[aria-label*='Next']",
    "a:has-text('Next')", "a:has-text('›')", "a:has-text('>>')",
    ".page-numbers.next",
]


# ── per-site configuration overrides ─────────────────────────────────────────

@dataclass
class SiteConfig:
    source_site:    str
    start_url:      str
    is_verified:    bool = True
    max_pages:      int  = 5
    card_selectors: list[str] = None    # None → use GENERIC_CARD
    extra_wait_ms:  int  = 0           # additional wait after load (ms)
    needs_scroll:   bool = True


AGENCY_CONFIGS: list[SiteConfig] = [
    SiteConfig("MarketMeri",           "https://marketmeri.com/real-estate",              max_pages=8),
    SiteConfig("SRE PNG",              "http://www.sre.com.pg/rentals",                   max_pages=5),
    SiteConfig("Century 21 PNG",       "https://www.century21.com.pg/rent",               max_pages=5),
    SiteConfig("Ray White PNG",        "https://www.raywhitepng.com/rent",                max_pages=5),
    SiteConfig("Pacific Palms",        "http://www.pacificpalmsproperty.com.pg/rentals",  max_pages=4),
    SiteConfig("DAC Properties",       "http://www.dac.com.pg/rentals",                   max_pages=4),
    SiteConfig("AAA Properties",       "http://www.aaaproperties.com.pg/rent",            max_pages=4),
    SiteConfig("Arthur Strachan",      "http://www.arthurstrachan.com.pg/rentals",        max_pages=4),
]


# ── card parser ───────────────────────────────────────────────────────────────

async def _first_text(el, selectors: list[str]) -> str:
    for sel in selectors:
        try:
            child = await el.query_selector(sel)
            if child:
                t = (await child.inner_text()).strip()
                if t:
                    return t
        except Exception:
            pass
    return ""

async def _first_attr(el, selectors: list[str], attr: str) -> str:
    for sel in selectors:
        try:
            child = await el.query_selector(sel)
            if child:
                v = (await child.get_attribute(attr) or "").strip()
                if v:
                    return v
        except Exception:
            pass
    return ""


async def _parse_card(card, cfg: SiteConfig, base_url: str) -> Optional[Listing]:
    title    = await _first_text(card, GENERIC_TITLE)
    price_r  = await _first_text(card, GENERIC_PRICE)
    location = await _first_text(card, GENERIC_LOCATION)
    href     = await _first_attr(card, GENERIC_LINK, "href")

    if not href:
        try:
            a = await card.query_selector("a[href]")
            if a:
                href = (await a.get_attribute("href") or "").strip()
        except Exception:
            pass

    if not href:
        return None

    url = href if href.startswith("http") else f"{base_url.rstrip('/')}/{href.lstrip('/')}"

    if not title:
        title = f"Property — {location}" if location else f"{cfg.source_site} Listing"

    return make_listing(
        source_site = cfg.source_site,
        title       = title,
        price_raw   = price_r,
        location    = location,
        listing_url = url,
        is_verified = cfg.is_verified,
        raw_text    = f"{title} {price_r} {location}",
    )


# ── single-site scraper ───────────────────────────────────────────────────────

class GeneralAgencyScraper(PNGScraper):
    """
    Adaptive scraper for a single agency site defined by a SiteConfig.

    Usage:
        scraper = GeneralAgencyScraper(AGENCY_CONFIGS[0])   # MarketMeri
        listings = await scraper.run()
    """

    IS_VERIFIED = True

    def __init__(self, config: SiteConfig, headless: bool = True):
        super().__init__(headless)
        self.cfg = config
        self.SOURCE_SITE = config.source_site

    async def scrape(self, context) -> list[Listing]:
        page = self._page
        cfg  = self.cfg
        results: list[Listing] = []
        seen_ids: set[str] = set()
        card_sels = cfg.card_selectors or GENERIC_CARD

        # Extract base URL for relative-URL resolution
        from urllib.parse import urlparse
        parsed   = urlparse(cfg.start_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        await page.route("**/*.{png,jpg,jpeg,gif,webp,woff,woff2,ttf}", lambda r: r.abort())

        for page_num in range(1, cfg.max_pages + 1):
            # Common WordPress pagination patterns
            if page_num == 1:
                url = cfg.start_url
            else:
                slash = "" if cfg.start_url.endswith("/") else "/"
                url   = f"{cfg.start_url}{slash}page/{page_num}/"

            log.info(f"[{cfg.source_site}] Page {page_num}/{cfg.max_pages} → {url}")

            if not await self._goto(url):
                break

            if cfg.extra_wait_ms:
                await asyncio.sleep(cfg.extra_wait_ms / 1000)

            if cfg.needs_scroll:
                await scroll_page(page, scrolls=random.randint(2, 4))

            await move_mouse(page)

            # Detect working selector
            cards = []
            for sel in card_sels:
                try:
                    await page.wait_for_selector(sel, timeout=6_000)
                    candidates = await page.query_selector_all(sel)
                    if candidates:
                        log.info(f"[{cfg.source_site}] '{sel}' → {len(candidates)} cards")
                        cards = candidates
                        break
                except Exception:
                    pass

            if not cards:
                log.warning(f"[{cfg.source_site}] No property cards found on page {page_num}")
                # Dump page title for debugging
                try:
                    title_tag = await page.title()
                    log.debug(f"[{cfg.source_site}] Page title: {title_tag}")
                except Exception:
                    pass
                break

            for card in cards:
                try:
                    listing = await _parse_card(card, cfg, base_url)
                    if listing and listing.listing_id not in seen_ids:
                        seen_ids.add(listing.listing_id)
                        results.append(listing)
                except Exception as e:
                    log.debug(f"[{cfg.source_site}] Parse error: {e}")

            log.info(f"[{cfg.source_site}] Running total: {len(results)}")

            # Next page check
            has_next = False
            for sel in GENERIC_NEXT:
                try:
                    loc = page.locator(sel).first
                    if await loc.is_visible(timeout=2_000):
                        has_next = True
                        break
                except Exception:
                    pass

            if not has_next:
                log.info(f"[{cfg.source_site}] No next page — done")
                break

            await sleep_human(2.0, 5.0)

        return results


# ── multi-site runner ────────────────────────────────────────────────────────

async def scrape_all_agencies(
    configs: list[SiteConfig] = None,
    headless: bool = True,
    concurrency: int = 3,
) -> list[Listing]:
    """
    Scrape all agency sites, running `concurrency` scrapers in parallel.

    Args:
        configs:     List of SiteConfig objects (defaults to AGENCY_CONFIGS)
        headless:    Run Playwright headless
        concurrency: Max simultaneous browser instances

    Returns:
        Flat list of all Listings across all sites
    """
    if configs is None:
        configs = AGENCY_CONFIGS

    semaphore = asyncio.Semaphore(concurrency)
    all_results: list[Listing] = []

    async def _run_one(cfg: SiteConfig) -> list[Listing]:
        async with semaphore:
            scraper = GeneralAgencyScraper(cfg, headless=headless)
            return await scraper.run()

    tasks = [_run_one(cfg) for cfg in configs]
    batches = await asyncio.gather(*tasks, return_exceptions=True)

    for cfg, batch in zip(configs, batches):
        if isinstance(batch, Exception):
            log.error(f"[{cfg.source_site}] Failed: {batch}")
        else:
            log.info(f"[{cfg.source_site}] ✓ {len(batch)} listings")
            all_results.extend(batch)

    return all_results
