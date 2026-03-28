import asyncio
from playwright.async_api import async_playwright
import os

async def verify():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 1000})
        page = await context.new_page()

        # Login
        await page.goto("http://localhost:5173")
        await page.click("text=Get Access")
        await page.click("text=Continue with Email")
        await page.fill("input[type='email']", "kmaisan@dspng.tech")
        await page.fill("input[type='password']", "kilomike@2024")
        await page.click("button:has-text('Login')")

        await page.wait_for_selector("text=Dashboard")

        # Navigate to Listings
        await page.click("button[title='Listings']")
        await page.wait_for_selector("text=SEARCH TITLE")

        # Check for badges
        await page.screenshot(path="verification/listings_legal_badges.png")

        # Trigger Title Search
        await page.click("text=SEARCH TITLE", position={"x": 5, "y": 5}) # Click the first one
        await page.wait_for_selector("text=Legal Guard: Title Verification")
        await page.screenshot(path="verification/legal_verification_modal.png")

        print("Legal Guard UI Verified!")
        await browser.close()

if __name__ == "__main__":
    os.makedirs("verification", exist_ok=True)
    asyncio.run(verify())
