"""
png_scraper/scrapers/facebook.py
─────────────────────────────────────────────────────────────────────────────
FacebookScraper  —  https://www.facebook.com/marketplace/category/propertyrentals

Handles:
• Stealth (init-script inherited from engine.new_stealth_context)
• Login popup — two-stage: close without login → fallback to credential login
• Session persistence (avoids frequent re-logins → reduces ban risk)
• Auto-scroll with human-like cadence
• Checkpoint / 2FA detection
• Rate-limit backoff
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
from pathlib import Path
from typing import Optional

from png_scraper.engine import (
    PNGScraper,
    Listing,
    make_listing,
    sleep_human,
    scroll_page,
    move_mouse,
    type_human,
    new_stealth_context,
)

log = logging.getLogger("png_scraper.facebook")

SOURCE_SITE   = "Facebook Marketplace"
MARKETPLACE_URL = "https://www.facebook.com/marketplace/category/propertyrentals"
LOGIN_URL       = "https://www.facebook.com/login"
SESSION_FILE    = Path("fb_session.json")

# Load FB credentials from environment (set in .env or CI secrets — never hardcode)
FB_EMAIL    = os.getenv("FB_EMAIL", "")
FB_PASSWORD = os.getenv("FB_PASSWORD", "")

# ── login wall handlers ───────────────────────────────────────────────────────

_CLOSE_SELECTORS = [
    "[aria-label='Close']",
    "button[title='Close']",
    "[data-testid='xout-dialog-header-close-button']",
    "div[role='dialog'] [aria-label='Close']",
]

_WALL_DETECTORS = [
    "form#login_form",
    "[data-testid='royal_login_form']",
    "input#email",
]


async def _dismiss_popup_no_login(page) -> bool:
    """
    Strategy A: Close the modal without logging in.
    Works when Marketplace shows public listings behind a soft login wall.
    Returns True if successfully dismissed.
    """
    # Try close button
    for sel in _CLOSE_SELECTORS:
        try:
            btn = page.locator(sel).first
            if await btn.is_visible(timeout=2_500):
                await sleep_human(0.4, 1.0)
                await btn.click()
                await sleep_human(0.8, 1.5)
                log.info("[FB] Login popup closed (no-login)")
                return True
        except Exception:
            pass

    # Try Escape key
    try:
        await page.keyboard.press("Escape")
        await sleep_human(0.5, 1.0)
        log.info("[FB] Popup dismissed with Escape")
        return True
    except Exception:
        pass

    return False


async def _login_with_credentials(page, email: str, password: str) -> bool:
    """
    Strategy B: Full credential login.

    ⚠️  PRODUCTION SAFETY RULES:
    1. Use a DEDICATED scraper account — never a personal account.
    2. Keep IP consistent (residential proxy in PG preferred).
    3. Save and reuse session cookies to minimise login frequency.
    4. Never log in from more than one location simultaneously.
    5. Rotate the account every 30–60 days.
    6. Enable TOTP 2FA on the scraper account so you control checkpoints.
    """
    if not email or not password:
        log.warning("[FB] No credentials supplied — skipping login")
        return False

    try:
        await page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=30_000)
        await sleep_human(2.0, 4.0)
        await move_mouse(page)

        # Accept cookie consent if present
        for cookie_sel in [
            "[data-cookiebanner='accept_button']",
            "[title='Accept all']",
            "button:has-text('Accept All')",
            "button:has-text('Allow all cookies')",
        ]:
            try:
                btn = page.locator(cookie_sel).first
                if await btn.is_visible(timeout=2_000):
                    await btn.click()
                    await sleep_human(0.5, 1.2)
                    break
            except Exception:
                pass

        # Type credentials with human cadence
        await type_human(page, "#email", email)
        await sleep_human(0.6, 1.5)
        await type_human(page, "#pass", password)
        await sleep_human(0.9, 2.0)
        await move_mouse(page)

        await page.click("#loginbutton")
        await sleep_human(3.5, 7.0)

        # Checkpoint / 2FA detection
        if "checkpoint" in page.url or "two_step" in page.url or "two-factor" in page.url:
            log.warning("[FB] ⚠️  2FA checkpoint detected!")
            log.warning("[FB]     Complete 2FA in the browser, then press ENTER.")
            input(">> Press ENTER after completing 2FA: ")
            await sleep_human(2.0, 4.0)

        # Verify login success
        if "facebook.com" in page.url and "login" not in page.url:
            await page.context.storage_state(path=str(SESSION_FILE))
            log.info(f"[FB] ✅ Logged in. Session saved → {SESSION_FILE}")
            return True

        log.error(f"[FB] Login failed. URL: {page.url}")
        return False

    except Exception as e:
        log.error(f"[FB] Login exception: {e}")
        return False


async def _restore_session(page) -> bool:
    """Check if saved session is still valid."""
    if not SESSION_FILE.exists():
        return False
    try:
        await page.goto("https://www.facebook.com/", wait_until="domcontentloaded", timeout=20_000)
        await sleep_human(1.5, 3.0)
        if "login" not in page.url:
            log.info("[FB] ✅ Session restored from saved state")
            return True
    except Exception:
        pass
    return False


# ── marketplace card parser ───────────────────────────────────────────────────

_CARD_SELECTORS = [
    "[data-testid='marketplace_feed_unit']",
    "[class*='MarketplaceListingCard']",
    "div[class*='x1yztbdb']",           # FB internal (changes often)
    "a[href*='/marketplace/item/']",
]

_TEXT_SELECTORS = [
    "span[dir='auto']",
    "div[dir='auto']",
    "[class*='x1lliihq']",              # FB internal text class
]


async def _parse_marketplace_card(card) -> Optional[dict]:
    """Extract raw fields from one Marketplace listing card."""
    texts: list[str] = []
    for sel in _TEXT_SELECTORS:
        els = await card.query_selector_all(sel)
        for el in els:
            try:
                t = (await el.inner_text()).strip()
                if t and t not in texts and len(t) < 300:
                    texts.append(t)
            except Exception:
                pass

    href = ""
    try:
        link = await card.query_selector("a[href*='/marketplace/item/']")
        if not link:
            link = await card.query_selector("a[href]")
        if link:
            href = (await link.get_attribute("href") or "").strip()
    except Exception:
        pass

    if not texts and not href:
        return None

    url = href if href.startswith("http") else f"https://www.facebook.com{href}"
    price_raw = texts[0] if texts else ""
    description = " | ".join(texts[1:4]) if len(texts) > 1 else ""
    location_raw = texts[-1] if len(texts) > 1 else ""

    return {
        "price_raw":   price_raw,
        "description": description,
        "location":    location_raw,
        "url":         url,
        "all_texts":   " ".join(texts),
    }


# ── main scraper ──────────────────────────────────────────────────────────────

class FacebookScraper(PNGScraper):
    """
    Scraper for Facebook Marketplace → Property Rentals.

    Lifecycle:
        1. Attempt session restore from fb_session.json
        2. If no session → try dismiss popup (no-login access)
        3. If content still gated → credential login
        4. Auto-scroll Marketplace infinite feed
        5. Parse and yield Listing objects
    """

    SOURCE_SITE = SOURCE_SITE
    IS_VERIFIED = False          # Social listings are unverified

    def __init__(
        self,
        scroll_rounds: int = 8,
        headless: bool = True,
        email: str = FB_EMAIL,
        password: str = FB_PASSWORD,
    ):
        super().__init__(headless)
        self.scroll_rounds = scroll_rounds
        self.email    = email
        self.password = password

    async def run(self) -> list[Listing]:
        """Override run() to inject saved session into context."""
        from playwright.async_api import async_playwright
        log.info(f"[FB] Starting scraper (headless={self.headless})")
        results: list[Listing] = []

        async with async_playwright() as pw:
            browser, context = await new_stealth_context(
                pw, self.headless, session_file=SESSION_FILE
            )
            try:
                self._page = await context.new_page()
                results = await self.scrape(context)
                log.info(f"[FB] ✓ Collected {len(results)} listings")
            except Exception as exc:
                log.error(f"[FB] Fatal: {exc}", exc_info=True)
            finally:
                # Always persist session on exit
                try:
                    await context.storage_state(path=str(SESSION_FILE))
                except Exception:
                    pass
                await browser.close()
        return results

    async def scrape(self, context) -> list[Listing]:
        page = self._page
        results: list[Listing] = []
        seen_ids: set[str] = set()

        # ── Phase 1: try accessing Marketplace ───────────────────────────────
        if not await self._goto(MARKETPLACE_URL):
            log.error("[FB] Cannot reach Facebook")
            return results

        # Check if already logged in (restored session)
        if "login" in page.url:
            dismissed = await _dismiss_popup_no_login(page)
            if not dismissed or "login" in page.url:
                logged_in = await _login_with_credentials(page, self.email, self.password)
                if logged_in:
                    await self._goto(MARKETPLACE_URL)
                else:
                    log.error("[FB] Cannot authenticate — no listings collected")
                    return results

        # ── Phase 2: dismiss any remaining modal ─────────────────────────────
        await _dismiss_popup_no_login(page)
        await sleep_human(1.5, 3.0)

        # ── Phase 3: auto-scroll + extract ───────────────────────────────────
        log.info(f"[FB] Scrolling {self.scroll_rounds} rounds to load Marketplace feed")

        for round_num in range(1, self.scroll_rounds + 1):
            log.info(f"[FB] Scroll round {round_num}/{self.scroll_rounds}")
            await move_mouse(page)
            await scroll_page(page, scrolls=random.randint(3, 6))
            await sleep_human(2.0, 4.5)

            # Collect cards visible so far
            for sel in _CARD_SELECTORS:
                try:
                    cards = await page.query_selector_all(sel)
                    if not cards:
                        continue
                    for card in cards:
                        raw = await _parse_marketplace_card(card)
                        if not raw:
                            continue
                        listing = make_listing(
                            source_site = SOURCE_SITE,
                            title       = raw["description"] or raw["price_raw"] or "FB Marketplace Rental",
                            price_raw   = raw["price_raw"],
                            location    = raw["location"],
                            listing_url = raw["url"],
                            is_verified = False,
                            raw_text    = raw["all_texts"],
                        )
                        if listing.listing_id not in seen_ids:
                            seen_ids.add(listing.listing_id)
                            results.append(listing)
                    if results:
                        break
                except Exception as e:
                    log.debug(f"[FB] Selector error: {e}")

            log.info(f"[FB] Running total: {len(results)} unique listings")

            # Longer breaks every 3 rounds (human reading simulation)
            if round_num % 3 == 0:
                pause = random.uniform(8.0, 18.0)
                log.info(f"[FB] Taking a {pause:.0f}s reading break...")
                await asyncio.sleep(pause)

        return results
