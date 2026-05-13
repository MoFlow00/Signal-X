import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor

# إعدادات
CSV_URL = "https://raw.githubusercontent.com/Mohamed4088/Telegram_Scrapper2/main/telegram_data.csv"
OUTPUT_FILE = "telegram_data.csv" # هيتحفظ في الـ Repo

def get_latest_id(link):
    try:
        username = link.split('t.me/')[1].split('/')[0].split('?')[0]
        if "+" in username or "joinchat" in username: return None
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        r = requests.get(f"https://t.me/s/{username}", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # البحث عن آخر رسالة
        messages = soup.find_all('div', {'class': 'tgme_widget_message'})
        if messages:
            last_post = messages[-1].get('data-post')
            if last_post:
                return last_post.split('/')[-1]
        return None
    except:
        return None

def process_radar():
    # 1. قراءة البيانات
    df = pd.read_csv(CSV_URL)
    
    # التأكد من وجود عمود LatestID
    if 'LatestID' not in df.columns:
        df['LatestID'] = None

    # 2. تحديث الـ IDs (باستخدام التوازي لتسريع العملية)
    print("Starting ID Hunting...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        # بنحدث فقط القنوات اللي معندناش ليها ID أو القنوات العامة
        links_to_check = df[df['LatestID'].isna()]['Link'].tolist()
        results = list(executor.map(get_latest_id, links_to_check))
        
        # دمج النتائج
        df.loc[df['LatestID'].isna(), 'LatestID'] = results

    # 3. حفظ الملف
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Update Done! Saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_radar()
