#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import csv
import urllib.request
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.advice_scraper import AdviceScraper
from config.settings import DATA_DIR, JSON_DIR, EXPORTS_DIR, IMAGES_DIR, DEFAULT_HEADERS

def print_banner():
    print("=" * 68)
    print("💻 Advice IT Products Scraper & Media Pipeline")
    print("   ดึงสเปกสินค้าไอที, ราคา, สต็อก, Schema JSON-LD และภาพ HD จาก Advice.co.th")
    print("=" * 68)

def download_images(images, sku):
    if not images or not sku:
        return []
    sku_dir = IMAGES_DIR / sku
    sku_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for idx, img_url in enumerate(images, 1):
        ext = img_url.split("?")[0].split(".")[-1]
        dest = sku_dir / f"{sku}_{idx}.{ext}"
        if not dest.exists():
            try:
                req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=10) as res:
                    with open(dest, "wb") as f:
                        f.write(res.read())
                downloaded.append(dest)
            except Exception:
                pass
        else:
            downloaded.append(dest)
    return downloaded

def scrape_product(url: str, download_photos: bool = True):
    print(f"\n🚀 กำลังดึงข้อมูลสินค้าจาก Advice: {url}")
    scraper = AdviceScraper()
    result = scraper.fetch_product(url)

    if result.get("status") != "success":
        print(f"❌ เกิดข้อผิดพลาด: {result.get('message')}")
        return

    data = result["data"]
    sku = data.get("sku") or "unknown_sku"
    print("\n✅ ดึงข้อมูลสินค้าสำเร็จ!")
    print(f"📦 ชื่อสินค้า: {data.get('name')}")
    print(f"🏷️  SKU:      {sku}")
    print(f"🏢 แบรนด์:    {data.get('brand')}")
    print(f"💰 ราคา:      {data.get('price'):,} {data.get('currency')}" if data.get('price') else "💰 ราคา:      -")
    print(f"📊 สถานะ:     {'มีสินค้า (In Stock)' if data.get('in_stock') else 'สินค้าหมด (Out of Stock)'}")
    print(f"⚡ สเปกย่อ:   {data.get('key_specs') or '-'}")

    # 1. บันทึก JSON
    json_path = JSON_DIR / f"{sku}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 2. บันทึก/อัปเดต CSV
    csv_path = EXPORTS_DIR / "advice_products_summary.csv"
    file_exists = csv_path.exists()
    with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
        fieldnames = ["sku", "name", "brand", "price", "currency", "in_stock", "key_specs", "url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "sku": data.get("sku"),
            "name": data.get("name"),
            "brand": data.get("brand"),
            "price": data.get("price"),
            "currency": data.get("currency"),
            "in_stock": data.get("in_stock"),
            "key_specs": data.get("key_specs"),
            "url": data.get("url")
        })

    # 3. ดาวน์โหลดรูปภาพ
    downloaded_imgs = []
    if download_photos and data.get("images"):
        downloaded_imgs = download_images(data["images"], sku)

    print("\n📁 บันทึกข้อมูลสำเร็จ:")
    print(f"   📄 JSON: {json_path}")
    print(f"   📊 CSV:  {csv_path}")
    if downloaded_imgs:
        print(f"   📸 รูปภาพ HD: {len(downloaded_imgs)} ภาพ ใน data/images/{sku}/")

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] ดึงข้อมูลสินค้าโดยระบุ URL Advice")
        print("  [2] ตัวอย่างสินค้าทดสอบ (iPhone 16 Pro Max บน Advice)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 68)

        choice = input("👉 เลือกเมนู (0-2): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม Advice Scraper")
            break
        elif choice == "1":
            url = input("🔗 ใส่ URL หน้าสินค้า Advice: ").strip()
            if url:
                scrape_product(url)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "2":
            sample_url = "https://www.advice.co.th/product/smart-phone/smart-phone-apple/iphone-16-pro-max-256gb-black-titanium-"
            scrape_product(sample_url)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py                 # เปิดเมนู Interactive")
            print("  python3 run.py <Advice_URL>    # ดึงข้อมูลจาก URL ทันที")
        elif arg.startswith("http://") or arg.startswith("https://"):
            scrape_product(sys.argv[1])
        else:
            print("⚠️ กรุณาระบุ URL หน้าสินค้า Advice ให้ถูกต้อง")
    else:
        interactive_menu()
