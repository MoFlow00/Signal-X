import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
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
PAGES_TO_SCRAPE = 5
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
    "stock market",
    "investing tools",
    "الربح من الانترنت",
    "العمل اونلاين",
    "الاستثمار",

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

async def run_scraper():
    print("🚀 Starting Integrated Scraper (Search + Merge)...")
    
    # 1. جلب البيانات القديمة للدمج
    try:
        df_old = pd.read_csv(URL_OLD)
        df_new = pd.read_csv(URL_NEW)
        existing_df = pd.concat([df_old, df_new], ignore_index=True)
    except Exception as e:
        print(f"⚠️ Warning during initial load: {e}")
        existing_df = pd.DataFrame(columns=['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID'])

    # 2. منطق البحث الأصلي (Playwright) في xtea
    new_results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        for keyword in KEYWORDS:
            print(f"🔍 Searching for: {keyword}")
            page = await context.new_page()
            encoded_query = urllib.parse.quote(keyword)
            target_url = f"https://xtea.pages.dev/search?q={encoded_query}"
            
            try:
                await page.goto(target_url, wait_until="networkidle", timeout=60000)
                for current_page in range(1, PAGES_TO_SCRAPE + 1):
                    if current_page > 1:
                        next_btn = page.locator(f".gsc-cursor-page >> text='{current_page}'")
                        if await next_btn.is_visible():
                            await next_btn.click()
                            await page.wait_for_timeout(10000)
                        else:
                            break
                    
                    try:
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
                    except:
                        print(f"No more results for {keyword} on page {current_page}")
                        break
                    
                    time.sleep(random.uniform(2, 5))
            except Exception as e:
                print(f"⚠️ Error with keyword {keyword}: {e}")
            await page.close()
        await browser.close()

    # 3. الدمج النهائي والتنظيف
    new_df = pd.DataFrame(new_results)
    final_df = pd.concat([existing_df, new_df], ignore_index=True)
    
    required_cols = ['Keyword', 'Channel Name', 'Link', 'Subscribers', 'LatestID']
    for col in required_cols:
        if col not in final_df.columns:
            final_df[col] = None
    
    final_df = final_df[required_cols]

    # تحويل LatestID لرقم لضمان الترتيب الصحيح
    final_df['LatestID'] = pd.to_numeric(final_df['LatestID'], errors='coerce')
    final_df = final_df.sort_values(by='LatestID', ascending=False)
    final_df.drop_duplicates(subset=['Link'], keep='first', inplace=True)

    # 4. الحفظ النهائي
    final_df.to_csv(SAVE_FILE, index=False, encoding="utf-8-sig")
    print(f"✨ Task Done! Total unique channels in {SAVE_FILE}: {len(final_df)}")

if __name__ == "__main__":
    asyncio.run(run_scraper())
