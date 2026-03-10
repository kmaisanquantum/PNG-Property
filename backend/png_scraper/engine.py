"""
png_scraper/engine.py
─────────────────────────────────────────────────────────────────────────────
PNG Real Estate Scraper Engine
Abstract base class, stealth browser factory, price normaliser,
and shared data model.

Install:
    pip install playwright fake-useragent python-dotenv
    playwright install chromium
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("png_scraper")

# ── user-agent pool (bundled fallback – no network needed) ───────────────────
_UA_POOL: list[str] = [
    # Chrome / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # Chrome / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    # Safari / macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    # Firefox / Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.2365.92",
    # Linux Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

try:
    from fake_useragent import UserAgent as _FUA
    _fua = _FUA(browsers=["chrome", "firefox", "edge"], os=["windows", "macos"])
    def random_ua() -> str:
        try:
            return _fua.random
        except Exception:
            return random.choice(_UA_POOL)
except ImportError:
    def random_ua() -> str:
        return random.choice(_UA_POOL)

# ── stealth init-script injected into every page ─────────────────────────────
STEALTH_JS = """
// 1. Remove webdriver flag
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// 2. Realistic plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' },
    ]
});

// 3. Languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-PG', 'en-US', 'en'] });

// 4. chrome runtime object (absent in headless)
if (!window.chrome) window.chrome = { runtime: {} };

// 5. Permissions API
const _origQuery = window.navigator.permissions.query;
window.navigator.permissions.query = params =>
    params.name === 'notifications'
        ? Promise.resolve({ state: Notification.permission })
        : _origQuery.call(navigator.permissions, params);

// 6. Canvas fingerprint noise
const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function (type) {
    const ctx = this.getContext('2d');
    if (ctx) {
        const img = ctx.getImageData(0, 0, this.width, this.height);
        for (let i = 0; i < img.data.length; i += 97)
            img.data[i] ^= (Math.random() * 4) | 0;
        ctx.putImageData(img, 0, 0);
    }
    return _origToDataURL.apply(this, arguments);
};

