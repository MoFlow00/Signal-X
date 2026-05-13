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
# CONFIG
# ======================
PAGES_TO_SCRAPE = 5  # تقليل الصفحات لتجنب البلوك السريع
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "progress_status.json"
MAX_RUNTIME_SECONDS = 30 * 60 
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

def get_subscribers(raw_username):
    lookup_name = raw_username.split("?")[0].split("#")[0]
    if lookup_name.startswith("s/"): lookup_name = lookup_name[2:]
    if "joinchat" in lookup_name or "+" in lookup_name: return "Private / Invite"
    try:
        r = requests.get(f"https://t.me/{lookup_name}", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        el = soup.select_one(".tgme_page_extra")
        return el.text.strip() if el else "N/A"
    except: return "error"

async def run_scraper():
    progress = load_progress()
    fail_count = 0  # عداد الفشل المتتالي للـ Circuit Breaker

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        for keyword in KEYWORDS:
            # القاطع الكهربائي: لو فشل في 3 كلمات ورا بعض يوقف الجلسة فوراً
            if fail_count >= 3:
                print("\n[!] Circuit Breaker Triggered: 3 consecutive timeouts. Google blocked the IP. Exiting...")
                break

            last_page_finished = progress.get(keyword, 0)
            if last_page_finished >= PAGES_TO_SCRAPE:
                continue

            print(f"\n>>> [{keyword}] -> Resuming from page {last_page_finished + 1}")
            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            keyword_success = False # مؤشر لنجاح الكلمة الحالية

            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                        print(f"[!] Time limit reached. Saving and exiting...")
                        await browser.close()
                        return

                    if current_page <= last_page_finished:
                        continue

                    print(f"  -- Scraping page {current_page}...")
                    try:
                        if current_page > 1:
                            next_btn = page.locator(f".gsc-cursor-page >> text='{current_page}'")
                            if await next_btn.is_visible():
                                await next_btn.click()
                                await page.wait_for_timeout(15000) # وقت كافٍ للتحميل
                            else: break
                        
                        # فحص وجود النتائج
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        
                        raw_html = await page.content()
                        raw_matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-\+\/\?=&]+", urllib.parse.unquote(raw_html))
                        
                        results = []
                        usernames = set()
                        for link in raw_matches:
                            path = link.split("t.me/")[1].strip("/")
                            if not path or path.lower() == "joinchat": continue
                            if not ("joinchat" in path.lower() or path.startswith("+")):
                                clean_user = path.split("?")[0].split("&")[0].split("/")[0]
                                if clean_user.startswith("s/"): clean_user = clean_user[2:]
                                if len(clean_user) > 4: usernames.add(clean_user.lower())

                        for user in usernames:
                            results.append({
                                "Keyword": keyword, 
                                "Channel Name": user, 
                                "Link": f"https://t.me/{user}", 
                                "Subscribers": get_subscribers(user)
                            })
                            time.sleep(random.uniform(1, 2))

                        if results:
                            df = pd.DataFrame(results)
                            df.to_csv(SAVE_FILE, mode='a', header=not os.path.exists(SAVE_FILE), index=False, encoding="utf-8-sig")
                            print(f"  [+] Saved {len(results)} items from page {current_page}")
                        
                        save_progress(keyword, current_page)
                        keyword_success = True
                        fail_count = 0 # تصفير عداد الفشل عند النجاح في أي صفحة
                        time.sleep(random.uniform(5, 10))

                    except Exception as e:
                        print(f"  [!] Error on page {current_page}: Timeout/No Results")
                        break # اخرج من صفحات الكلمة دي وجرب الكلمة اللي بعدها

                if not keyword_success:
                    fail_count += 1
                    print(f"  [!] Fail count incremented: {fail_count}/3")

            except Exception as e:
                print(f"[!] Critical Error loading keyword {keyword}: {e}")
                fail_count += 1
            
            await page.close()
            time.sleep(random.uniform(20, 40))

        await browser.close()
        print("Session completed.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
