import pandas as pd
import asyncio
import os
import re
import time
from telethon import TelegramClient
from telethon.sessions import StringSession

# ======================
# CONFIG & SECRETS
# ======================
API_ID = int(os.getenv('TG_API_ID', 0))
API_HASH = os.getenv('TG_API_HASH', '')
STRING_SESSION = os.getenv('TG_STRING_SESSION', '')

LOCAL_DATA = "telegram_data.csv"
MANUAL_DATA = "manual_channels.csv"
REMOTE_CHANNELS = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/refs/heads/main/telegram_channels.csv"
FINAL_FILE = "telegram_data.csv"
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

# ======================
# HELPERS
# ======================
def is_clean_lang(text):
    if not text or pd.isna(text): return True
    # يسمح فقط بالعربي والإنجليزي والأرقام والرموز
    pattern = r'^[\u0600-\u06FFa-zA-Z0-9\s._\-@()]+$'
    return bool(re.match(pattern, str(text)))

def safe_load_csv(path):
    if not os.path.exists(path): return pd.DataFrame(columns=COLS)
    try:
        # اكتشاف الفاصلة (, أو ;) تلقائياً وتخطي الأخطاء
        return pd.read_csv(path, sep=None, engine='python', on_bad_lines='skip', quotechar='"')
    except:
        return pd.DataFrame(columns=COLS)

async def hunt_latest_ids(links):
    """استخدام Telethon لجلب الـ IDs بدون بلوك وبسرعة عالية"""
    results = {}
    async with TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH) as client:
        for link in links:
            try:
                # استخراج اليوزرنيم من اللينك
                username = link.rstrip('/').split('/')[-1]
                if not username or "+" in username or "joinchat" in username:
                    results[link] = None
                    continue
                
                # الحصول على آخر رسالة (لا يتطلب الاشتراك في القناة)
                entity = await client.get_entity(username)
                messages = await client.get_messages(entity, limit=1)
                
                if messages:
                    results[link] = messages[0].id
                    print(f"✅ {username} -> ID: {messages[0].id}")
                else:
                    results[link] = None
            except Exception as e:
                print(f"⚠️ Skipping {link}: {str(e)[:50]}")
                results[link] = None
            
            # تأخير بسيط جداً للامتثال لقواعد تليجرام
            await asyncio.sleep(0.3)
    return results

# ======================
# MAIN SYNC
# ======================
def main():
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
    
    # ضمان وجود الأعمدة الصحيحة وحذف التكرار
    combined = combined.reindex(columns=COLS).drop_duplicates(subset=['Link'], keep='first')

    # فلتر اللغة (تطهير قاعدة البيانات)
    initial_len = len(combined)
    combined = combined[
        combined['Channel Name'].apply(is_clean_lang) & 
        combined['Keyword'].apply(is_clean_lang)
    ]
    print(f"🧹 Language Filter: Removed {initial_len - len(combined)} bad channels.")

    # تحديد القنوات التي تحتاج IDs
    combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    mask = combined['LatestID'].isna()
    targets = combined.loc[mask, 'Link'].tolist()

    if targets and STRING_SESSION:
        print(f"🎯 Hunting {len(targets)} IDs via API...")
        # تشغيل المحرك غير المتزامن
        id_results = asyncio.run(hunt_latest_ids(targets))
        
        # دمج النتائج
        combined['LatestID'] = combined['LatestID'].astype(object)
        combined.loc[mask, 'LatestID'] = [id_results.get(link) for link in targets]
        combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
    else:
        if not STRING_SESSION: print("❌ Error: TG_STRING_SESSION is missing!")
        else: print("😎 Everything is already up to date.")

    # حفظ الملف النهائي بترميز UTF-8
    combined.to_csv(FINAL_FILE, index=False, encoding='utf-8-sig')
    print(f"✅ Sync Finished. Total channels: {len(combined)}")

if __name__ == "__main__":
    main()
