import sys
import os

with open('backend/png_scraper/scrapers/facebook.py', 'r') as f:
    content = f.read()

# 1. Update imports
content = content.replace('from pathlib import Path', 'import sys\nfrom pathlib import Path')

# 2. Update SESSION_FILE to be configurable via environment variable
content = content.replace(
    'SESSION_FILE    = Path("fb_session.json")',
    'SESSION_FILE    = Path(os.getenv("FB_SESSION_PATH", "fb_session.json"))'
)

# 3. Update 2FA logic to check for interactive environment
search_2fa = """        # Checkpoint / 2FA detection
        if "checkpoint" in page.url or "two_step" in page.url or "two-factor" in page.url:
            log.warning("[FB] ⚠️  2FA checkpoint detected!")
            log.warning("[FB]     Complete 2FA in the browser, then press ENTER.")
            input(">> Press ENTER after completing 2FA: ")
            await sleep_human(2.0, 4.0)"""

replace_2fa = """        # Checkpoint / 2FA detection
        if "checkpoint" in page.url or "two_step" in page.url or "two-factor" in page.url:
            log.warning("[FB] ⚠️  2FA checkpoint detected!")
            if sys.stdin.isatty():
                log.warning("[FB]     Complete 2FA in the browser, then press ENTER.")
                input(">> Press ENTER after completing 2FA: ")
                await sleep_human(2.0, 4.0)
            else:
                log.error("[FB] ❌ Non-interactive shell — cannot complete 2FA checkpoint.")
                log.error("[FB]    Strategy: Run once locally to generate session file, then upload to Render.")
                return False"""

content = content.replace(search_2fa, replace_2fa)

with open('backend/png_scraper/scrapers/facebook.py', 'w') as f:
    f.write(content)
