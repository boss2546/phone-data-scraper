import sys
import json
import csv
import time
import re
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR, JSON_DIR, EXPORTS_DIR

def clean_unicode_digits(text: str) -> str:
    """แปลงตัวเลข Mathematical Bold / Unicode เช่น 𝟔,𝟓𝟓𝟎 หรือ 𝟏𝟏 เป็นเลขธรรมดา 6,550 หรือ 11"""
    trans_table = {
        '𝟎': '0', '𝟏': '1', '𝟐': '2', '𝟑': '3', '𝟒': '4',
        '𝟓': '5', '𝟔': '6', '𝟕': '7', '𝟖': '8', '𝟗': '9',
        '𝐢': 'i', '𝐏': 'P', '𝐡': 'h', '𝐨': 'o', '𝐧': 'n', '𝐞': 'e',
        '𝐆': 'G', '𝐁': 'B', '𝐓': 'T', '𝐇': 'H', '𝐥': 'l', '𝐬': 's', '𝐮': 'u'
    }
    for k, v in trans_table.items():
        text = text.replace(k, v)
    return text

def parse_post_content(raw_text: str):
    """แยกแยะข้อมูลสินค้า: รุ่น, ราคา, ความจุ, สุขภาพแบตเตอรี่"""
    normalized = clean_unicode_digits(raw_text)
    
    # 1. หาชื่อรุ่น (เช่น iPhone 11, iPhone 8 Plus, iPad, ฯลฯ)
    model_match = re.search(r'(iPhone\s*[0-9A-Za-z\s\+]+|iPad\s*[0-9A-Za-z\s]+)', normalized, re.IGNORECASE)
    model = model_match.group(1).strip() if model_match else "โทรศัพท์มือสอง"

    # 2. หาความจุ (เช่น 64GB, 128GB, 256GB)
    storage_match = re.search(r'(\d+\s*GB|\d+\s*gb)', normalized)
    storage = storage_match.group(1).upper() if storage_match else None

    # 3. หาราคา (เช่น ราคา : 6,550.- หรือ 25,990)
    price_match = re.search(r'ราคา\s*[:\s]\s*([\d,]+)', normalized)
    price = None
    if price_match:
        price = price_match.group(1).replace(",", "")
    else:
        # fallback ค้นหาตัวเลขหลักพัน
        digits_match = re.search(r'\b([1-9]\d{0,2},\d{3})\b', normalized)
        if digits_match:
            price = digits_match.group(1).replace(",", "")

    # 4. หาสุขภาพแบตเตอรี่
    battery_match = re.search(r'(?:แบต|สุขภาพแบต|เบต้า)\s*[:\s]*(\d+)\s*%', normalized)
    battery = f"{battery_match.group(1)}%" if battery_match else None

    return {
        "model": model,
        "storage": storage,
        "price": int(price) if price and price.isdigit() else None,
        "battery": battery
    }

def process_all_instagram_links(limit: int = 50):
    links_file = Path("instagram_all_links.txt")
    if not links_file.exists():
        print("❌ ไม่พบไฟล์ instagram_all_links.txt")
        return

    with open(links_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print("=" * 60)
    print(f"🚀 เริ่มต้นประมวลผลลิงก์ Instagram ({len(urls)} ลิงก์ทั้งหมด)...")
    print(f"⏳ กำลังดึงข้อมูล {min(limit, len(urls))} โพสต์แรก...")
    print("=" * 60)

    results = []
    for i, post_url in enumerate(urls[:limit], 1):
        clean_url = post_url.split("?")[0]
        oembed_url = f"https://www.instagram.com/api/v1/oembed/?url={clean_url}"
        
        try:
            req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode("utf-8"))
            
            raw_caption = data.get("title", "")
            parsed = parse_post_content(raw_caption)
            
            item = {
                "index": i,
                "post_url": clean_url,
                "model": parsed["model"],
                "storage": parsed["storage"],
                "price": parsed["price"],
                "battery": parsed["battery"],
                "thumbnail_url": data.get("thumbnail_url"),
                "author": data.get("author_name"),
                "caption": raw_caption
            }
            results.append(item)
            print(f"[{i}/{min(limit, len(urls))}] ✅ {parsed['model']} | ราคา: {parsed['price'] or '-'} บาท")
            time.sleep(0.3)  # หน่วงเวลาเล็กน้อยเพื่อความสุภาพกับ API
        except Exception as e:
            print(f"[{i}/{min(limit, len(urls))}] ⚠️ ไม่สามารถดึง {clean_url}: {e}")

    # 1. บันทึกเป็น JSON
    json_out = JSON_DIR / "instagram_batch_posts.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 2. บันทึกเป็น CSV (Excel)
    csv_out = EXPORTS_DIR / "instagram_products.csv"
    fieldnames = ["index", "model", "storage", "price", "battery", "post_url", "thumbnail_url", "caption"]
    with open(csv_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in results:
            writer.writerow(item)

    print("\n" + "=" * 60)
    print(f"🎉 ประมวลผลเสร็จสิ้น {len(results)} โพสต์!")
    print(f"📄 บันทึกไฟล์ JSON: {json_out}")
    print(f"📊 บันทึกไฟล์ CSV (Excel): {csv_out}")
    print("=" * 60)

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    process_all_instagram_links(limit=limit)
