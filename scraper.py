import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import requests
from bs4 import BeautifulSoup
import random
import time
import urllib.parse
import os
import json

# ======================
# CONFIG & SOURCES
# ======================
URL_OLD = "https://raw.githubusercontent.com/MoFlow00/Telegram_Scrapper/main/telegram_channels.csv"
URL_NEW = "https://raw.githubusercontent.com/MoFlow00/Signal-X/main/telegram_data.csv"
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "progress_status.json"
PAGES_TO_SCRAPE = 5
MAX_RUNTIME_SECONDS = 25 * 60 # تقليل الوقت لضمان الحفظ
START_TIME = time.time()

KEYWORDS = [
    # Android / Apps
    "premium apk", "pro apps", "modded apps", "unlocked apk",
    "android mod", "cracked software", "nova launcher setup",
    "android apps paid free", "mod apk download", "apk hacks",
    "تطبيقات مهكرة", "برامج برو", "أندرويد مدفوع",
    "ألعاب مهكرة", "تطبيقات معدلة", "نسخة احترافية",

    # AI / Tech
    "machine learning", "best ai tools", "gpt4", "ai automation",
    "chatgpt tools", "ai prompts", "openai tools", "llm tools",
    "ذكاء اصطناعي", "أدوات الذكاء",
    "تقنيات حديثة", "شروحات تقنية", "مواقع ذكاء اصطناعي",

    # Trending AI
    "sora ai", "claude ai", "gemini ai", "cursor ai",
    "bolt ai", "lovable ai", "deepseek", "suno ai",
    "capcut pro",

    # Programming / Learning
    "free courses", "udemy coupons", "programming scripts",
    "github repos", "python coding", "excel tutorials",
    "data analysis python", "automation scripts",
    "كورسات مجانية", "دورة برمجية", "تعليم إكسيل",
    "تعلم البرمجة", "مكتبات بايثون", "كتب تقنية",

    # Books / Study
    "pdf books", "engineering books", "medical books",
    "ielts materials", "university notes", "study resources",
    "research papers", "academic resources",
    "ebooks free", "paid courses free",
    "ملفات pdf", "كتب جامعية",

    # UAE / Deals
    "uae offers", "dubai discounts", "coupon codes",
    "amazon deals uae", "noon coupons",
    "uae promo codes", "dubai deals today",
    "عروض الإمارات", "أكواد خصم",
    "تخفيضات دبي", "وفر فلوسك",

    # Media / IPTV
    "iptv links", "netflix premium", "movies hd",
    "live tv", "series hd", "arab movies",
    "قنوات مشفرة", "أفلام وثائقية", "بث مباشر",
    "سيرفرات iptv", "مسلسلات حصرية",

    # Shared / Premium
    "premium accounts", "shared accounts",
    "streaming accounts", "spotify premium",
    "canva pro", "youtube premium",
    "adobe crack", "windows activator",
    "office activator", "software keys",
    "serial keys", "warez",
    "كورسات مدفوعة مجانا",
    "اشتراكات مجانية",

    # Gaming
    "gaming leaks", "game mods",
    "steam free games", "pc games repack",
    "gaming news", "ps5 jailbreak",
    "switch mods", "cheat engine",
    "قنوات ألعاب",

    # APIs / Tools
    "free api key", "free llm", "open source tools",
    "automation tools",
    "مواقع مفيدة", "معلومات عامة",

    # Cybersecurity / Privacy
    "ethical hacking",
    "bug bounty",
    "osint tools",
    "cyber security",
    "network security",
    "penetration testing",
    "kali linux",
    "linux tools",
    "privacy tools",
    "vpn deals",
    "security research",
    "هكر أخلاقي",
    "أمن سيبراني",
    "اختبار اختراق",
    "أدوات لينكس",

    # Productivity
    "notion templates",
    "obsidian vault",
    "productivity apps",
    "second brain",
    "time management",
    "remote work tools",
    "freelance tools",
    "startup tools",
    "قوالب نوتشن",
    "تنظيم الوقت",
    "العمل الحر",

    # Design / Content
    "video editing",
    "after effects presets",
    "premiere pro tips",
    "photoshop resources",
    "figma templates",
    "ui ux design",
    "graphic design",
    "content creation",
    "مونتاج فيديو",
    "تصميم جرافيك",
    "صناعة المحتوى",

    # Finance / Online Income
    "side hustle",
    "online business",
    "make money online",
    "dropshipping",
    "affiliate marketing",
    "crypto news",
    "stock market",
    "investing tools",
    "الربح من الانترنت",
    "العمل اونلاين",
    "الاستثمار",
    "العمل الحر",

    # AI Creation
    "ai image generation",
    "text to video ai",
    "ai voice tools",
    "ai coding assistant",
    "ai productivity",
    "prompt engineering",
    "local llm",
    "stable diffusion",
    "مولد صور بالذكاء الاصطناعي",
    "هندسة البرومبت",
    "نماذج محلية",

    # Developer / DevOps
    "docker tutorial",
    "kubernetes",
    "self hosted tools",
    "raspberry pi",
    "homelab",
    "server setup",
    "cloud computing",
    "devops tools",
    "aws tutorials",
    "github automation",
    "استضافة ذاتية",
    "إدارة سيرفرات",

    # Mobile / Devices
    "iphone tips",
    "samsung tricks",
    "android customization",
    "tech deals",
    "smart gadgets",
    "wearable tech",
    "tablet apps",
    "تطبيقات ايفون",
    "خدع أندرويد",
    "أجهزة ذكية",

    # Education / Career
    "cv templates",
    "interview questions",
    "tech interview",
    "linkedin tips",
    "career growth",
    "certifications",
    "english learning",
    "study hacks",
    "قوالب سيرة ذاتية",
    "تعلم الإنجليزية",
    "تطوير مهني",

    # Entertainment
    "anime hd",
    "documentary films",
    "science videos",
    "football highlights",
    "mma highlights",
    "gaming clips",
    "انمي مترجم",
    "ملخصات مباريات",
    "وثائقيات",

    # UAE / Local
    "dubai tech",
    "uae startups",
    "dubai events",
    "uae jobs",
    "dubai restaurants",
    "dubai nightlife",
    "امارات",
    "وظائف دبي",
    "فعاليات دبي"
]

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_progress(keyword, page):
    progress = load_progress()
    progress[keyword] = page
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=4)

