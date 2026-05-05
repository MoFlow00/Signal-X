import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re  # <--- هذا هو السطر الذي كان ناقصاً وتسبب في المشكلة
import requests
from bs4 import BeautifulSoup
import random
import time
import urllib.parse
import os

# ======================
# CONFIG
# ======================
PAGES_TO_SCRAPE = 3     # تم تقليلها لـ 3 لتقليل فرصة حظر جوجل السحابي
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "completed_keywords.txt"

KEYWORDS =  [
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
    "تقنيات حديثة", "شروحات تقنية",

    # Programming / Learning
    "free courses", "udemy coupons", "programming scripts",
    "github repos", "python coding", "excel tutorials",
    "data analysis python", "automation scripts",
    "كورسات مجانية", "دورة برمجية", "تعليم إكسيل",
    "تعلم البرمجة", "مكتبات بايثون", "كتب تقنية",

    # Deals / UAE
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

    # إضافي مفيد
    "free api key", "free llm", "open source tools",
    "telegram bots", "automation tools",
    "مواقع مفيدة", "قنوات مفيدة", "معلومات عامة",
    
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

    # عربي
    "محرك بحث تيليجرام", "بحث قنوات تيليجرام",
    "دليل قنوات تيليجرام", "اكتشاف قنوات",
    "بوت بحث تيليجرام", "قنوات تيليجرام مفيدة",
    "أقوى قنوات تيليجرام", "قنوات ترند تيليجرام"
]

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def save_progress(keyword):
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{keyword}\n")

def get_subscribers(username):
    try:
        r = requests.get(f"https://t.me/{username}", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        el = soup.select_one(".tgme_page_extra")
        return el.text.strip() if el else "N/A"
    except:
        return "error"

async def run_scraper():
    completed = load_progress()
    
    # تفريغ السجل إذا تم الانتهاء من جميع الكلمات للبدء من جديد
    if len(completed) >= len(KEYWORDS):
        print("All keywords processed previously. Resetting progress...")
        os.remove(PROGRESS_FILE)
        completed = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        for keyword in KEYWORDS:
            if keyword in completed:
                print(f"Skipping '{keyword}' (Already processed)")
                continue

            print(f"\n[{keyword}] -> Starting search...")
            page = await context.new_page()
            
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            usernames = set()
            invite_links = set()
            
            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    try:
                        await page.wait_for_selector(".gsc-webResult", timeout=15000)
                        await page.wait_for_timeout(3000)
                    except:
                        break # لا توجد نتائج أخرى

                    raw_html = await page.content()
                    decoded_html = urllib.parse.unquote(raw_html)
                    raw_matches = re.findall(r"t\.me\/[a-zA-Z0-9_\-\+\/\?=&]+", decoded_html)
                    
                    for link in raw_matches:
                        path = link.split("t.me/")[1]
                        clean_path = path.split("?")[0].split("&")[0].split("#")[0].strip()
                        if clean_path.startswith("s/"):
                            clean_path = clean_path[2:]
                            
                        if "joinchat" in clean_path.lower() or clean_path.startswith("+"):
                            invite_links.add(clean_path)
                        else:
                            username_only = clean_path.split("/")[0]
                            if len(username_only) > 4:
                                usernames.add(username_only.lower())

                    if current_page < PAGES_TO_SCRAPE:
                        next_btn = page.locator(f".gsc-cursor-page >> text='{current_page + 1}'")
                        if await next_btn.is_visible():
                            await next_btn.click()
                            await page.wait_for_timeout(3000)
                        else:
                            break
                            
            except Exception as e:
                print(f"Error fetching {keyword}: {e}")
                
            await page.close()

            # --- استخراج وحفظ البيانات ---
            results = []
            
            for user in usernames:
                subs = get_subscribers(user)
                results.append({
                    "Keyword": keyword,
                    "Channel Name": user,
                    "Link": f"https://t.me/{user}",
                    "Subscribers": subs
                })
                time.sleep(0.5) # تجنب حظر تليجرام

            for invite in invite_links:
                results.append({
                    "Keyword": keyword,
                    "Channel Name": invite,
                    "Link": f"https://t.me/{invite}",
                    "Subscribers": "Private / Invite"
                })

            if results:
                df = pd.DataFrame(results)
                # الحفظ المباشر في CSV
                if os.path.exists(SAVE_FILE):
                    df.to_csv(SAVE_FILE, mode='a', header=False, index=False, encoding="utf-8-sig")
                else:
                    df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                
                print(f"Saved {len(results)} channels for '{keyword}'")
            else:
                print(f"No channels found for '{keyword}'")

            # توثيق اكتمال الكلمة المفتاحية
            save_progress(keyword)
            
            # راحة إجبارية لتجنب حظر IP السيرفر من جوجل
            time.sleep(random.uniform(5, 10))

        await browser.close()
        print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_scraper())
