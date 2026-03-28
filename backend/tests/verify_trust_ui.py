import asyncio
from playwright.async_api import async_playwright
import os

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Go to the app
        await page.goto("http://localhost:8000")

        print("Logging in...")
        # Landing page has 'Sign In' in nav
        await page.click("nav button:has-text('Sign In')")

        # Wait for modal
        await page.wait_for_selector("input[placeholder='Email or Phone number']")

        # Step 1: Identify
        await page.fill("input[placeholder='Email or Phone number']", "kmaisan@dspng.tech")
        await page.click("button:has-text('Continue')")

        # Wait for Step 2: Login (Password)
        await page.wait_for_selector("input[type='password']", timeout=5000)
        await page.fill("input[type='password']", "kilomike@2024")
        # Click Sign In button in the form
        await page.click("form button:has-text('Sign In')")

        # Wait for dashboard
        print("Waiting for dashboard...")
        await page.wait_for_selector("text=Dashboard", timeout=10000)

        # Go to Listings view
        print("Navigating to Listings...")
        # Use the nav button icon for Listings (≡)
        await page.click("text=≡")

        await page.wait_for_selector("text=Health", timeout=5000)
        print("Listings view loaded.")

        # Ensure some data is loaded
        await page.wait_for_selector("text=%", timeout=10000)

        # Capture the Trust Suite elements
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.screenshot(path="verification/listings_trust.png")
        print("Screenshot saved to verification/listings_trust.png")

        await browser.close()

if __name__ == "__main__":
    if not os.path.exists("verification"):
        os.makedirs("verification")
    asyncio.run(verify())
