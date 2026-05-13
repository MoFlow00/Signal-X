import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor
import os
import time
import re

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
REMOTE_CHANNELS = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/refs/heads/main/telegram_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

# تقليل العمال لتجنب البلوك السريع من GitHub IP
MAX_WORKERS = 10 

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
})

# ======================
# FILTERS & REGEX
# ======================
POST_REGEX = re.compile(r'data-post="[^"]+/(\d+)"')

def is_clean_lang(text):
    if not text or pd.isna(text): return True
    # حصر المحتوى في العربي والإنجليزي والرموز الأساسية فقط
    pattern = r'^[\u0600-\u06FFa-zA-Z0-9\s._\-@()]+$'
    return bool(re.match(pattern, str(text)))

def get_latest_id(link):
    try:
        user = link.rstrip('/').split('/')[-1]
        if not user or any(x in user for x in ["+", "joinchat", "telegram.me"]):
            return None

        # استخدام طلب محدد لجزء من الصفحة لتوفير الوقت والبيانات
        with session.get(f"https://t.me/s/{user}", timeout=15, stream=True) as r:
            if r.status_code != 200: return None
            # قراءة أول 50 كيلوبايت فقط (كافية لاستخراج المعرفات)
            text = r.raw.read(50000).decode('utf-8', errors='ignore')
            matches = POST_REGEX.findall(text)
            return int(max(matches, key=int)) if matches else None
    except:
        return None

def safe_load_csv(path):
    if not os.path.exists(path): return pd.DataFrame(columns=COLS)
    try:
        # استخدام sep=None لاكتشاف الفواصل (عادية أو منقوطة) تلقائياً
        return pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip', quotechar='"')
    except:
        return pd.DataFrame(columns=COLS)

# ======================
# CORE LOGIC
# ======================
def sync():
    print("🔄 Loading and Merging Sources...")
    df_local = safe_load_csv(LOCAL_DATA)
    df_manual = safe_load_csv(MANUAL_DATA)
    
    try:
        df_remote = pd.read_csv(REMOTE_CHANNELS, on_bad_lines='skip')
        df_remote.columns = df_remote.columns.str.strip().str.replace('_', ' ')
        df_remote.rename(columns={'ChannelName': 'Channel Name', 'channel name': 'Channel Name'}, inplace=True)
    except:
        df_remote = pd.DataFrame(columns=COLS)

    combined = pd.concat([df_local, df_manual, df_remote], ignore_index=True)
    combined = combined.reindex(columns=COLS).drop_duplicates(subset=['Link'], keep='first')

    # تنظيف اللغات
    initial_len = len(combined)
    combined = combined[combined['Channel Name'].apply(is_clean_lang) & combined['Keyword'].apply(is_clean_lang)]
    print(f"🧹 Language Filter: Removed {initial_len - len(combined)} channels")

    # تحديث المعرفات
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    mask = combined['LatestID'].isna()
    targets = combined.loc[mask, 'Link'].tolist()

    if targets:
        print(f"🎯 Hunting {len(targets)} IDs...")
        start = time.time()
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            results = list(ex.map(get_latest_id, targets))
        
        combined.loc[mask, 'LatestID'] = results
        print(f"⚡ Sync finished in {round(time.time()-start, 2)}s")

    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ Database updated: {len(combined)} channels total.")

if __name__ == "__main__":
    sync()
