import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import random
import time
import urllib.parse
import os
import json

# ======================
# CONFIG
# ======================
PAGES_TO_SCRAPE = 5
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "progress_status.json"
MAX_RUNTIME_SECONDS = 30 * 60 
START_TIME = time.time()

KEYWORDS = ["premium apk", "ai automation", "uae offers", "iptv links", "python coding"] # أضف بقية كلماتك هنا

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_progress(keyword, page):
    progress = load_progress()
    progress[keyword] = page
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)

async def run_scraper():
    progress = load_progress()
    fail_count = 0 

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        for keyword in KEYWORDS:
            if fail_count >= 3: break
            last_page_finished = progress.get(keyword, 0)
            if last_page_finished >= PAGES_TO_SCRAPE: continue

            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    if time.time() - START_TIME > MAX_RUNTIME_SECONDS: break
                    if current_page <= last_page_finished: continue

                    try:
                        if current_page > 1:
                            next_btn = page.locator(f".gsc-cursor-page >> text='{current_page}'")
                            if await next_btn.is_visible():
                                await next_btn.click()
                                await page.wait_for_timeout(10000)
                            else: break
                        
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        raw_html = await page.content()
                        raw_matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-\+\/\?=&]+", urllib.parse.unquote(raw_html))
                        
                        new_results = []
                        usernames = set()
                        for link in raw_matches:
                            path = link.split("t.me/")[1].strip("/")
                            if not path or "joinchat" in path.lower() or path.startswith("+"): continue
                            clean_user = path.split("?")[0].split("&")[0].split("/")[0]
                            if clean_user.startswith("s/"): clean_user = clean_user[2:]
                            if len(clean_user) > 4: usernames.add(clean_user.lower())

                        for user in usernames:
                            new_results.append({
                                "Keyword": keyword, 
                                "Channel Name": user, 
                                "Link": f"https://t.me/{user}", 
                                "Subscribers": "N/A",
                                "LatestID": None # قيمة افتراضية للعمود الجديد
                            })

                        if new_results:
                            new_df = pd.DataFrame(new_results)
                            if os.path.exists(SAVE_FILE):
                                old_df = pd.read_csv(SAVE_FILE)
                                # دمج مع الحفاظ على الـ IDs القديمة لو موجودة
                                combined = pd.concat([old_df, new_df], ignore_index=True)
                                combined.drop_duplicates(subset=['Link'], keep='first', inplace=True)
                                combined.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                            else:
                                new_df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                        
                        save_progress(keyword, current_page)
                        fail_count = 0 
                        time.sleep(random.uniform(3, 7))
                    except: break 
            except: fail_count += 1
            await page.close()
            time.sleep(random.uniform(10, 20))
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
