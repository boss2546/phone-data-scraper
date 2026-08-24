import sys
import json
import csv
import re
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR, DEFAULT_HEADERS

COMPASIA_DIR = DATA_DIR / "compasia"
COMPASIA_IMAGES_DIR = DATA_DIR / "images" / "compasia"
EXPORTS_DIR = DATA_DIR / "exports"

COMPASIA_DIR.mkdir(parents=True, exist_ok=True)
COMPASIA_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

def clean_html(html_text: str) -> str:
    """แปลง HTML เป็นข้อความสะอาด"""
    if not html_text:
        return ""
    text = re.sub(r'<br\s*/?>', '\n', html_text)
    text = re.sub(r'</p>', '\n', text)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&')
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    return '\n'.join(lines)

def parse_accessories_and_battery(body_text: str):
    """แยกข้อมูลอุปกรณ์ที่ได้รับและสุขภาพแบตเตอรี่"""
    accessories = []
    battery_health = "80-100%"
    warranty = "รับประกันสินค้า 1 เดือน"

    lines = body_text.split('\n')
    for line in lines:
        if "กล่อง" in line or "อะแดปเตอร์" in line or "สายชาร์จ" in line or "เคส" in line or "ฟิล์ม" in line or "อุปกรณ์" in line:
            accessories.append(line)
        if "สุขภาพแบต" in line or "แบต" in line:
            bat_m = re.search(r'สุขภาพแบต[^\n\r]+', line)
            if bat_m:
                battery_health = bat_m.group(0)
        if "ประกัน" in line:
            warr_m = re.search(r'ประกัน[^\n\r]+', line)
            if warr_m:
                warranty = warr_m.group(0)

    acc_str = ' | '.join(accessories) if accessories else "บรรจุในกล่อง CompAsia (ไม่มีหัวชาร์จ/สายชาร์จ)"
    return acc_str, battery_health, warranty

def fetch_product_details(index: int, product_url: str):
    """ดึงข้อมูลสินค้าทั้งหมดจาก CompAsia JSON API"""
    clean_url = product_url.strip().split("?")[0].rstrip("/")
    handle = clean_url.split("/")[-1]
    
    encoded_handle = urllib.parse.quote(handle)
    json_api_url = f"https://compasia.co.th/products/{encoded_handle}.json"
    
    try:
        req = urllib.request.Request(json_api_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=12) as res:
            raw_data = json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"[{index}] ❌ ไม่สามารถดึง {handle}: {e}")
        return None

    product = raw_data.get("product", {})
    if not product:
        return None

    title = product.get("title", "")
    body_html = product.get("body_html", "")
    body_text = clean_html(body_html)
    accessories, battery_health, warranty = parse_accessories_and_battery(body_text)

    # 1. รวบรวม Options
    options = [o.get("name") for o in product.get("options", [])]

    # 2. รวบรวม Variants (สี, ความจุ, เกรด, ราคา)
    variants_data = []
    prices = []
    for v in product.get("variants", []):
        opt1 = v.get("option1")  # มักจะเป็น สี (Color)
        opt2 = v.get("option2")  # มักจะเป็น ความจุ (Storage)
        opt3 = v.get("option3")  # มักจะเป็น เกรด (Grade)
        
        price = float(v.get("price", 0))
        compare_price = float(v.get("compare_at_price", 0)) if v.get("compare_at_price") else None
        prices.append(price)

        variants_data.append({
            "variant_id": v.get("id"),
            "title": v.get("title"),
            "color": opt1,
            "storage": opt2,
            "grade": opt3,
            "price_thb": int(price),
            "original_price_thb": int(compare_price) if compare_price else None,
            "available": v.get("available", True),
            "sku": v.get("sku")
        })

    min_price = min(prices) if prices else 0
    max_price = max(prices) if prices else 0
    price_range = f"{int(min_price):,} - {int(max_price):,} บาท" if min_price != max_price else f"{int(min_price):,} บาท"

    # 3. รวบรวมและดาวน์โหลดรูปภาพ
    images_raw = product.get("images", [])
    image_urls = [img.get("src") for img in images_raw if img.get("src")]

    product_img_folder = COMPASIA_IMAGES_DIR / handle
    product_img_folder.mkdir(parents=True, exist_ok=True)

    local_images = []
    for img_idx, img_url in enumerate(image_urls, start=1):
        ext = ".png" if ".png" in img_url.lower() else ".jpg"
        img_dest = product_img_folder / f"img_{img_idx}{ext}"
        
        try:
            img_req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(img_req, timeout=10) as img_res:
                with open(img_dest, "wb") as f:
                    f.write(img_res.read())
            local_images.append(str(img_dest.relative_to(BASE_DIR)))
        except Exception:
            pass

    return {
        "index": index,
        "product_id": product.get("id"),
        "title": title,
        "handle": handle,
        "vendor": product.get("vendor", "Apple"),
        "product_type": product.get("product_type", "Smartphone"),
        "price_range": price_range,
        "min_price": int(min_price),
        "max_price": int(max_price),
        "options": options,
        "variants_count": len(variants_data),
        "variants": variants_data,
        "accessories": accessories,
        "battery_health": battery_health,
        "warranty": warranty,
        "images_count": len(local_images),
        "local_images": local_images,
        "image_urls": image_urls,
        "url": clean_url,
        "description": body_text
    }

