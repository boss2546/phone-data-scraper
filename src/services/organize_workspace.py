import json
import csv
import re
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# โฟลเดอร์เป้าหมาย
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
LINKS_DIR = DATA_DIR / "links"
FACEBOOK_DIR = DATA_DIR / "facebook"
INSTAGRAM_DIR = DATA_DIR / "instagram"
ADVICE_DIR = DATA_DIR / "advice"

# สร้างโฟลเดอร์ให้ครบ
for d in [EXPORTS_DIR, LINKS_DIR, FACEBOOK_DIR, INSTAGRAM_DIR, ADVICE_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 1. ย้ายและจัดเก็บไฟล์จาก Root เข้าโฟลเดอร์
# ย้าย Facebook JSON
fb_raw = BASE_DIR / "facebook_group_user_posts_1786864985160.json"
if fb_raw.exists():
    shutil.move(str(fb_raw), str(FACEBOOK_DIR / "facebook_group_posts.json"))

# ลบไฟล์ว่าง
empty_fb = BASE_DIR / "facebook_posts.json"
if empty_fb.exists() and empty_fb.stat().st_size <= 2:
    empty_fb.unlink()

# ย้ายไฟล์ลิงก์
ig_links_raw = BASE_DIR / "instagram_all_links.txt"
if ig_links_raw.exists():
    shutil.copy(str(ig_links_raw), str(LINKS_DIR / "instagram_all_links.txt"))
    ig_links_raw.unlink()

# 2. ฟังก์ชันแปลง Unicode Bold / Decor ตัวอักษร
def clean_unicode(text: str) -> str:
    trans_table = {
        '𝟎': '0', '𝟏': '1', '𝟐': '2', '𝟑': '3', '𝟒': '4',
        '𝟓': '5', '𝟔': '6', '𝟕': '7', '𝟖': '8', '𝟗': '9',
        '𝐢': 'i', '𝐏': 'P', '𝐡': 'h', '𝐨': 'o', '𝐧': 'n', '𝐞': 'e',
        '𝐆': 'G', '𝐁': 'B', '𝐓': 'T', '𝐇': 'H', '𝐥': 'l', '𝐬': 's', '𝐮': 'u',
        '𝟔': '6', '𝟓': '5', '𝟎': '0', '𝟒': '4', '𝟗': '9', '𝟖': '8', '𝟕': '7',
        '𝗟': 'L', '𝗶': 'i', '𝗻': 'n', '𝗲': 'e'
    }
    for k, v in trans_table.items():
        text = text.replace(k, v)
    return text

# 3. จัดระเบียบข้อมูล Instagram Posts (228 โพสต์)
ig_data_file = INSTAGRAM_DIR / "all_posts_data.json"
if ig_data_file.exists():
    with open(ig_data_file, "r", encoding="utf-8") as f:
        ig_posts = json.load(f)

    cleaned_ig_products = []
    for item in ig_posts:
        idx = item.get("index")
        caption_raw = item.get("caption", "")
        norm = clean_unicode(caption_raw)
        
        # แยกข้อมูล
        # Model
        model_m = re.search(r'(iPhone\s*[0-9A-Za-z\s\+]+|iPad\s*[0-9A-Za-z\s]+)', norm, re.IGNORECASE)
        model = model_m.group(1).strip() if model_m else "โทรศัพท์มือสอง"
        
        # Storage
        storage_m = re.search(r'(\d+\s*GB|\d+\s*gb)', norm)
        storage = storage_m.group(1).upper() if storage_m else None
        
        # Region (TH / LL / ZA / etc)
        region = "TH" if "TH" in norm else ("LL" if "LL" in norm else "ศูนย์")
        
        # Price
        price_m = re.search(r'ราคา\s*[:\s]\s*([\d,]+)', norm)
        price = None
        if price_m:
            price = price_m.group(1).replace(",", "")
        else:
            num_m = re.search(r'\b([1-9]\d{0,2},\d{3})\b', norm)
            if num_m:
                price = num_m.group(1).replace(",", "")
        
        # Battery Health
        bat_m = re.search(r'(?:แบต|สุขภาพแบต|เบต้า)\s*[:\s]*(\d+)\s*%', norm)
        battery = f"{bat_m.group(1)}%" if bat_m else None
        
        # Warranty
        warr_m = re.search(r'ประกัน[^\n\r,]+', norm)
        warranty = warr_m.group(0).strip() if warr_m else "ประกันร้าน 15-30 วัน"
        
        # Local Image
        local_imgs = item.get("local_images", [])
        primary_img = local_imgs[0] if local_imgs else ""

        # Single line caption
        single_line_cap = re.sub(r'\s+', ' ', caption_raw).strip()

        cleaned_ig_products.append({
            "id": idx,
            "model": model,
            "storage": storage or "-",
            "region": region,
            "price_thb": int(price) if price and price.isdigit() else "-",
            "battery_health": battery or "-",
            "warranty": warranty,
            "image_path": primary_img,
            "post_url": item.get("post_url"),
            "caption": single_line_cap
        })

    # บันทึก CSV สะอาดเรียบร้อย (ไม่มีบรรทัดแตก)
    csv_file = EXPORTS_DIR / "instagram_products_cleaned.csv"
    fieldnames = ["id", "model", "storage", "region", "price_thb", "battery_health", "warranty", "image_path", "post_url", "caption"]
    with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_ig_products)

    # บันทึก JSON สะอาด
    with open(INSTAGRAM_DIR / "instagram_products_cleaned.json", "w", encoding="utf-8") as f:
        json.dump(cleaned_ig_products, f, ensure_ascii=False, indent=2)

    print(f"✅ บันทึก Instagram Cleaned Dataset: {csv_file}")

