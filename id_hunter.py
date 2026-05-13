import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os

OUTPUT_FILE = "telegram_data.csv"

def get_latest_id(link):
    try:
        username = link.split('t.me/')[1].split('/')[0].split('?')[0]
        if "+" in username or "joinchat" in username: return None
        r = requests.get(f"https://t.me/s/{username}", timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        messages = soup.find_all('div', {'class': 'tgme_widget_message'})
        if messages:
            last_post = messages[-1].get('data-post')
            return last_post.split('/')[-1] if last_post else None
        return None
    except: return None

def run_update():
    if not os.path.exists(OUTPUT_FILE): return
    
    df = pd.read_csv(OUTPUT_FILE)
    if 'LatestID' not in df.columns: df['LatestID'] = None

    # فحص فقط الصفوف اللي محتاجة تحديث (الـ LatestID فيها فاضي)
    mask = df['LatestID'].isna() | (df['LatestID'] == "None")
    links_to_check = df[mask]['Link'].tolist()
    
    if links_to_check:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(get_latest_id, links_to_check))
        df.loc[mask, 'LatestID'] = results
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    run_update()