async def run_scraper():
    print("🚀 Step 1: Immediate Merging of CSV files...")
    
    # --- مـنـطـق الـدمـج الـفـوري (أول شـيء يـحـدث) ---
    try:
        # محاولة قراءة الملفات من الروابط
        df1 = pd.read_csv(URL_OLD)
        df2 = pd.read_csv(URL_NEW)
        print(f"✅ Loaded {len(df1)} from Old and {len(df2)} from New.")
        
        combined_df = pd.concat([df1, df2], ignore_index=True)
        
        # توحيد العواميد
        cols = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']
        for col in cols:
            if col not in combined_df.columns: combined_df[col] = None
        combined_df = combined_df[cols]
        
        # مسح التكرار فوراً بناءً على اللينك
        combined_df.drop_duplicates(subset=['Link'], keep='first', inplace=True)
        
        # حفظ الملف المدمج كقاعدة أساسية قبل البدء
        combined_df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
        print(f"✨ Initial merge done! Base file has {len(combined_df)} unique channels.")
    except Exception as e:
        print(f"⚠️ Initial merge skipped or failed: {e}")

    print("\n🚀 Step 2: Starting Search for new channels...")
    progress = load_progress()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0...")
        
        for keyword in KEYWORDS:
            last_page = progress.get(keyword, 0)
            if last_page >= PAGES_TO_SCRAPE: continue

            print(f"🔍 Keyword: {keyword}")
            page = await context.new_page()
            try:
                encoded = urllib.parse.quote(keyword)
                await page.goto(f"https://xtea.pages.dev/search?q={encoded}", timeout=60000)
                
                for cp in range(1, PAGES_TO_SCRAPE + 1):
                    if cp <= last_page: continue
                    print(f"  -- Page {cp}")
                    
                    try:
                        if cp > 1:
                            btn = page.locator(f".gsc-cursor-page >> text='{cp}'")
                            if await btn.is_visible():
                                await btn.click()
                                await page.wait_for_timeout(8000)
                            else: break
                        
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        html = await page.content()
                        matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-]+", urllib.parse.unquote(html))
                        
                        # حفظ النتائج الجديدة فوراً في الملف (Append Mode)
                        if matches:
                            new_data = []
                            for link in set(matches):
                                user = link.split('/')[-1]
                                if len(user) > 4 and "joinchat" not in user:
                                    new_data.append([keyword, user, f"https://t.me/{user}", "N/A", None])
                            
                            new_df = pd.DataFrame(new_data, columns=cols)
                            # دمج مع الملف المحلي ومسح التكرار في كل صفحة
                            local_df = pd.read_csv(SAVE_FILE)
                            final_update = pd.concat([local_df, new_df], ignore_index=True)
                            final_update.drop_duplicates(subset=['Link'], keep='first', inplace=True)
                            final_update.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                        
                        save_progress(keyword, cp)
                        time.sleep(random.uniform(3, 6))
                    except: break
            except: pass
            await page.close()
            
            # توقف لو الوقت خلص
            if time.time() - START_TIME > MAX_RUNTIME_SECONDS: break

        await browser.close()
    print("✨ Process Completed.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
