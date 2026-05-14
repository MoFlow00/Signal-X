import pandas as pd
import requests
import re
import os
import time
import random
from concurrent.futures import ThreadPoolExecutor

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

# مصدر خارجي (Mirror/Aggregator) بعيد عن خوادم تيليجرام
# سنستخدم TGStat كونه يمتلك أرشفة قوية
EXTERNAL_SOURCE_URL = "https://tgstat.com/channel/@{username}"

# وكلاء مستخدم (User-Agents) متنوعة لتبدو الطلبات طبيعية
AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
]

def get_latest_id_external(link):
    """سحب أحدث ID من مصدر خارجي (TGStat) لتجنب حظر تيليجرام"""
    try:
        # استخراج اليوزرنيم
        username = link.rstrip('/').split('/')[-1].replace('@', '')
        if not username or "+" in username or "joinchat" in username:
            return None

        # الطلب من المصدر الخارجي
        url = EXTERNAL_SOURCE_URL.format(username=username)
        headers = {'User-Agent': random.choice(AGENTS)}
        
        # انتظار عشوائي بسيط جداً (أقل بكثير من الـ API الرسمي)
        time.sleep(random.uniform(1.5, 3.0)) 
        
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code != 200:
            return None

        # البحث عن أحدث ID في روابط المنشورات داخل الموقع
        # الروابط في TGStat تكون بصيغة /channel/@username/123
        ids = re.findall(rf'/{username}/(\d+)"', r.text)
        
        if ids:
            return int(max(ids, key=int))
        return None
    except:
        return None

def sync():
    print("🚀 External Source Mode: Fetching via TGStat...")
    
    # تحميل الملفات (نفس المنطق السابق)
    def load_safe(path):
        if not os.path.exists(path): return pd.DataFrame(columns=COLS)
        return pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip')

    df_local = load_safe(LOCAL_DATA)
    df_manual = load_safe(MANUAL_DATA)
    
    combined = pd.concat([df_local, df_manual], ignore_index=True)
    combined = combined.reindex(columns=COLS).drop_duplicates(subset=['Link'], keep='first')

    # تحديد القنوات التي تحتاج تحديث
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    mask = combined['LatestID'].isna()
    targets = combined.loc[mask, 'Link'].tolist()

    if targets:
        print(f"🎯 Hunting {len(targets)} IDs via External Aggregator...")
        
        # استخدام ThreadPool لزيادة السرعة (عدد عمال متزن)
        with ThreadPoolExecutor(max_workers=5) as ex:
            results = list(ex.map(get_latest_id_external, targets))
        
        combined.loc[mask, 'LatestID'] = results
        print(f"✅ Sync Complete. Found {len([r for r in results if r])} IDs.")
    else:
        print("😎 All IDs are already cached.")

    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    sync()
