with open('README.md', 'r') as f:
    content = f.read()

fb_section = """
---

## 🔵 Facebook Scraping & 2FA Setup

Facebook Marketplace scraping requires an account. Due to 2FA and Render's headless environment, follow these steps:

### 1. Configure Render Environment
In the `png-property-api` service → **Environment**:
- `FB_EMAIL`: Your dedicated scraper account email.
- `FB_PASSWORD`: Your scraper account password.
- `FB_SESSION_PATH`: `/app/data/fb_session.json` (Render persistent disk).

### 2. Handle 2FA (Local → Render)
If your account has 2FA enabled:
1. **Run locally once**: Start the backend locally (`python png_scraper/main.py`).
2. **Complete 2FA**: The scraper will pause and ask you to complete 2FA in the browser window or terminal.
3. **Capture Session**: Once logged in, a `fb_session.json` file is created in your local backend folder.
4. **Upload to Render**:
   - Use the Render Shell or an SSH tunnel to upload `fb_session.json` to `/app/data/fb_session.json`.
   - Alternatively, use a **Secret File** in Render named `FB_SESSION_CONTENT` and update the code to read from it (persistent disk is preferred).

Once the session file is present in the persistent disk, the scraper will bypass the login wall automatically.
"""

# Find a good place to insert - after Step 3 of Deploy to Render
insertion_point = "### Step 3 — Set Environment Variables"
if insertion_point in content:
    parts = content.split(insertion_point)
    content = parts[0] + fb_section + insertion_point + parts[1]
else:
    content += fb_section

with open('README.md', 'w') as f:
    f.write(content)
