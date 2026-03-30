import asyncio
from playwright.async_api import async_playwright
import os

async def verify_visuals():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Create a new context with a larger viewport to see the dashboard
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()

        # Mock authentication
        await page.goto("http://localhost:3000")
        await page.evaluate("""() => {
            localStorage.setItem('png_token', 'mock-token');
            localStorage.setItem('png_user', JSON.stringify({
                email: 'admin@example.com',
                full_name: 'Test Admin',
                role: 'admin'
            }));
        }""")

        # Reload to enter dashboard
        await page.goto("http://localhost:3000")
        await asyncio.sleep(2)

        # Take screenshot of Dashboard
        await page.screenshot(path="verify_compact_dashboard.png")
        print("Dashboard screenshot saved.")

        # Navigate to Heatmap
        await page.click("button[title='Heatmap']")
        await asyncio.sleep(2)
        await page.screenshot(path="verify_compact_heatmap.png")
        print("Heatmap screenshot saved.")

        # Navigate to Listings
        await page.click("button[title='Listings']")
        await asyncio.sleep(2)
        await page.screenshot(path="verify_compact_listings.png")
        print("Listings screenshot saved.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_visuals())
