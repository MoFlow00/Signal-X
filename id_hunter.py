import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os
import time
import random

FILE = "telegram_data.csv"

# قائمة User-Agents لتقليل احتمالية الحظر
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

def get_id(link):
    # إضافة تأخير عشوائي بسيط لكسر النمط (Pattern)
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        user = link.split('/')[-1].split('?')[0]
        if not user or "+" in user: return None
        
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        
        # محاولة السحب مع مهلة زمنية
        r = requests.get(f"https://t.me/s/{user}", headers=headers, timeout=15)
        
        if r.status_code == 429:
            print(f"🛑 Rate limited on: {user}. Need to slow down.")
            return None
            
        if r.status_code != 200: return None

        soup = BeautifulSoup(r.text, 'html.parser')
        messages = soup.find_all('div', {'class': 'tgme_widget_message'})
        
        if messages:
            # السحب من آخر رسالة حقيقية (لتجنب الرسائل المثبتة أحياناً)
            last_post = messages[-1].get('data-post')
            if last_post:
                return last_post.split('/')[-1]
        return None
    except Exception as e:
        return None

def run():
    if not os.path.exists(FILE): 
        print("❌ File not found.")
        return
        
    df = pd.read_csv(FILE)
    if 'LatestID' not in df.columns: df['LatestID'] = None
    
    # تحويل العمود لنصوص لضمان المقارنة الصحيحة
    df['LatestID'] = df['LatestID'].astype(str)
    
    mask = (df['LatestID'].isna()) | (df['LatestID'] == "None") | (df['LatestID'] == "nan")
    targets = df[mask]['Link'].tolist()
    
    if targets:
        print(f"🎯 Hunting IDs for {len(targets)} channels...")
        
        # تقليل عدد الـ workers لـ 5 لتجنب الحظر السريع
        with ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(get_id, targets))
        
        # تحديث الداتا
        df.loc[mask, 'LatestID'] = results
        df.to_csv(FILE, index=False, encoding='utf-8-sig')
        print(f"✅ IDs Updated. Found {len([r for r in results if r is not None])} new IDs.")
    else:
        print("Array is already up to date! 😎")

if __name__ == "__main__":
    run()
