"""
png_scraper/engine.py
─────────────────────────────────────────────────────────────────────────────
PNG Real Estate Scraper Engine
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import random
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field
from datetime import timezone, datetime
from pathlib import Path
from typing import Optional, Callable, Any

log = logging.getLogger("png_scraper")

_UA_POOL: list[str] = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

def random_ua() -> str:
    return random.choice(_UA_POOL)

STEALTH_JS = "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"

@dataclass
class Listing:
    listing_id:      str
    source_site:     str
    title:           str
    price_raw:       str
    price_monthly_k: Optional[int]
    price_confidence:str
    location:        str
    suburb:          Optional[str]
    listing_url:     str
    is_verified:     bool
    scraped_at:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    first_seen_at:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    property_type:   Optional[str] = None
    bedrooms:        Optional[int]  = None
    sqm:             Optional[float] = None
    is_for_sale:     bool = False
    is_active:       bool = True
    health_score:    int = 0
    is_middleman:    bool = False
    title_status:    str = "Unknown / TBC"
    legal_flags:     list[str] = field(default_factory=list)
    group_id:        Optional[str] = None
    investment_score: Optional[float] = 0.0
    investment_flags: list[str] = field(default_factory=list)
    raw_text:        str            = ""

    def to_dict(self) -> dict:
        return asdict(self)

def normalise_price(raw: str) -> tuple[Optional[int], str, str]:
    t = raw.lower().replace(",", "").replace("k", "")
    nums = re.findall(r"\d+", t)
    if not nums: return None, "", "low"
    val = int(nums[0])
    if "week" in raw.lower() or "pw" in raw.lower(): return val * 4, raw, "high"
    return val, raw, "medium"

def detect_suburb(text: str) -> Optional[str]:
    # Hardcoded list for engine to avoid circular imports if main.py is busy
    subs = ["Waigani","Boroko","Gerehu","Gordons","Hohola","Tokarara","Koki","Badili","Six Mile","Eight Mile","Morata","Erima","Konedobu"]
    t = text.lower()
    for s in subs:
        if s.lower() in t: return s
    return None

def make_listing(source_site, title, price_raw, location, listing_url, is_verified, raw_text=""):
    price_k, _, conf = normalise_price(price_raw)
    combined = f"{title} {raw_text} {location}"
    return Listing(
        listing_id      = hashlib.md5(f"{listing_url}:{price_raw}".encode()).hexdigest(),
        source_site     = source_site,
        title           = title.strip(),
        price_raw       = price_raw.strip(),
        price_monthly_k = price_k,
        price_confidence= conf,
        location        = location.strip(),
        suburb          = detect_suburb(combined),
        listing_url     = listing_url,
        is_verified     = is_verified,
        raw_text        = raw_text[:400],
    )

async def sleep_human(lo=1.0, hi=3.0):
    await asyncio.sleep(random.uniform(lo, hi))

async def type_human(page, selector, text):
    await page.click(selector)
    for ch in text:
        await page.type(selector, ch, delay=random.randint(50, 150))

async def scroll_page(page, scrolls=3):
    for _ in range(scrolls):
        await page.mouse.wheel(0, random.randint(300, 600))
        await asyncio.sleep(1)

async def move_mouse(page):
    await page.mouse.move(random.randint(100, 500), random.randint(100, 500))

async def new_stealth_context(pw, headless=True):
    browser = await pw.chromium.launch(headless=headless, args=["--no-sandbox"])
    context = await browser.new_context(user_agent=random_ua())
    await context.add_init_script(STEALTH_JS)
    return browser, context

class PNGScraper(ABC):
    SOURCE_SITE: str = "Unknown"
    MAX_RETRIES: int = 2
    def __init__(self, headless=True):
        self.headless = headless
        self._page = None

    @abstractmethod
    async def scrape(self, context, on_progress=None) -> list[Listing]: ...

    async def run(self, on_progress=None) -> list[Listing]:
        from playwright.async_api import async_playwright
        async with async_playwright() as pw:
            browser, context = await new_stealth_context(pw, self.headless)
            try:
                self._page = await context.new_page()
                return await self.scrape(context, on_progress=on_progress)
            except Exception as e:
                log.error(f"[{self.SOURCE_SITE}] Scrape error: {e}")
                return []
            finally: await browser.close()

    async def _goto(self, url: str, wait_until: str = "load") -> bool:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                log.info(f"[{self.SOURCE_SITE}] Navigating to {url}")
                resp = await self._page.goto(url, wait_until=wait_until, timeout=45_000)
                log.info(f"[{self.SOURCE_SITE}] Status: {resp.status if resp else 'N/A'}")
                await asyncio.sleep(2)
                return True
            except Exception as e:
                log.warning(f"[{self.SOURCE_SITE}] Nav failed: {e}")
                await asyncio.sleep(3)
        return False
