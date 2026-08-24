import sys
import json
import re
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR

FACEBOOK_DATA_DIR = DATA_DIR / "facebook"
FACEBOOK_DATA_DIR.mkdir(parents=True, exist_ok=True)

class FacebookScraper:
    """Scraper สำหรับดึงโพสต์ใน Facebook Groups / Member Profile โดยใช้ Playwright หรือประมวลผล JSON ที่สกัดมา"""

    @staticmethod
    def parse_facebook_json(json_file_path: Path):
        """จัดระเบียบและแปลงข้อมูลจาก Facebook JSON ที่ดึงมาจาก Console / Playwright"""
        if not json_file_path.exists():
            return {"status": "error", "message": f"ไม่พบไฟล์ {json_file_path}"}

        with open(json_file_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        cleaned_products = []
        for item in posts:
            idx = item.get("post_index") or item.get("id")
            content = item.get("content", "")
            
            # 1. หารุ่นสินค้า
            model_m = re.search(r'(iPhone\s*[0-9A-Za-z\s\+]+|iPad\s*[0-9A-Za-z\s]+|Galaxy\s*[0-9A-Za-z\s\+]+)', content, re.IGNORECASE)
            model = model_m.group(1).strip() if model_m else "โทรศัพท์มือสอง"
            
            # 2. หาความจุ
            storage_m = re.search(r'(\d+\s*GB|\d+\s*gb|\d+\s*G)', content)
            storage = storage_m.group(1).upper() if storage_m else None
            
            # 3. หาราคา
            price_m = re.search(r'฿?([\d,]{4,6})', content)
            price = price_m.group(1).replace(",", "") if price_m else None
            
            # 4. หาสุขภาพแบตเตอรี่
            bat_m = re.search(r'(?:แบต|สุขภาพแบต|เบต้า)\s*[:\s]*(\d+)\s*%', content)
            battery = f"{bat_m.group(1)}%" if bat_m else None

            cleaned_products.append({
                "id": idx,
                "model": model,
                "storage": storage or "-",
                "price_thb": int(price) if price and price.isdigit() else "-",
                "battery_health": battery or "-",
                "post_url": item.get("post_url"),
                "images_count": item.get("images_count", len(item.get("images", []))),
                "images": item.get("images", []),
                "content": re.sub(r'\s+', ' ', content).strip()
            })

        out_path = FACEBOOK_DATA_DIR / "facebook_products_cleaned.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_products, f, ensure_ascii=False, indent=2)

        return {
            "status": "success",
            "total_posts": len(cleaned_products),
            "output_file": str(out_path),
            "data": cleaned_products
        }

    @staticmethod
    async def scrape_with_playwright(target_url: str, scrolls: int = 15):
        """รัน Playwright อัตโนมัติเพื่อดึงโพสต์จาก Facebook"""
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ กรุณาติดตั้ง playwright ก่อน: pip install playwright && playwright install chromium")
            return None

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(DATA_DIR / "facebook" / "session"),
                headless=False
            )
            page = await browser.new_page()
            print(f"🚀 กำลังเปิดหน้า: {target_url}")
            await page.goto(target_url)
            await page.wait_for_timeout(3000)

            print(f"⏳ กำลังเลื่อนหน้าจอ {scrolls} รอบ...")
            posts = await page.evaluate(f"""
                async () => {{
                    for (let i = 1; i <= {scrolls}; i++) {{
                        window.scrollBy({{ top: window.innerHeight * 1.5, behavior: 'smooth' }});
                        await new Promise(r => setTimeout(r, 1800));
                        document.querySelectorAll('div[role="button"]').forEach(b => {{
                            if (b.innerText === 'ดูเพิ่มเติม' || b.innerText === 'See more') b.click();
                        }});
                    }}

                    let postElements = document.querySelectorAll('div[role="article"]');
                    const results = [];
                    postElements.forEach((el, idx) => {{
                        const text = el.innerText || "";
                        const images = Array.from(el.querySelectorAll('img'))
                            .map(img => img.src)
                            .filter(src => src && src.includes('scontent') && !src.includes('p50x50'));
                        
                        const linkEl = el.querySelector('a[href*="/posts/"], a[href*="/permalink/"]');
                        const postUrl = linkEl ? linkEl.href.split('?')[0] : window.location.href;

                        if (text.length > 10) {{
                            results.push({{
                                post_index: idx + 1,
                                post_url: postUrl,
                                images_count: images.length,
                                images: images,
                                content: text
                            }});
                        }}
                    }});
                    return results;
                }}
            """)

            save_file = FACEBOOK_DATA_DIR / "facebook_group_posts.json"
            with open(save_file, "w", encoding="utf-8") as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)

            await browser.close()
            print(f"🎉 ดึงข้อมูลสำเร็จ: {len(posts)} โพสต์ บันทึกที่ {save_file}")
            return posts

if __name__ == "__main__":
    raw_fb_file = FACEBOOK_DATA_DIR / "facebook_group_posts.json"
    if raw_fb_file.exists():
        result = FacebookScraper.parse_facebook_json(raw_fb_file)
        print(f"✅ จัดระเบียบข้อมูล Facebook เรียบร้อย: {result['total_posts']} โพสต์ -> {result['output_file']}")
    else:
        print("💡 ใส่ URL หรือไฟล์ JSON เพื่อรัน Facebook Scraper")
