import pandas as pd
import asyncio
import re
import os
import random
from playwright.async_api import async_playwright

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

def get_username(link):
    link = link.rstrip('/')
    username = link.split('/')[-1].replace('@', '')
    if not username or any(x in username for x in ["+", "joinchat", "t.me/c/"]):
        return None
    return username

async def fetch_with_playwright(page, username):
    """يجيب آخر ID باستخدام Playwright"""
    if not username:
        return None
    
    urls = [
        f"https://t.me/s/{username}",           # الويب العامة (أسرع)
        f"https://tgstat.com/channel/@{username}" # TGStat (backup)
    ]
    
    for url in urls:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(random.uniform(2, 4))  # انتظر تحميل JS
            
            content = await page.content()
            
            # محاولة 1: t.me/s/username (الأفضل)
            ids = re.findall(r'data-post-id="(\d+)"', content)
            
            # محاولة 2: روابط /username/123
            if not ids:
                ids = re.findall(rf'/{re.escape(username)}/(\d+)', content)
            
            # محاولة 3: أي رقم كبير في الروابط
            if not ids:
                ids = re.findall(r'/(\d{3,})["/]', content)
            
            if ids:
                return int(max(ids, key=int))
                
        except Exception as e:
            print(f"⚠️ {url} failed: {e}")
            continue
    
    return None

async def sync():
    print("🚀 GitHub Actions Mode: Playwright Sync...")
    
    def load_safe(path):
        if not os.path.exists(path): 
            return pd.DataFrame(columns=COLS)
        try:
            return pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')
        except:
            return pd.DataFrame(columns=COLS)

    df_local = load_safe(LOCAL_DATA)
    df_manual = load_safe(MANUAL_DATA)
    
    combined = pd.concat([df_local, df_manual], ignore_index=True)
    combined = combined.reindex(columns=COLS).drop_duplicates(subset=['Link'], keep='first')
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    
    mask = combined['LatestID'].isna() | (combined['LatestID'] == 0)
    targets = combined.loc[mask, 'Link'].tolist()

    if not targets:
        print("✅ All IDs cached.")
        combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
        return

    print(f"🔍 Hunting {len(targets)} IDs via Playwright...")
    
    results = {}
    
    async with async_playwright() as p:
        # تشغيل Chromium headless مع stealth options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        
        page = await context.new_page()
        
        # تخطي Cloudflare لو ظهر (انتظار ديناميكي)
        for link in targets:
            username = get_username(link)
            latest_id = await fetch_with_playwright(page, username)
            results[link] = latest_id
            
            status = f"✅ ID={latest_id}" if latest_id else "❌ Failed"
            print(f"   {link:<40} {status}")
            
            # Rate limiting بين كل قناة والتانية
            await asyncio.sleep(random.uniform(3, 6))
        
        await browser.close()

    # تحديث البيانات
    for link, latest_id in results.items():
        if latest_id:
            combined.loc[combined['Link'] == link, 'LatestID'] = latest_id

    found = len([r for r in results.values() if r])
    print(f"\n📊 Sync Complete. Found {found}/{len(targets)} IDs.")
    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    asyncio.run(sync())
