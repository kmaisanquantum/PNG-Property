import sys, os, asyncio, json
from pathlib import Path
from datetime import datetime, timezone

# Ensure backend is in path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock some things if needed, but let's try to run it for real with 0 pages if possible
# or just mock the scraper parts

import main
from main import _run_scrape, ScrapeRequest, scrape_jobs

async def test():
    req = ScrapeRequest(sources=[], max_pages=0, headless=True) # Empty sources should finish quickly
    job_id = "test_job"
    scrape_jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "sources": req.sources,
        "max_pages": req.max_pages,
        "queued_at": datetime.now(timezone.utc).isoformat(),
        "progress": 0,
        "collected": 0
    }

    print("Starting mock scrape...")
    try:
        await _run_scrape(job_id, req)
        print("Scrape job state:", json.dumps(scrape_jobs[job_id], indent=2))
        print("Scrape finished successfully")
    except Exception as e:
        print(f"Scrape failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
