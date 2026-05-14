import pandas as pd
import os
import re

# ======================
# CONFIG
# ======================
LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
REMOTE_CHANNELS = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/refs/heads/main/telegram_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

def is_clean_lang(text):
    if not text or pd.isna(text): return True
    # حصر المحتوى في العربي والإنجليزي فقط
    pattern = r'^[\u0600-\u06FFa-zA-Z0-9\s._\-@()]+$'
    return bool(re.match(pattern, str(text)))

def safe_load_csv(path):
    if not os.path.exists(path): return pd.DataFrame(columns=COLS)
    try:
        return pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip', quotechar='"')
    except:
        return pd.DataFrame(columns=COLS)

def sync():
    print("🔄 Merging and Cleaning Directory...")
    
    df_local = safe_load_csv(LOCAL_DATA)
    df_manual = safe_load_csv(MANUAL_DATA)
    
    try:
        df_remote = pd.read_csv(REMOTE_CHANNELS, on_bad_lines='skip')
        df_remote.columns = df_remote.columns.str.strip().str.replace('_', ' ')
        df_remote.rename(columns={'ChannelName': 'Channel Name', 'channel name': 'Channel Name'}, inplace=True)
    except:
        df_remote = pd.DataFrame(columns=COLS)

    combined = pd.concat([df_local, df_manual, df_remote], ignore_index=True)
    
    # تنظيف وتوحيد البيانات
    combined = combined.reindex(columns=COLS)
    combined.drop_duplicates(subset=['Link'], keep='first', inplace=True)

    # فلتر اللغة الصارم
    initial_len = len(combined)
    combined = combined[
        combined['Channel Name'].apply(is_clean_lang) & 
        combined['Keyword'].apply(is_clean_lang)
    ]
    
    print(f"🧹 Language Filter: Kept {len(combined)} clean channels out of {initial_len}.")
    
    # حفظ الملف
    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ Sync Finished. Directory is ready.")

if __name__ == "__main__":
    sync()
