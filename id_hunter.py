import pandas as pd
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

# الإعدادات المباشرة لرابط ملفك
CSV_URL = "https://raw.githubusercontent.com/Mohamed4088/Telegram_Scrapper2/main/telegram_data.csv"
OUTPUT_FILE = "telegram_data.csv"

def get_latest_id(link):
    if not isinstance(link, str) or 't.me/' not in link:
        return None
    try:
        # استخراج المعرف البرمجي للقناة
        username = link.split('t.me/')[1].split('/')[0].split('?')[0]
        if "+" in username or "joinchat" in username: 
            return None
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        # الدخول لصفحة المعاينة العامة
        r = requests.get(f"https://t.me/s/{username}", headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # البحث عن أحدث معرف رسالة في الصفحة
        messages = soup.find_all('div', {'class': 'tgme_widget_message'})
        if messages:
            last_post = messages[-1].get('data-post')
            if last_post:
                return last_post.split('/')[-1]
        return None
    except:
        return None

def run_update():
    print("Reading data from GitHub...")
    df = pd.read_csv(CSV_URL)
    
    # إضافة العمود إذا لم يكن موجوداً
    if 'LatestID' not in df.columns:
        df['LatestID'] = None

    # تحديث المعرفات للقنوات العامة التي تفتقر للمعرف
    print("Hunting for Latest IDs...")
    mask = df['LatestID'].isna() & (~df['Link'].str.contains('\+', na=False))
    links_to_check = df[mask]['Link'].tolist()
    
    if not links_to_check:
        print("No new IDs to fetch.")
        return

    # استخدام ThreadPool لتسريع العملية (10 خيوط متوازية)
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(get_latest_id, links_to_check))
    
    df.loc[mask, 'LatestID'] = results

    # حفظ الملف بصيغة utf-8-sig لضمان دعم اللغة العربية في Excel
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"Update complete. File saved as {OUTPUT_FILE}")

if __name__ == "__main__":
    run_update()
