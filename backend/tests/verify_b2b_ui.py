
import asyncio
from playwright.async_api import async_playwright
import os

async def verify_b2b_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 1200})
        page = await context.new_page()

        await page.goto("http://localhost:8000")

        # 1. Click 'Sign In' in the nav
        # There are two 'Sign In' buttons, one in nav and one in modal footer.
        # nav button has class 'btn-ghost'
        await page.click("nav button:has-text('Sign In')")

        # 2. Enter email in the 'identify' step
        await page.wait_for_selector("input[placeholder='Email or Phone number']")
        await page.fill("input[placeholder='Email or Phone number']", "kmaisan@dspng.tech")
        await page.click("button:has-text('Continue')")

        # 3. Enter password in the 'login' step
        await page.wait_for_selector("input[placeholder='••••••••']")
        await page.fill("input[placeholder='••••••••']", "kilomike@2024")

        # Click the 'Sign In' submit button (it's the only submit button visible now)
        await page.click("button[type='submit']")

        # 4. Wait for dashboard and Agent Intel button
        await page.wait_for_selector("button[title='Agent Intel']", timeout=15000)
        print("Logged in successfully.")

        # 5. Navigate to Agent Intel
        await page.click("button[title='Agent Intel']")
        await asyncio.sleep(3)

        # 6. Verify B2B components
        await page.wait_for_selector("text=COMPETITOR PRICING ALERTS")
        await page.wait_for_selector("text=MARKET OPPORTUNITY")
        await page.wait_for_selector("text=HOT LEADS")

        # Take the final screenshot
        os.makedirs("verification", exist_ok=True)
        await page.screenshot(path="verification/agent_intel_dashboard.png", full_page=True)
        print("Screenshot saved to verification/agent_intel_dashboard.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_b2b_ui())
