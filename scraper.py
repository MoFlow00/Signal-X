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

# ======================
# CONFIG
# ======================
PAGES_TO_SCRAPE = 10
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "completed_keywords.txt"
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
    "ذكاء اصطناعي", "أدوات الذكاء", "بوتات تليجرام",
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
    "telegram bots", "automation tools",
    "مواقع مفيدة", "قنوات مفيدة", "معلومات عامة",

    # Telegram discovery
    "telegram channels",
    "best telegram channels",
    "top telegram groups",
    "telegram communities",
    "telegram groups",
    "telegram mega groups",
    "join telegram channel",
    "telegram invite links",
    "telegram public channels",
    "telegram supergroups",
    "telegram communities list",
    "telegram hidden gems",
    "telegram archive",
    "telegram hub",
    "telegram collection",

    # Telegram search / discovery
    "telegram search engine", "telegram directory", "telegram channels list",
    "telegram channels search", "telegram groups search", "telegram finder",
    "telegram explorer", "telegram catalog", "telegram index",

    # Bots & tools
    "telegram search bot", "telegram finder bot", "telegram index bot",
    "telegram scraper bot", "telegram crawler", "telegram analytics bot",

    # Growth / discovery
    "telegram trending channels", "telegram popular channels",
    "telegram viral channels", "telegram growth tips",
    "telegram marketing", "telegram seo",

    # Tech side
    "telegram api", "telegram scraping", "telegram data",
    "telegram automation tools", "telegram bots development",

    # Regional
    "india telegram channels",
    "arab telegram groups",
    "uae telegram",
    "egypt telegram",
    "dubai community",
    "saudi telegram",

    # Arabic Telegram
    "محرك بحث تيليجرام",
    "بحث قنوات تيليجرام",
    "دليل قنوات تيليجرام",
    "اكتشاف قنوات",
    "بوت بحث تيليجرام",
    "قنوات تيليجرام مفيدة",
    "أقوى قنوات تيليجرام",
    "قنوات ترند تيليجرام",
    "جروبات تيليجرام",
    "قنوات تيليجرام",
    "روابط تيليجرام",
    "قنوات تقنية",
    "جروبات تعليم",
    "قنوات ذكاء اصطناعي",
    "قنوات أفلام",
    "تسريبات",
    "برامج مهكرة"
]

# تعديل السلوك: ترتيب عشوائي للكلمات في كل تشغيل
random.shuffle(KEYWORDS)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_progress(keyword):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{keyword}\n")

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
    completed = load_progress()
    
    # تعديل السلوك: إيقاف التصفير التلقائي للسجل لضمان عدم التكرار
    if len(completed) >= len(KEYWORDS):
        print("!!! ALL KEYWORDS COMPLETED SUCCESSFULLY !!!")
        print("Add new keywords to the list to continue.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
        )
        
        for keyword in KEYWORDS:
            if time.time() - START_TIME > MAX_RUNTIME_SECONDS:
                print(f"\n[!] Time limit reached. Saving progress...")
                break

            if keyword in completed:
                continue

            print(f"[{keyword}] -> Searching...")
            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            usernames, invite_links = set(), set()
            
            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    try:
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        await page.wait_for_timeout(15000) # زيادة وقت الانتظار
                    except: break

                    raw_html = await page.content()
                    raw_matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-\+\/\?=&]+", urllib.parse.unquote(raw_html))
                    
                    for link in raw_matches:
                        path = link.split("t.me/")[1].strip("/")
                        if not path or path.lower() == "joinchat": continue
                        if "joinchat" in path.lower() or path.startswith("+"): invite_links.add(path)
                        else:
                            clean_user = path.split("?")[0].split("&")[0].split("/")[0]
                            if clean_user.startswith("s/"): clean_user = clean_user[2:]
                            if len(clean_user) > 4: usernames.add(clean_user.lower())

                    if current_page < PAGES_TO_SCRAPE:
                        next_btn = page.locator(f".gsc-cursor-page >> text='{current_page + 1}'")
                        if await next_btn.is_visible():
                            await next_btn.click()
                            await page.wait_for_timeout(3000)
                        else: break
            except: pass
            await page.close()

            results = []
            for user in usernames:
                results.append({"Keyword": keyword, "Channel Name": user, "Link": f"https://t.me/{user}", "Subscribers": get_subscribers(user)})
                time.sleep(random.uniform(1, 2)) # تأخير بسيط بين فحص المشتركين

            for invite in invite_links:
                results.append({"Keyword": keyword, "Channel Name": invite, "Link": f"https://t.me/{invite}", "Subscribers": "Private / Invite"})

            if results:
                df = pd.DataFrame(results)
                df.to_csv(SAVE_FILE, mode='a', header=not os.path.exists(SAVE_FILE), index=False, encoding="utf-8-sig")
                print(f"Saved {len(results)} items for '{keyword}'")
            
            save_progress(keyword)
            # تعديل السلوك: زيادة وقت الراحة بين الكلمات لتفادي الحظر
            wait_time = random.uniform(20, 45)
            print(f"Waiting {int(wait_time)}s before next keyword...")
            time.sleep(wait_time)

        await browser.close()
        print("Session completed.")

if __name__ == "__main__":
    asyncio.run(run_scraper())
