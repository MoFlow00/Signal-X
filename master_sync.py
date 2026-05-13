import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os
import time
import random

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
REMOTE_CHANNELS = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/refs/heads/main/telegram_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_latest_id(link):
    time.sleep(random.uniform(0.3, 0.8))
    try:
        user = link.split('/')[-1].split('?')[0]
        if not user or "+" in user or "joinchat" in user: return None
        headers = {'User-Agent': random.choice(AGENTS)}
        r = requests.get(f"https://t.me/s/{user}", headers=headers, timeout=15)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, 'html.parser')
        msgs = soup.find_all('div', {'class': 'tgme_widget_message'})
        if msgs:
            last_post = msgs[-1].get('data-post')
            return last_post.split('/')[-1] if last_post else None
        return None
    except: return None

def sync():
    print("🔄 Merging all sources...")
    
    # 1. Load Local
    df_local = pd.read_csv(LOCAL_DATA) if os.path.exists(LOCAL_DATA) else pd.DataFrame(columns=COLS)
    
    # 2. Load Manual
    df_manual = pd.read_csv(MANUAL_DATA) if os.path.exists(MANUAL_DATA) else pd.DataFrame(columns=COLS)
    
    # 3. Load Remote
    try:
        df_remote = pd.read_csv(REMOTE_CHANNELS)
        df_remote.columns = df_remote.columns.str.strip().str.replace('_', ' ')
        df_remote.rename(columns={'ChannelName': 'Channel Name', 'channel name': 'Channel Name'}, inplace=True)
    except:
        df_remote = pd.DataFrame(columns=COLS)

    # Combine & Clean
    combined = pd.concat([df_local, df_manual, df_remote], ignore_index=True)
    
    for col in COLS:
        if col not in combined.columns: combined[col] = None
            
    combined = combined[COLS]
    combined.drop_duplicates(subset=['Link'], keep='first', inplace=True)
    
    # Hunt IDs
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    mask = combined['LatestID'].isna()
    targets = combined[mask]['Link'].tolist()

    if targets:
        print(f"🎯 Hunting IDs for {len(targets)} channels...")
        with ThreadPoolExecutor(max_workers=10) as ex:
            results = list(ex.map(get_latest_id, targets))
        combined.loc[mask, 'LatestID'] = results
    
    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ Sync Complete. Total: {len(combined)} channels.")

if __name__ == "__main__":
    sync()
