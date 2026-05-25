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

    # ─────────────────────────────
    # IPTV + STREAMING
    # ─────────────────────────────

    "iptv",
    "iptv عربي",
    "سيرفرات iptv",
    "اشتراك iptv",
    "بث مباشر",
    "قنوات رياضية",
    "bein sports",
    "شاهد vip",
    "netflix مجانا",
    "osn مجانا",
    "افلام",
    "مسلسلات",
    "movie app",
    "streaming apps",
    "live tv",
    "movies hd",
    "series hd",
    "anime عربي",
    "تطبيقات مشاهدة",
    "تطبيق افلام",

    # ─────────────────────────────
    # PREMIUM APPS + MODS
    # ─────────────────────────────

    "تطبيقات مهكرة",
    "برامج مهكرة",
    "apk مهكر",
    "apk معدل",
    "premium apps",
    "spotify مهكر",
    "youtube premium",
    "canva pro",
    "capcut pro",
    "vpn premium",
    "netflix premium",
    "chatgpt plus",
    "alight motion",
    "adobe crack",
    "windows activator",
    "office activator",
    "premium apk",
    "mod apk",
    "modded apps",
    "unlocked apk",
    "android mod",

    # ─────────────────────────────
    # AI + TOOLS
    # ─────────────────────────────

    "ذكاء اصطناعي",
    "ادوات ai",
    "ai tools",
    "chatgpt",
    "cursor ai",
    "claude ai",
    "gemini ai",
    "deepseek",
    "midjourney",
    "suno ai",
    "bolt ai",
    "lovable ai",
    "openai",
    "مولد صور ai",
    "بوتات تليجرام",
    "telegram bots",
    "free ai tools",
    "ai prompts",

    # ─────────────────────────────
    # TECH + INTERNET HACKS
    # ─────────────────────────────

    "تريكات",
    "خدع",
    "مواقع مفيدة",
    "تطبيقات مفيدة",
    "vpn مجاني",
    "proxy مجاني",
    "telegram tools",
    "free api",
    "open source tools",
    "ادوات تليجرام",
    "مواقع سرية",
    "مواقع رهيبة",
    "ادوات مجانية",
    "اختراق الواي فاي",

    # ─────────────────────────────
    # COURSES + BOOKS
    # ─────────────────────────────

    "كورسات مجانية",
    "دورات مدفوعة مجانا",
    "udemy مجانا",
    "coursera مجانا",
    "كورس برمجة",
    "تعلم البرمجة",
    "تعلم الذكاء الاصطناعي",
    "كتب pdf",
    "كتب تقنية",
    "ملفات pdf",
    "ebooks free",
    "study resources",
    "research papers",

    # ─────────────────────────────
    # GAMING
    # ─────────────────────────────

    "العاب مهكرة",
    "game mods",
    "steam free games",
    "pc games repack",
    "ps5 jailbreak",
    "gaming leaks",
    "قنوات العاب",
    "العاب pc",
    "العاب اندرويد",

    # ─────────────────────────────
    # CYBER SECURITY
    # ─────────────────────────────

    "هكر اخلاقي",
    "امن سيبراني",
    "ethical hacking",
    "bug bounty",
    "osint tools",
    "cyber security",
    "kali linux",

    # ─────────────────────────────
    # DESIGN + EDITING
    # ─────────────────────────────

    "مونتاج فيديو",
    "تصميم جرافيك",
    "video editing",
    "photoshop resources",
    "ui ux",
    "notion templates",
    "productivity apps",

    # ─────────────────────────────
    # MONEY + OFFERS
    # ─────────────────────────────

    "الربح من الانترنت",
    "العمل اونلاين",
    "side hustle",
    "make money online",
    "dropshipping",
    "عروض الامارات",
    "اكواد خصم",
    "كوبونات خصم",
    "تخفيضات دبي",
    "amazon deals",
    "noon coupons",
    "وفر فلوسك",

    # ─────────────────────────────
    # TELEGRAM DISCOVERY
    # ─────────────────────────────

    "قنوات تليجرام",
    "telegram channels",
    "telegram عربي",
    "telegram search",
    "telegram directory",
    "قنوات مفيدة",
    "قنوات ai",
    "قنوات افلام",
    "قنوات تطبيقات"

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
