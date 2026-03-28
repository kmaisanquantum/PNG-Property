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

        # Navigate to Valuation
        await page.click("button[title='Valuation']")
        await page.wait_for_selector("text=VALUE MY HOME")

        # Fill Form
        await page.select_option("select:near(text='SUBURB')", "Waigani")
        await page.fill("input:near(text='BEDROOMS')", "3")
        await page.fill("input:near(text='LAND SIZE (SQM)')", "200")

        # Get Free Estimate
        await page.click("text=GENERATE FREE ESTIMATE")
        await page.wait_for_selector("text=ESTIMATED MARKET VALUE")
        await page.screenshot(path="verification/valuation_estimate.png")

        # Unlock Premium Report
        await page.click("text=UNLOCK FOR K25.00")
        await page.wait_for_selector("text=Detailed Market Comparison")
        await page.click("text=Verify & Unlock")

        await page.wait_for_selector("text=Premium Report Unlocked")
        await page.screenshot(path="verification/valuation_premium_report.png")

        print("Valuation UI Verified!")
        await browser.close()

if __name__ == "__main__":
    os.makedirs("verification", exist_ok=True)
    asyncio.run(verify())
