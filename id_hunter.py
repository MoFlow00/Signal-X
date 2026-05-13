import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os

FILE = "telegram_data.csv"

def get_id(link):
    try:
        user = link.split('/')[-1]
        r = requests.get(f"https://t.me/s/{user}", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        msgs = soup.find_all('div', {'class': 'tgme_widget_message'})
        return msgs[-1].get('data-post').split('/')[-1] if msgs else None
    except: return None

def run():
    if not os.path.exists(FILE): return
    df = pd.read_csv(FILE)
    if 'LatestID' not in df.columns: df['LatestID'] = None
    
    # تحديث الخانات الفاضية فقط
    mask = df['LatestID'].isna() | (df['LatestID'] == "None")
    targets = df[mask]['Link'].tolist()
    
    if targets:
        print(f"🎯 Hunting IDs for {len(targets)} channels...")
        with ThreadPoolExecutor(max_workers=15) as ex:
            ids = list(ex.map(get_id, targets))
        df.loc[mask, 'LatestID'] = ids
        df.to_csv(FILE, index=False, encoding='utf-8-sig')
        print("✅ IDs Updated.")

if __name__ == "__main__":
    run()
