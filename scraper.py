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
# CONFIG & SOURCES
# ======================
URL_OLD = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/main/telegram_channels.csv"
URL_NEW = "https://raw.githubusercontent.com/MoFlow00/Signal-X/main/telegram_data.csv"
SAVE_FILE = "telegram_data.csv"
PAGES_TO_SCRAPE = 3 
KEYWORDS = ["premium apk", "ai automation", "uae offers", "iptv links", "python coding"] # أضف كلماتك هنا

async def run_scraper():
    print("🚀 Starting Signal-X Unified Scraper...")
    
    # 1. جلب البيانات القديمة للدمج
    try:
        df_old = pd.read_csv(URL_OLD)
        df_new = pd.read_csv(URL_NEW)
        existing_df = pd.concat([df_old, df_new], ignore_index=True)
        print(f"📦 Loaded {len(existing_df)} existing channels.")
    except:
        existing_df = pd.DataFrame(columns=['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])

    # 2. عملية الـ Scraping الجديدة
    new_results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        
        for keyword in KEYWORDS:
            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            try:
                await page.goto(f"https://xtea.pages.dev/search?q={encoded_query}", timeout=60000)
                await page.wait_for_selector(".gsc-webResult", timeout=15000)
                raw_html = await page.content()
                links = re.findall(r"t\.me\/[a-zA-Z0-9_\-]+", urllib.parse.unquote(raw_html))
                
                for link in set(links):
                    user = link.split('/')[-1]
                    if len(user) > 4 and "joinchat" not in user:
                        new_results.append({
                            "Keyword": keyword, "Channel Name": user,
                            "Link": f"https://t.me/{user}", "Subscribers": "N/A", "LatestID": None
                        })
            except: pass
            await page.close()
        await browser.close()

    # 3. الدمج النهائي ومسح التكرار
    final_df = pd.concat([existing_df, pd.DataFrame(new_results)], ignore_index=True)
    
    # التأكد من وجود الـ 5 عواميد المطلوبة فقط
    cols = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']
    for col in cols:
        if col not in final_df.columns: final_df[col] = None
    
    final_df = final_df[cols]
    
    # مسح التكرار بناءً على اللينك (الحفاظ على النسخة اللي فيها LatestID)
    final_df = final_df.sort_values(by='LatestID', ascending=False)
    final_df.drop_duplicates(subset=['Link'], keep='first', inplace=True)

    final_df.to_csv(SAVE_FILE, index=False, encoding='utf-8-sig')
    print(f"✨ Final File Saved: {len(final_df)} Unique Channels.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
