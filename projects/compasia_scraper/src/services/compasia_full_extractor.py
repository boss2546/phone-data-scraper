import sys
import json
import csv
import re
import urllib.request
import urllib.parse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

# Ensure project base is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR, COMPASIA_DIR, IMAGES_DIR, EXPORTS_DIR, LINKS_DIR, DEFAULT_HEADERS

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
    battery_health = "80-100%"
    warranty = "รับประกันสินค้า 1 เดือน"

    lines = body_text.split('\n')
    for line in lines:
        if "สุขภาพแบตเตอรี่" in line or "แบตเตอรี่" in line:
            m = re.search(r'(\d+[\s\-\%to]+\d+%)', line)
            if m:
                battery_health = m.group(1).replace(" ", "")
        if "รับประกัน" in line:
            m = re.search(r'(รับประกัน[^\.\n]+)', line)
            if m:
                warranty = m.group(1).strip()

    return battery_health, warranty

def download_image(img_url: str, dest_path: Path):
    if dest_path.exists():
        return True
    try:
        req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=10) as res:
            with open(dest_path, "wb") as f:
                f.write(res.read())
        return True
    except Exception:
        return False

def run_compasia_extractor(max_workers: int = 5, download_photos: bool = True):
    json_path = LINKS_DIR / "compasia_products_links.json"
    if not json_path.exists():
        legacy_path = BASE_DIR.parent.parent / "_archive_legacy" / "data" / "links" / "compasia_products_links.json"
        if legacy_path.exists():
            json_path = legacy_path

    if not json_path.exists():
        print(f"❌ ไม่พบไฟล์ {json_path}")
        print("💡 กรุณารัน fetch_compasia_links() ก่อน")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        products = json.load(f)

    print("=" * 64)
    print(f"🛍️ เริ่มการสกัดข้อมูลเชิงลึก CompAsia: {len(products)} รายการ")
    print("=" * 64)

    all_detailed_products = []
    all_variants_rows = []

    for idx, prod in enumerate(products, 1):
        handle = prod.get("handle")
        title = prod.get("title")
        body_html = prod.get("body_html", "")
        cleaned_body = clean_html(body_html)
        battery_health, warranty = parse_accessories_and_battery(cleaned_body)

        images = [img.get("src") for img in prod.get("images", []) if img.get("src")]
        variants = prod.get("variants", [])

        print(f"[{idx}/{len(products)}] สกัด {title} ({len(variants)} ตัวเลือก, {len(images)} ภาพ)")

        # Download images
        local_images = []
        if download_photos and images:
            prod_img_dir = IMAGES_DIR / handle
            prod_img_dir.mkdir(parents=True, exist_ok=True)
            for i_idx, img_url in enumerate(images, 1):
                ext = img_url.split("?")[0].split(".")[-1]
                ext = ext if ext in ["jpg", "jpeg", "png", "webp"] else "jpg"
                dest_file = prod_img_dir / f"img_{i_idx}.{ext}"
                download_image(img_url, dest_file)
                local_images.append(str(dest_file.relative_to(BASE_DIR)))

        detailed_prod = {
            "id": prod.get("id"),
            "handle": handle,
            "title": title,
            "product_type": prod.get("product_type"),
            "vendor": prod.get("vendor"),
            "url": f"https://compasia.co.th/products/{handle}",
            "battery_health": battery_health,
            "warranty": warranty,
            "variants_count": len(variants),
            "images_count": len(images),
            "images": images,
            "local_images": local_images,
            "description": cleaned_body[:300]
        }
        all_detailed_products.append(detailed_prod)

        for v in variants:
            all_variants_rows.append({
                "product_id": prod.get("id"),
                "product_title": title,
                "variant_id": v.get("id"),
                "variant_title": v.get("title"),
                "price": float(v.get("price", 0)),
                "compare_at_price": float(v.get("compare_at_price") or 0) if v.get("compare_at_price") else "-",
                "sku": v.get("sku"),
                "available": v.get("available"),
                "battery_health": battery_health,
                "url": f"https://compasia.co.th/products/{handle}?variant={v.get('id')}"
            })

    # Save to JSON
    out_json = COMPASIA_DIR / "compasia_all_products.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_detailed_products, f, ensure_ascii=False, indent=2)

    # Save to CSV
    out_csv = EXPORTS_DIR / "compasia_variants_detailed.csv"
    if all_variants_rows:
        with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_variants_rows[0].keys()))
            writer.writeheader()
            writer.writerows(all_variants_rows)

    print("\n🎉 สกัดข้อมูลเชิงลึก CompAsia สำเร็จสมบูรณ์!")
    print(f"📦 รวมสินค้า: {len(all_detailed_products)} รุ่น | ตัวเลือกทั้งหมด: {len(all_variants_rows)} รายการ")
    print(f"📄 บันทึก JSON: {out_json}")
    print(f"📊 บันทึก CSV:  {out_csv}")
