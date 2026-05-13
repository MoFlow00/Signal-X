import pandas as pd

# 1. روابط المصادر
URL_OLD = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/main/telegram_channels.csv"
URL_NEW = "https://raw.githubusercontent.com/MoFlow00/Signal-X/main/telegram_data.csv"
TARGET_FILE = "telegram_data.csv"

def perform_manual_merge():
    print("⏳ جاري سحب ودمج البيانات...")
    
    try:
        # قراءة الملفات
        df1 = pd.read_csv(URL_OLD)
        df2 = pd.read_csv(URL_NEW)
        
        # الدمج
        combined = pd.concat([df1, df2], ignore_index=True)
        
        # التأكد من وجود العواميد الخمسة المطلوبة فقط
        required_cols = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']
        for col in required_cols:
            if col not in combined.columns:
                combined[col] = None
        
        combined = combined[required_cols]
        
        # مسح التكرار بناءً على الرابط (Link)
        # نقوم بترتيب البيانات لضمان بقاء الصفوف التي تحتوي على LatestID
        combined['LatestID'] = pd.to_numeric(combined['LatestID'], errors='coerce')
        combined = combined.sort_values(by='LatestID', ascending=False)
        combined.drop_duplicates(subset=['Link'], keep='first', inplace=True)
        
        # الحفظ النهائي في الملف المحلي
        combined.to_csv(TARGET_FILE, index=False, encoding="utf-8-sig")
        print(f"✅ تم الدمج بنجاح! الملف الآن يحتوي على {len(combined)} قناة فريدة.")
        
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الدمج: {e}")

if __name__ == "__main__":
    perform_manual_merge()
