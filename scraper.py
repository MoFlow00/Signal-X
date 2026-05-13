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
MAX_RUNTIME_SECONDS = 30 * 60 
START_TIME = time.time()

# قائمة الكلمات المفتاحية (تم الإبقاء عليها كاملة)
KEYWORDS = [
    "premium apk", "pro apps", "modded apps", "unlocked apk",
    "android mod", "cracked software", "nova launcher setup",
    "android apps paid free", "mod apk download", "apk hacks",
    "تطبيقات مهكرة", "برامج برو", "أندرويد مدفوع",
    "ألعاب مهكرة", "تطبيقات معدلة", "نسخة احترافية",
    "machine learning", "best ai tools", "gpt4", "ai automation",
    "chatgpt tools", "ai prompts", "openai tools", "llm tools",
    "ذكاء اصطناعي", "أدوات الذكاء",
    "تقنيات حديثة", "شروحات تقنية", "مواقع ذكاء اصطناعي",
    "sora ai", "claude ai", "gemini ai", "cursor ai",
    "bolt ai", "lovable ai", "deepseek", "suno ai",
    "capcut pro", "free courses", "udemy coupons", "programming scripts",
    "github repos", "python coding", "excel tutorials",
    "data analysis python", "automation scripts",
    "كورسات مجانية", "دورة برمجية", "تعليم إكسيل",
    "تعلم البرمجة", "مكتبات بايثون", "كتب تقنية",
    "pdf books", "engineering books", "medical books",
    "ielts materials", "university notes", "study resources",
    "research papers", "academic resources",
    "ebooks free", "paid courses free",
    "ملفات pdf", "كتب جامعية",
    "uae offers", "dubai discounts", "coupon codes",
    "amazon deals uae", "noon coupons",
    "uae promo codes", "dubai deals today",
    "عروض الإمارات", "أكواد خصم",
    "تخفيضات دبي", "وفر فلوسك",
    "iptv links", "netflix premium", "movies hd",
    "live tv", "series hd", "arab movies",
    "قنوات مشفرة", "أفلام وثائقية", "بث مباشر",
    "سيرفرات iptv", "مسلسلات حصرية",
    "premium accounts", "shared accounts",
    "streaming accounts", "spotify premium",
    "canva pro", "youtube premium",
    "adobe crack", "windows activator",
    "office activator", "software keys",
    "serial keys", "warez",
    "كورسات مدفوعة مجانا",
    "اشتراكات مجانية",
    "gaming leaks", "game mods",
    "steam free games", "pc games repack",
    "gaming news", "ps5 jailbreak",
    "switch mods", "cheat engine",
    "قنوات ألعاب",
    "free api key", "free llm", "open source tools",
    "automation tools",
    "مواقع مفيدة", "معلومات عامة",
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
    "anime hd",
    "documentary films",
    "science videos",
    "football highlights",
    "mma highlights",
    "gaming clips",
    "انمي مترجم",
    "ملخصات مباريات",
    "وثائقيات",
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
    print("🚀 Starting Integrated Scraper (Search + Merge)...")
    progress = load_progress()
    fail_count = 0
    new_results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        for keyword in KEYWORDS:
            if fail_count >= 3:
                print("\n[!] Circuit Breaker Triggered. Exiting...")
                break

            last_page_finished = progress.get(keyword, 0)
            if last_page_finished >= PAGES_TO_SCRAPE:
                continue

            print(f"\n>>> [{keyword}] -> Page {last_page_finished + 1}")
            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            keyword_success = False

            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                        print(f"[!] Time limit reached.")
                        break

                    if current_page <= last_page_finished:
                        continue

                    print(f"  -- Scraping page {current_page}...")
                    try:
                        if current_page > 1:
                            next_btn = page.locator(f".gsc-cursor-page >> text='{current_page}'")
                            if await next_btn.is_visible():
                                await next_btn.click()
                                await page.wait_for_timeout(10000)
                            else: break
                        
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        raw_html = await page.content()
                        raw_matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-\+\/\?=&]+", urllib.parse.unquote(raw_html))
                        
                        for link in raw_matches:
                            path = link.split("t.me/")[1].strip("/")
                            if not path or "joinchat" in path.lower() or path.startswith("+"):
                                continue
                            clean_user = path.split("?")[0].split("&")[0].split("/")[0]
                            if clean_user.startswith("s/"):
                                clean_user = clean_user[2:]
                            
                            if len(clean_user) > 4:
                                new_results.append({
                                    "Keyword": keyword, 
                                    "Channel Name": clean_user, 
                                    "Link": f"https://t.me/{clean_user}", 
                                    "Subscribers": "N/A",
                                    "LatestID": None
                                })
                        
                        save_progress(keyword, current_page)
                        keyword_success = True
                        fail_count = 0
                        time.sleep(random.uniform(2, 5))

                    except Exception:
                        print(f"  [!] No more results on page {current_page}")
                        break

                if not keyword_success:
                    fail_count += 1

            except Exception as e:
                print(f"[!] Error loading {keyword}: {e}")
                fail_count += 1
            
            await page.close()
            time.sleep(random.uniform(10, 20))

        await browser.close()

    # --- مـنـطـق الـدمـج والـتـنـظـيـف الـنهـائي ---
    print("\n📦 Consolidating and Cleaning Data...")
    
    # 1. جلب البيانات الخارجية
    try:
        df_old = pd.read_csv(URL_OLD)
        df_new = pd.read_csv(URL_NEW)
        existing_df = pd.concat([df_old, df_new], ignore_index=True)
    except:
        existing_df = pd.DataFrame(columns=['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])

    # 2. تحويل النتائج الجديدة لـ DataFrame
    new_df = pd.DataFrame(new_results)
    
    # 3. الدمج الشامل
    final_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    # 4. توحيد العواميد الـ 5 المطلوبة
    cols = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']
    for col in cols:
        if col not in final_df.columns:
            final_df[col] = None
    final_df = final_df[cols]

    # 5. مسح التكرار مع الحفاظ على القنوات التي لها LatestID
    final_df['LatestID'] = pd.to_numeric(final_df['LatestID'], errors='coerce')
    final_df = final_df.sort_values(by='LatestID', ascending=False)
    final_df.drop_duplicates(subset=['Link'], keep='first', inplace=True)

    # 6. الحفظ النهائي
    final_df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
    print(f"✨ Success! Total unique channels: {len(final_df)}")

if __name__ == "__main__":
    asyncio.run(run_scraper())
