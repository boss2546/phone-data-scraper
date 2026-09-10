#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add apple_scraper root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.apple_scraper import AppleScraper
from src.scrapers.tech_specs_scraper import TechSpecsScraper
from src.services.storage import AppleStorageService
from config.settings import DEFAULT_LOCALE, BASE_APPLE_URL

POPULAR_MODELS = {
    "1": ("iPhone 16 Pro", "iphone-16-pro"),
    "2": ("iPhone 16", "iphone-16"),
    "3": ("iPad Pro (M4)", "ipad-pro"),
    "4": ("MacBook Pro (M3/M4)", "macbook-pro"),
    "5": ("Apple Watch Ultra 2", "apple-watch-ultra-2")
}

def print_banner():
    print("=" * 72)
    print("🍎 Apple Scraper — เครื่องมือดึงข้อมูลสินค้าทางการ สเปก & ราคาจาก Apple")
    print(f"   ฐานข้อมูลเป้าหมาย: Apple Store Thailand ({BASE_APPLE_URL}/{DEFAULT_LOCALE})")
    print("=" * 72)

def run_scrape(url_or_path: str, download_images: bool = True):
    print(f"\n🚀 กำลังดึงข้อมูลจาก Apple: {url_or_path}")
    scraper = AppleScraper(locale=DEFAULT_LOCALE)
    specs_scraper = TechSpecsScraper(locale=DEFAULT_LOCALE)

    # 1. ดึงภาพรวมและราคา
    overview = scraper.scrape_product(url_or_path)
    if overview.get("status") != "success":
        print(f"❌ เกิดข้อผิดพลาด: {overview.get('message')}")
        return

    title = overview.get("title", "Apple Product")
    slug = overview.get("slug", "product")
    print(f"✅ ดึงข้อมูลภาพรวมสำเร็จ: {title}")

    # 2. ตรวจสอบหน้า Tech Specs เพื่อดึงสเปกละเอียด
    specs_url = overview.get("specs_url") or f"{overview['url'].rstrip('/')}/specs/"
    print(f"⏳ กำลังตรวจสอบสเปกทางเทคนิค (Tech Specs)...")
    specs_data = specs_scraper.scrape_specs(specs_url)
    
    if specs_data.get("status") == "success":
        overview["specs"] = specs_data.get("specs", {})
        overview["capacities"] = specs_data.get("capacities", [])
        overview["colors"] = specs_data.get("colors", [])
        print(f"   ↳ สกัดสเปกชิป: {overview['specs'].get('chip')[:60]}...")
    else:
        overview["specs"] = {}

    # 3. บันทึกข้อมูล JSON & CSV
    json_path = AppleStorageService.save_product_json(overview, f"{slug}.json")
    csv_path = AppleStorageService.export_summary_csv([overview], "apple_products_summary.csv")
    print(f"💾 บันทึก JSON สำเร็จ: {json_path}")
    print(f"📊 อัปเดต CSV สรุป:  {csv_path}")

    # 4. ดาวน์โหลดภาพสินค้า
    if download_images and overview.get("images"):
        print(f"📸 กำลังดาวน์โหลดรูปภาพทางการ {len(overview['images'][:4])} รูป...")
        downloaded = AppleStorageService.download_images(overview["images"], slug, max_images=4)
        print(f"   ↳ ดาวน์โหลดภาพสำเร็จ: {len(downloaded)} รูป ใน data/images/{slug}/")

    # 5. สรุปผลลัพธ์
    print("\n" + "-" * 72)
    print(f"🏷️  สินค้า:        {title}")
    print(f"💰 ราคาเริ่มต้น:   {overview.get('starting_price_thb'):,} บาท" if overview.get('starting_price_thb') else "💰 ราคา:         ตรวจสอบใน Store")
    print(f"⚡ ชิปประมวลผล:   {overview.get('specs', {}).get('chip', '-')}")
    print(f"💾 ความจุ:        {', '.join(overview.get('capacities', [])) if overview.get('capacities') else '-'}")
    print(f"🎨 ตัวเลือกสี:     {', '.join(overview.get('colors', [])) if overview.get('colors') else '-'}")
    print(f"🔗 ลิงก์ต้นทาง:    {overview.get('url')}")
    print("-" * 72 + "\n")

def interactive_menu():
    while True:
        print_banner()
        print("เลือกเมนูการดึงข้อมูล:")
        for k, (name, path) in POPULAR_MODELS.items():
            print(f"  [{k}] ดึงข้อมูล {name}")
        print("  [6] ระบุ URL ของ Apple เอง (Custom Apple URL)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 72)

        choice = input("👉 เลือกเมนู (0-6): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม ขอบคุณครับ!")
            break
        elif choice in POPULAR_MODELS:
            _, path = POPULAR_MODELS[choice]
            run_scrape(path)
            input("กด Enter เพื่อกลับสู่เมนู...")
        elif choice == "6":
            custom_url = input("🔗 ใส่ URL หน้าเว็บ Apple: ").strip()
            if custom_url:
                run_scrape(custom_url)
            input("กด Enter เพื่อกลับสู่เมนู...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py                                # เปิด Interactive Menu")
            print("  python3 run.py <URL หรือ Product Slug>         # ดึงข้อมูลสินค้าระบุ URL")
            print("ตัวอย่าง:")
            print("  python3 run.py iphone-16-pro")
            print("  python3 run.py https://www.apple.com/th/macbook-pro/")
        else:
            run_scrape(arg)
    else:
        interactive_menu()