// 7. WebGL vendor spoof
const _getParam = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function (param) {
    if (param === 37445) return 'Intel Inc.';
    if (param === 37446) return 'Intel Iris OpenGL Engine';
    return _getParam.call(this, param);
};
"""

# ── shared data model ────────────────────────────────────────────────────────

@dataclass
class Listing:
    """Canonical listing record – analytics-ready."""
    listing_id:      str            # md5(url + price_raw)
    source_site:     str            # e.g. "Hausples", "The Professionals"
    title:           str
    price_raw:       str            # original string, e.g. "K2,500/month"
    price_monthly_k: Optional[int]  # normalised integer PGK/month
    price_confidence:str            # "high" | "medium" | "low"
    location:        str
    suburb:          Optional[str]  # canonical suburb name
    listing_url:     str
    is_verified:     bool           # True for agency sites
    scraped_at:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    property_type:   Optional[str] = None
    bedrooms:        Optional[int]  = None
    raw_text:        str            = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── price normaliser ─────────────────────────────────────────────────────────

_PERIOD_MULT: dict[str, float] = {
    "day": 30, "daily": 30,
    "week": 4.3333, "weekly": 4.3333, "wk": 4.3333, "w": 4.3333,
    "fortnight": 2.16665, "fn": 2.16665,
    "month": 1, "monthly": 1, "mo": 1, "mth": 1, "m": 1,
    "year": 1/12, "yearly": 1/12, "annual": 1/12, "pa": 1/12,
}

_PRICE_RE = re.compile(
    r"(?:k|pgk|kina)?\s*"
    r"(?P<amount>\d[\d,]*(?:\.\d+)?)"
    r"\s*(?:k|kina|pgk)?"
    r"(?:\s*(?:per|a|p|/|-)?\s*"
    r"(?P<period>day|daily|week|weekly|wk|w|fortnight|fn|month|monthly|mo|mth|year|yearly|annual|pa))?"
    , re.IGNORECASE
)

def normalise_price(raw: str) -> tuple[Optional[int], str, str]:
    """
    Returns (monthly_pgk, matched_raw, confidence).
    Confidence: "high" = explicit period found,
                "medium" = inferred by magnitude,
                "low" = no numeric found.
    """
    text = raw.lower().replace(",", "").replace("pgk", "k").replace("kina", "k")
    best: Optional[tuple[float, str, str]] = None

    for m in _PRICE_RE.finditer(text):
        try:
            amount = float(m.group("amount"))
        except (TypeError, ValueError):
            continue
        if amount < 50 or amount > 600_000:
            continue

        period = (m.group("period") or "").lower().strip()
        mult   = _PERIOD_MULT.get(period)

        if mult:
            monthly, conf = amount * mult, "high"
        elif amount <= 2_000:
            monthly, conf = amount * 4.333, "medium"   # likely weekly
        else:
            monthly, conf = amount, "medium"            # likely monthly

        if best is None or (mult and best[2] != "high"):
            best = (monthly, m.group(0).strip(), conf)

    if best:
        return int(round(best[0])), best[1], best[2]
    return None, "", "low"


# ── suburb recogniser ────────────────────────────────────────────────────────

_SUBURB_MAP: dict[str, str] = {
    "waigani": "Waigani", "boroko": "Boroko", "gerehu": "Gerehu",
    "gordons": "Gordons", "koki": "Koki", "hohola": "Hohola",
    "tokarara": "Tokarara", "tokerara": "Tokarara", "six mile": "Six Mile",
    "6 mile": "Six Mile", "eight mile": "Eight Mile", "8 mile": "Eight Mile",
    "nine mile": "Nine Mile", "9 mile": "Nine Mile", "badili": "Badili",
    "morata": "Morata", "erima": "Erima", "gordons": "Gordons",
    "lawes road": "Lawes Road", "port moresby": "Port Moresby",
    "pom": "Port Moresby", "ncd": "Port Moresby", "lae": "Lae",
    "madang": "Madang", "mt hagen": "Mt Hagen", "mount hagen": "Mt Hagen",
    "kokopo": "Kokopo", "alotau": "Alotau", "wewak": "Wewak",
}

def detect_suburb(text: str) -> Optional[str]:
    t = text.lower()
    for alias, canonical in _SUBURB_MAP.items():
        if re.search(r"\b" + re.escape(alias) + r"\b", t):
            return canonical
    return None


# ── property type classifier ─────────────────────────────────────────────────

_TYPE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(house|home|bungalow|dwelling)\b", re.I), "House"),
    (re.compile(r"\b(flat|apartment|apt|unit)\b", re.I),      "Apartment"),
    (re.compile(r"\bstudio\b", re.I),                          "Studio"),
    (re.compile(r"\b(townhouse|town\s*house|villa)\b", re.I), "Townhouse"),
    (re.compile(r"\b(room|bedsit|single room)\b", re.I),      "Room"),
    (re.compile(r"\b(land|block|plot|allotment)\b", re.I),    "Land"),
    (re.compile(r"\b(commercial|office|shop|warehouse)\b", re.I), "Commercial"),
]

def classify_type(text: str) -> Optional[str]:
    for pat, label in _TYPE_PATTERNS:
        if pat.search(text):
            return label
    return None

_BED_RE = re.compile(r"(\d+)\s*(?:bed(?:room)?s?|bdrm|br\b|b/r)", re.I)

def extract_bedrooms(text: str) -> Optional[int]:
    m = _BED_RE.search(text)
    if m:
        n = int(m.group(1))
        return n if 1 <= n <= 20 else None
    return None


# ── listing factory helper ───────────────────────────────────────────────────

def make_listing(
    source_site: str,
    title: str,
    price_raw: str,
    location: str,
    listing_url: str,
    is_verified: bool,
    raw_text: str = "",
) -> Listing:
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
        property_type   = classify_type(combined),
        bedrooms        = extract_bedrooms(combined),
        raw_text        = raw_text[:400],
    )


# ── human timing helpers ─────────────────────────────────────────────────────

async def sleep_human(lo: float = 1.0, hi: float = 3.5) -> None:
    t = max(lo, min(hi, random.gauss((lo + hi) / 2, (hi - lo) / 4)))
    await asyncio.sleep(t)

async def type_human(page, selector: str, text: str) -> None:
    await page.click(selector)
    await sleep_human(0.2, 0.6)
    for ch in text:
        await page.type(selector, ch, delay=random.randint(55, 200))
        if ch in (" ", "@", "."):
            await asyncio.sleep(random.uniform(0.1, 0.4))

async def scroll_page(page, scrolls: int = 4) -> None:
    for _ in range(scrolls):
        await page.mouse.wheel(0, random.randint(250, 750))
        await sleep_human(0.6, 1.8)

async def move_mouse(page) -> None:
    vp = page.viewport_size or {"width": 1280, "height": 900}
    for _ in range(random.randint(2, 4)):
        await page.mouse.move(
            random.randint(80, vp["width"] - 80),
            random.randint(80, vp["height"] - 80),
            steps=random.randint(6, 14),
        )
        await asyncio.sleep(random.uniform(0.05, 0.3))


# ── browser / context factory ─────────────────────────────────────────────────

async def new_stealth_context(pw, headless: bool = True, session_file: Optional[Path] = None):
    """
    Creates a Playwright BrowserContext with:
    • random user-agent & viewport
    • PNG locale / timezone / geolocation
    • stealth JS init-script
    • optional saved session state
    """
    ua = random_ua()
    w  = random.choice([1280, 1366, 1440, 1920])
    h  = random.choice([768, 800, 900, 1080])

    browser = await pw.chromium.launch(
        headless=headless,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-features=IsolateOrigins,site-per-process",
            f"--window-size={w},{h}",
        ],
    )

    ctx_kwargs = dict(
        user_agent   = ua,
        viewport     = {"width": w, "height": h},
        locale       = "en-PG",
        timezone_id  = "Pacific/Port_Moresby",
        geolocation  = {"latitude": -9.4438, "longitude": 147.1803},
        permissions  = ["geolocation"],
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "DNT": "1",
            "Sec-Fetch-Mode": "navigate",
        },
    )
    if session_file and session_file.exists():
        ctx_kwargs["storage_state"] = str(session_file)

    context = await browser.new_context(**ctx_kwargs)
    await context.add_init_script(STEALTH_JS)
    # Block ads / trackers for speed
    await context.route(
        r"**/(ads|analytics|tracking|doubleclick|facebook\.net/signals|connect\.facebook\.net/en_US/fbevents)*",
        lambda r: r.abort()
    )
    return browser, context


# ── abstract base class ──────────────────────────────────────────────────────

class PNGScraper(ABC):
    """
    Abstract base for all PNG real estate scrapers.

    Concrete subclasses must implement:
        scrape(context) -> list[Listing]

    They inherit:
        run()              — orchestrates browser lifecycle
        _goto()            — page.goto with retry + backoff
        _safe_text()       — safe inner_text extraction
    """

    SOURCE_SITE: str = "Unknown"
    IS_VERIFIED: bool = False
    MAX_RETRIES: int = 3

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._page = None

    @abstractmethod
    async def scrape(self, context) -> list[Listing]:
        """Perform the actual scrape. Receives a ready BrowserContext."""
        ...

    async def run(self) -> list[Listing]:
        """Full lifecycle: launch browser → scrape → close → return listings."""
        from playwright.async_api import async_playwright
        log.info(f"[{self.SOURCE_SITE}] Starting scraper (headless={self.headless})")
        results: list[Listing] = []
        async with async_playwright() as pw:
            browser, context = await new_stealth_context(pw, self.headless)
            try:
                self._page = await context.new_page()
                results = await self.scrape(context)
                log.info(f"[{self.SOURCE_SITE}] ✓ Collected {len(results)} listings")
            except Exception as exc:
                log.error(f"[{self.SOURCE_SITE}] Fatal error: {exc}", exc_info=True)
            finally:
                await browser.close()
        return results

    async def _goto(self, url: str, wait_until: str = "domcontentloaded") -> bool:
        """Navigate with exponential-backoff retry."""
        from playwright.async_api import TimeoutError as PWTimeout
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                await self._page.goto(url, wait_until=wait_until, timeout=35_000)
                await sleep_human(1.0, 2.5)
                return True
            except PWTimeout:
                wait = (2 ** attempt) + random.uniform(0.5, 2.0)
                log.warning(f"[{self.SOURCE_SITE}] Timeout ({attempt}/{self.MAX_RETRIES}) — retry in {wait:.1f}s")
                await asyncio.sleep(wait)
        log.error(f"[{self.SOURCE_SITE}] All retries failed for {url}")
        return False

    async def _safe_text(self, element, default: str = "") -> str:
        try:
            return (await element.inner_text()).strip()
        except Exception:
            return default

    async def _safe_attr(self, element, attr: str, default: str = "") -> str:
        try:
            val = await element.get_attribute(attr)
            return (val or "").strip()
        except Exception:
            return default
