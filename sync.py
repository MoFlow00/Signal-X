import pandas as pd
import requests
import re
import os
import time
import random

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

# مفتاح ScrapingAnt من GitHub Secrets
SCRAPINGANT_API_KEY = os.getenv("SCRAPINGANT_API_KEY", "")

def get_username(link):
    """يستخرج اليوزرنيم من أي لينك تلجرام"""
    # ⚠️ إصلاح NaN: تأكد إن الـ link string مش float/NaN
    if pd.isna(link) or not isinstance(link, str):
        return None
    
    link = link.rstrip('/')
    username = link.split('/')[-1].replace('@', '')
    if not username or any(x in username for x in ["+", "joinchat", "t.me/c/"]):
        return None
    return username

def fetch_via_scrapingant(username):
    """يستخدم ScrapingAnt API لتجاوز Cloudflare"""
    if not username or not SCRAPINGANT_API_KEY:
        return None
    
    url = f"https://t.me/s/{username}"
    api_url = "https://api.scrapingant.com/v2/general"
    
    params = {
        'url': url,
        'x-api-key': SCRAPINGANT_API_KEY,
        'browser': 'false',
        'proxy_country': 'US'
    }
    
    try:
        r = requests.get(api_url, params=params, timeout=30)
        if r.status_code != 200:
            print(f"⚠️ Status {r.status_code} for @{username}")
            return None
        
        content = r.text
        
        # استخراج ID
        ids = re.findall(r'data-post-id="(\d+)"', content)
        if not ids:
            ids = re.findall(rf'/{re.escape(username)}/(\d+)', content)
        if not ids:
            ids = re.findall(r'/(\d{3,})["/]', content)
        
        if ids:
            return int(max(ids, key=int))
            
    except Exception as e:
        print(f"⚠️ Error for @{username}: {e}")
    
    return None

def sync():
    print("🚀 GitHub Actions Mode: ScrapingAnt API...")
    
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
    combined = combined.reindex(columns=COLS)
    
    # ⚠️ إصلاح NaN: نظف عمود Link
    combined['Link'] = combined['Link'].astype(str).replace('nan', pd.NA)
    combined = combined.dropna(subset=['Link'])  # احذف الصفوف الفاضية
    combined = combined[combined['Link'] != 'nan']  # تأكد إضافية
    combined = combined.drop_duplicates(subset=['Link'], keep='first')
    
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    
    mask = combined['LatestID'].isna() | (combined['LatestID'] == 0)
    targets = combined.loc[mask, 'Link'].tolist()

    if not targets:
        print("✅ All IDs cached.")
        combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
        return

    print(f"🔍 Hunting {len(targets)} IDs via ScrapingAnt...")
    
    results = {}
    for link in targets:
        username = get_username(link)
        latest_id = fetch_via_scrapingant(username)
        results[link] = latest_id
        
        status = f"✅ ID={latest_id}" if latest_id else "❌ Failed"
        print(f"   {link:<40} {status}")
        
        time.sleep(random.uniform(2, 5))

    for link, latest_id in results.items():
        if latest_id:
            combined.loc[combined['Link'] == link, 'LatestID'] = latest_id

    found = len([r for r in results.values() if r])
    print(f"\n📊 Sync Complete. Found {found}/{len(targets)} IDs.")
    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    sync()
