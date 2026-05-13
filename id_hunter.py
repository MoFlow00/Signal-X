import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os
import time
import random

FILE = "telegram_data.csv"
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_latest_id(link):
    time.sleep(random.uniform(0.5, 1.2))
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

def run():
    if not os.path.exists(FILE): return
    df = pd.read_csv(FILE)
    if 'LatestID' not in df.columns: df['LatestID'] = None
    
    df['LatestID'] = pd.to_numeric(df['LatestID'], errors='coerce')
    mask = df['LatestID'].isna()
    targets = df[mask]['Link'].tolist()
    
    if targets:
        print(f"🎯 Hunting IDs for {len(targets)} channels...")
        with ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(get_latest_id, targets))
        
        df.loc[mask, 'LatestID'] = results
        df.to_csv(FILE, index=False, encoding='utf-8-sig')
        print(f"✅ Found {len([r for r in results if r])} new IDs.")
    else:
        print("😎 All IDs are up to date.")

if __name__ == "__main__":
    run()
