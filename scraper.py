import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import requests
import random
import time
import urllib.parse
import os
import json

# ======================
# CONFIG & SOURCES
# ======================
URL_OLD = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/main/telegram_channels.csv"
URL_NEW = "https://raw.githubusercontent.com/MoFlow00/Signal-X/main/telegram_data.csv"
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "progress_status.json"
PAGES_TO_SCRAPE = 5
MAX_RUNTIME_SECONDS = 25 * 60 
START_TIME = time.time()
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

# قائمة الكلمات المفتاحية (Keywords)
KEYWORDS = [
    "premium apk", "pro apps", "modded apps", "ai automation", "uae offers", "iptv links",
    "ذكاء اصطناعي", "تطبيقات مهكرة", "كورسات مجانية", "عروض الإمارات"
    # أضف بقية الكلمات هنا بنفس التنسيق
]

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
    print("🚀 Step 1: Immediate Merging and Cleaning...")
    
    try:
        df1 = pd.read_csv(URL_OLD)
        df2 = pd.read_csv(URL_NEW)
        df_local = pd.read_csv(SAVE_FILE) if os.path.exists(SAVE_FILE) else pd.DataFrame()
        
        combined_df = pd.concat([df1, df2, df_local], ignore_index=True)
        
        # تنظيف العواميد
        combined_df.columns = combined_df.columns.str.strip().str.replace('_', ' ')
        mapping = {'ChannelName': 'Channel Name', 'channel name': 'Channel Name'}
        combined_df.rename(columns=mapping, inplace=True)

        for col in COLS:
            if col not in combined_df.columns: combined_df[col] = None
        
        combined_df = combined_df[COLS]
        
        # تحويل LatestID لرقم والترتيب لضمان بقاء الصفوف المكتملة
        combined_df['LatestID'] = pd.to_numeric(combined_df['LatestID'], errors='coerce')
        combined_df = combined_df.sort_values(by='LatestID', ascending=False)
        combined_df.drop_duplicates(subset=['Link'], keep='first', inplace=True)
        
        combined_df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
        print(f"✨ Merge Done! Total: {len(combined_df)} unique channels.")
    except Exception as e:
        print(f"⚠️ Merge skipped: {e}")

    print("\n🚀 Step 2: Starting Playwright Search...")
    progress = load_progress()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        for keyword in KEYWORDS:
            if time.time() - START_TIME > MAX_RUNTIME_SECONDS: break

            last_page = progress.get(keyword, 0)
            if last_page >= PAGES_TO_SCRAPE: continue

            print(f"🔍 Keyword: {keyword}")
            page = await context.new_page()
            try:
                encoded = urllib.parse.quote(keyword)
                await page.goto(f"https://xtea.pages.dev/search?q={encoded}", wait_until="networkidle", timeout=60000)
                
                for cp in range(1, PAGES_TO_SCRAPE + 1):
                    if cp <= last_page: continue
                    
                    try:
                        if cp > 1:
                            btn = page.locator(f".gsc-cursor-page >> text='{cp}'")
                            if await btn.is_visible():
                                await btn.click()
                                await page.wait_for_timeout(8000)
                            else: break
                        
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        html = await page.content()
                        matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-]+", urllib.parse.unquote(html))
                        
                        if matches:
                            new_data = []
                            for link in set(matches):
                                user = link.split('/')[-1]
                                if len(user) > 4 and "joinchat" not in user:
                                    new_data.append({"Keyword": keyword, "Channel Name": user, "Link": f"https://t.me/{user}", "Subscribers": "N/A", "LatestID": None})
                            
                            if new_data:
                                current_df = pd.read_csv(SAVE_FILE)
                                final_update = pd.concat([current_df, pd.DataFrame(new_data)], ignore_index=True)
                                final_update['LatestID'] = pd.to_numeric(final_update['LatestID'], errors='coerce')
                                final_update = final_update.sort_values(by='LatestID', ascending=False)
                                final_update.drop_duplicates(subset=['Link'], keep='first', inplace=True)
                                final_update[COLS].to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                        
                        save_progress(keyword, cp)
                        time.sleep(random.uniform(2, 4))
                    except: break
            except: pass
            await page.close()

        await browser.close()
