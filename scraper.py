import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import requests
import random
import time
import urllib.parse
import os
import json

# ======================
# CONFIG & SOURCES
# ======================
SAVE_FILE = "telegram_data.csv"
PROGRESS_FILE = "progress_status.json"
# 💡 زودنا الصفحات لـ 15 عشان يجيب نتائج أكتر
PAGES_TO_SCRAPE = 15 
MAX_RUNTIME_SECONDS = 25 * 60 
START_TIME = time.time()
COLS = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']

KEYWORDS = [
    "premium apk", "pro apps", "modded apps", "unlocked apk", "android mod", "cracked software", 
    "nova launcher setup", "android apps paid free", "mod apk download", "apk hacks", "تطبيقات مهكرة", 
    "برامج برو", "أندرويد مدفوع", "ألعاب مهكرة", "تطبيقات معدلة", "نسخة احترافية",
    "machine learning", "best ai tools", "gpt4", "ai automation", "chatgpt tools", "ai prompts", 
    "openai tools", "llm tools", "ذكاء اصطناعي", "أدوات الذكاء", "تقنيات حديثة", "شروحات تقنية", "مواقع ذكاء اصطناعي",
    "sora ai", "claude ai", "gemini ai", "cursor ai", "bolt ai", "lovable ai", "deepseek", "suno ai", "capcut pro",
    "free courses", "udemy coupons", "programming scripts", "github repos", "python coding", "excel tutorials", 
    "data analysis python", "automation scripts", "كورسات مجانية", "دورة برمجية", "تعليم إكسيل", "تعلم البرمجة",
    "pdf books", "engineering books", "medical books", "ielts materials", "university notes", "study resources", 
    "research papers", "academic resources", "ebooks free", "ملفات pdf", "كتب جامعية",
    "uae offers", "dubai discounts", "coupon codes", "amazon deals uae", "noon coupons", "uae promo codes", 
    "dubai deals today", "عروض الإمارات", "أكواد خصم", "تخفيضات دبي", "وفر فلوسك",
    "iptv links", "netflix premium", "movies hd", "live tv", "series hd", "arab movies", "قنوات مشفرة", 
    "أفلام وثائقية", "بث مباشر", "سيرفرات iptv", "مسلسلات حصرية",
    "premium accounts", "shared accounts", "streaming accounts", "spotify premium", "canva pro", "youtube premium", 
    "adobe crack", "windows activator", "office activator", "software keys", "كورسات مدفوعة مجانا",
    "gaming leaks", "game mods", "steam free games", "pc games repack", "gaming news", "ps5 jailbreak", "قنوات ألعاب",
    "ethical hacking", "bug bounty", "osint tools", "cyber security", "kali linux", "هكر أخلاقي", "أمن سيبراني",
    "notion templates", "productivity apps", "video editing", "photoshop resources", "ui ux design", "مونتاج فيديو", "تصميم جرافيك",
    "side hustle", "make money online", "dropshipping", "الربح من الانترنت", "العمل اونلاين", "dubai tech", "uae startups", 
    "dubai events", "uae jobs", "وظائف دبي", "فعاليات دبي"
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
    if not os.path.exists(SAVE_FILE):
        pd.DataFrame(columns=COLS).to_csv(SAVE_FILE, index=False)

    print("\n🚀 Starting Deep Search...")
    progress = load_progress()
    
    # 💡 حركة ذكية: بنرتب الكلمات عشوائياً عشان كل ساعة يجرب حظه في كلمات مختلفة
    shuffled_keywords = KEYWORDS.copy()
    random.shuffle(shuffled_keywords)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
        
        for keyword in shuffled_keywords:
            if time.time() - START_TIME > MAX_RUNTIME_SECONDS: 
                print("⏱ Time limit reached. Stopping...")
                break

            last_page = progress.get(keyword, 0)
            if last_page >= PAGES_TO_SCRAPE: 
                # 💡 لو الكلمة "قديمة" وبحثنا فيها كتير، احتمال نرجع نبحث من صفحة 1 كل فترة
                if random.random() > 0.1: continue 
                else: last_page = 0 

            print(f"🔍 Keyword: {keyword} (Starting from page {last_page + 1})")
            page = await context.new_page()
            try:
                encoded = urllib.parse.quote(keyword)
                await page.goto(f"https://xtea.pages.dev/search?q={encoded}", wait_until="networkidle", timeout=60000)
                
                for cp in range(1, PAGES_TO_SCRAPE + 1):
                    if cp <= last_page: continue
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
                        
                        if matches:
                            new_data = []
                            for link in set(matches):
                                user = link.split('/')[-1]
                                if len(user) > 4 and "joinchat" not in user:
                                    new_data.append({"Keyword": keyword, "Channel Name": user, "Link": f"https://t.me/{user}", "Subscribers": "N/A", "LatestID": None})
                            
                            if new_data:
                                local_df = pd.read_csv(SAVE_FILE)
                                final_update = pd.concat([local_df, pd.DataFrame(new_data)], ignore_index=True)
                                final_update.drop_duplicates(subset=['Link'], keep='first', inplace=True)
                                final_update[COLS].to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
                        
                        save_progress(keyword, cp)
                        if time.time() - START_TIME > MAX_RUNTIME_SECONDS: break
                    except: break
            except: pass
            await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_scraper())