def run_compasia_extractor(max_workers: int = 6):
    links_file = DATA_DIR / "links" / "compasia_product_links.txt"
    if not links_file.exists():
        print(f"❌ ไม่พบไฟล์ {links_file}")
        return

    with open(links_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    total = len(urls)
    print("=" * 70)
    print(f"🚀 กำลังดึงข้อมูลสินค้า CompAsia ทั้งหมด {total} รายการ...")
    print(f"📁 โฟลเดอร์เก็บข้อมูล: {COMPASIA_DIR}")
    print(f"🖼️  โฟลเดอร์เก็บรูปภาพ: {COMPASIA_IMAGES_DIR}")
    print("=" * 70)

    products = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_product_details, i, url): i for i, url in enumerate(urls, start=1)}
        for future in as_completed(futures):
            res = future.result()
            if res:
                products.append(res)
            completed += 1
            if res:
                print(f"[{completed}/{total}] ✅ {res['title']} ({res['price_range']}) | {res['variants_count']} ตัวเลือก | {res['images_count']} รูป")

    products.sort(key=lambda x: x["index"])

    # 1. บันทึก JSON รวมทั้งหมด
    json_path = COMPASIA_DIR / "compasia_all_products.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    # 2. บันทึก CSV สรุปสินค้าหลัก (Master Table)
    master_csv = EXPORTS_DIR / "compasia_products_summary.csv"
    with open(master_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "vendor", "price_range", "variants_count", "accessories", "battery_health", "warranty", "url", "image_path"])
        for p in products:
            img = p["local_images"][0] if p["local_images"] else ""
            writer.writerow([
                p["index"],
                p["title"],
                p["vendor"],
                p["price_range"],
                p["variants_count"],
                p["accessories"],
                p["battery_health"],
                p["warranty"],
                p["url"],
                img
            ])

    # 3. บันทึก CSV ละเอียดระดับตัวเลือก (ทุกสี x ความจุ x เกรด x ราคา)
    variants_csv = EXPORTS_DIR / "compasia_variants_detailed.csv"
    with open(variants_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["product_id", "product_title", "color", "storage", "grade", "price_thb", "original_price_thb", "accessories", "warranty", "url"])
        for p in products:
            for v in p["variants"]:
                writer.writerow([
                    p["index"],
                    p["title"],
                    v.get("color") or "-",
                    v.get("storage") or "-",
                    v.get("grade") or "-",
                    v.get("price_thb"),
                    v.get("original_price_thb") or "-",
                    p["accessories"],
                    p["warranty"],
                    p["url"]
                ])

    total_variants = sum(p["variants_count"] for p in products)
    total_images = sum(p["images_count"] for p in products)

    print("\n" + "=" * 70)
    print("🎉 ดึงข้อมูล CompAsia เสร็จสมบูรณ์ 100%!")
    print(f"📦 สินค้าหลักทั้งหมด:           {len(products)} รายการ")
    print(f"🏷️  ตัวเลือก (สี x ความจุ x เกรด): {total_variants} ตัวเลือก")
    print(f"📸 รูปภาพที่ดาวน์โหลดลงเครื่อง:    {total_images} รูป")
    print(f"📄 JSON รวม:                   {json_path}")
    print(f"📊 CSV สรุปสินค้า:              {master_csv}")
    print(f"📊 CSV ละเอียดทุกตัวเลือก/ราคา:   {variants_csv}")
    print("=" * 70)

if __name__ == "__main__":
    run_compasia_extractor(max_workers=6)
