import sys, os, asyncio

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from png_scraper.main import run_all

async def test():
    try:
        # Using Professionals as it's often more reliable and faster for a quick test
        res = await run_all(sources=["professionals"], max_pages=1, headless=True, include_facebook=False)
        print(f"Collected {len(res)} results")
    except Exception as e:
        print(f"Scrape failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