# 4. จัดระเบียบข้อมูล Facebook Posts
fb_data_file = FACEBOOK_DIR / "facebook_group_posts.json"
if fb_data_file.exists():
    with open(fb_data_file, "r", encoding="utf-8") as f:
        fb_posts = json.load(f)

    cleaned_fb_products = []
    for item in fb_posts:
        idx = item.get("post_index")
        content = item.get("content", "")
        
        model_m = re.search(r'(iPhone\s*[0-9A-Za-z\s\+]+|iPad\s*[0-9A-Za-z\s]+)', content, re.IGNORECASE)
        model = model_m.group(1).strip() if model_m else "โทรศัพท์มือสอง"
        
        storage_m = re.search(r'(\d+\s*GB|\d+\s*gb)', content)
        storage = storage_m.group(1).upper() if storage_m else None
        
        price_m = re.search(r'฿?([\d,]{4,6})', content)
        price = price_m.group(1).replace(",", "") if price_m else None
        
        bat_m = re.search(r'(?:แบต|สุขภาพแบต|เบต้า)\s*[:\s]*(\d+)\s*%', content)
        battery = f"{bat_m.group(1)}%" if bat_m else None

        cleaned_fb_products.append({
            "id": idx,
            "model": model,
            "storage": storage or "-",
            "price_thb": int(price) if price and price.isdigit() else "-",
            "battery_health": battery or "-",
            "post_url": item.get("post_url"),
            "images_count": item.get("images_count"),
            "content": re.sub(r'\s+', ' ', content).strip()
        })

    fb_csv_file = EXPORTS_DIR / "facebook_products_cleaned.csv"
    with open(fb_csv_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "model", "storage", "price_thb", "battery_health", "post_url", "images_count", "content"])
        writer.writeheader()
        writer.writerows(cleaned_fb_products)

    print(f"✅ บันทึก Facebook Cleaned Dataset: {fb_csv_file}")

print("✨ จัดระเบียบโฟลเดอร์และข้อมูลเสร็จสมบูรณ์เรียบร้อย!")
