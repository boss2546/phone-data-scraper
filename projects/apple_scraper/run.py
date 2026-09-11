#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# Add apple_scraper root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.apple_scraper import AppleScraper
from src.scrapers.tech_specs_scraper import TechSpecsScraper
from src.scrapers.catalog_crawler import AppleCatalogCrawler
from src.services.storage import AppleStorageService
from src.services.database_builder import AppleDatabaseBuilder
from src.services.media_downloader import AppleMediaDownloader
from src.services.bg_remover import AppleBackgroundRemover
from src.services.deep_asset_crawler import AppleDeepAssetCrawler
from config.settings import DEFAULT_LOCALE, BASE_APPLE_URL

POPULAR_MODELS = {
    "1": ("iPhone 16", "iphone-16"),
    "2": ("iPhone 15", "iphone-15"),
    "3": ("iPad Pro (M4)", "ipad-pro"),
    "4": ("iPad Air (M2)", "ipad-air"),
    "5": ("MacBook Air", "macbook-air"),
    "6": ("MacBook Pro", "macbook-pro")
}

def print_banner():
    print("=" * 74)
    print("🍎 Apple Scraper & Database Builder — ระบบดึงข้อมูลทางการ Apple ครบวงจร")
    print(f"   ฐานข้อมูลเป้าหมาย: Apple Store Thailand ({BASE_APPLE_URL}/{DEFAULT_LOCALE})")
    print("=" * 74)

def run_scrape_single(url_or_path: str, download_images: bool = True):
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
    print("\n" + "-" * 74)
    print(f"🏷️  สินค้า:        {title}")
    print(f"💰 ราคาเริ่มต้น:   {overview.get('starting_price_thb'):,} บาท" if overview.get('starting_price_thb') else "💰 ราคา:         ตรวจสอบใน Store")
    print(f"⚡ ชิปประมวลผล:   {overview.get('specs', {}).get('chip', '-')}")
    print(f"💾 ความจุ:        {', '.join(overview.get('capacities', [])) if overview.get('capacities') else '-'}")
    print(f"🎨 ตัวเลือกสี:     {', '.join(overview.get('colors', [])) if overview.get('colors') else '-'}")
    print(f"🔗 ลิงก์ต้นทาง:    {overview.get('url')}")
    print("-" * 74 + "\n")

def run_build_full_database():
    """ดึงข้อมูลสินค้าทั้งหมดทุกหมวดหมู่ ทุกรุ่น ทุกสี ทุกราคา และสร้างฐานข้อมูล 3 รูปแบบ"""
    crawler = AppleCatalogCrawler()
    db_builder = AppleDatabaseBuilder()
    media_downloader = AppleMediaDownloader()

    # 1. Crawl all products
    variants = crawler.crawl_all()
    if not variants:
        print("❌ ไม่พบข้อมูลสินค้า กรุณาตรวจสอบการเชื่อมต่ออินเทอร์เน็ต")
        return

    # 2. Attach local paths
    media_downloader.attach_local_paths(variants)

    # 3. Build Databases
    print("\n📦 กำลังสร้างฐานข้อมูลมาตรฐานระดับโปรดักชัน (SQLite, JSON Tree, SQL Dump, CSV, JS SDK)...")
    json_path = db_builder.build_full_json_export(variants, "apple_full_catalog.json")
    tree_path = db_builder.build_catalog_tree_json(variants, "apple_catalog_tree.json")
    js_path = db_builder.build_js_bundle(variants, "apple_catalog.js")
    csv_path = db_builder.build_csv_database(variants, "apple_all_variants.csv")
    db_path = db_builder.build_sqlite_database(variants, "apple_catalog.db")
    sql_path = db_builder.build_sql_dump(variants, "apple_catalog.sql")
    db_builder.build_client_helpers()

    # 4. Download 4K Retina & Multi-angle images
    print("\n📸 กำลังดาวน์โหลดรูปภาพสินค้า 4K Retina ทุกสีและทุกมุมมอง...")
    media_downloader.download_all_images(variants, download_galleries=True, download_png=False)

    # 5. Summary
    print("\n" + "=" * 74)
    print("🎉 สร้างฐานข้อมูลสินค้า Apple สำเร็จสมบูรณ์ 100%!")
    print(f"📦 จำนวนตัวเลือกสินค้าทั้งหมด:     {len(variants)} รายการ (ตรวจสอบความถูกต้องเรียบร้อย)")
    print(f"🗄️ 1. SQLite Relational DB:         {db_path}")
    print(f"       ↳ ตาราง: categories, products, colors, variants")
    print(f"       ↳ มุมมอง: v_catalog (Join ทุกฟิลด์), v_product_summary")
    print(f"📜 2. SQL Dump File:                {sql_path} (สำหรับ MySQL / Postgres / Supabase)")
    print(f"📄 3. JSON Master Catalog:          {json_path}")
    print(f"🌳 4. E-Commerce Tree JSON:         {tree_path} (สำหรับตัวเลือกสินค้าหน้าเว็บ)")
    print(f"⚡ 5. JavaScript Web Bundle:        {js_path} (window.APPLE_DATABASE)")
    print(f"🛠️  6. Frontend/Backend SDKs:        apple_db_helper.js และ apple_db_helper.py")
    print(f"📊 7. Master CSV (Excel):           {csv_path}")
    print(f"🌐 8. Web Preview Catalog:          {BASE_DIR / 'catalog_preview.html'}")
    print("=" * 74 + "\n")

def run_remove_background():
    remover = AppleBackgroundRemover()
    remover.process_all_images(max_workers=8)
    remover.generate_transparent_catalog_exports()

def run_deep_assets():
    crawler = AppleDeepAssetCrawler()
    crawler.crawl_all_deep_products()
    crawler.download_curated_local_images(max_per_product=5, max_workers=8)

def interactive_menu():
    while True:
        print_banner()
        print("เลือกเมนูการทำงาน:")
        print("  [7] 🗄️ ดึงข้อมูลทุกรุ่น ทุกสี ทุกราคา & สร้างฐานข้อมูลเต็มรูปแบบ (Build Database)")
        print("  [6] 🔍 เจาะลึกรูปภาพทุกสินค้า แยก 6 หมวดหมู่ (Deep Product Media Gallery)")
        print("  [9] 🎨 ลบพื้นหลังภาพสินค้าทั้งหมดเป็น Transparent PNG (No-BG)")
        print("  --------------------------------------------------------------------------")
        for k, (name, path) in POPULAR_MODELS.items():
            print(f"  [{k}] ดึงข้อมูลเฉพาะรุ่น {name}")
        print("  [8] ระบุ URL ของ Apple เอง (Custom Apple URL)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 74)

        choice = input("👉 เลือกเมนู (0-9): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม ขอบคุณครับ!")
            break
        elif choice == "7":
            run_build_full_database()
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "6":
            run_deep_assets()
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "9":
            run_remove_background()
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice in POPULAR_MODELS:
            _, path = POPULAR_MODELS[choice]
            run_scrape_single(path)
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "8":
            custom_url = input("🔗 ใส่ URL หน้าเว็บ Apple: ").strip()
            if custom_url:
                run_scrape_single(custom_url)
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py                                # เปิด Interactive Menu")
            print("  python3 run.py build-db                       # สร้างฐานข้อมูลทุกรุ่น ทุกสี ทุกราคา")
            print("  python3 run.py deep-assets                    # เจาะลึกรูปภาพ 4K ครบทุกหมวดหมู่")
            print("  python3 run.py remove-bg                      # ลบพื้นหลังสินค้าทั้งหมดเป็น Transparent PNG")
            print("  python3 run.py <URL หรือ Product Slug>         # ดึงข้อมูลเฉพาะรุ่น")
            print("ตัวอย่าง:")
            print("  python3 run.py build-db")
            print("  python3 run.py deep-assets")
            print("  python3 run.py remove-bg")
            print("  python3 run.py iphone-16")
        elif arg in ["build-db", "build_db", "database", "all"]:
            run_build_full_database()
        elif arg in ["deep-assets", "deep_assets", "gallery", "deep"]:
            run_deep_assets()
        elif arg in ["remove-bg", "remove_bg", "nobg", "transparent"]:
            run_remove_background()
        else:
            run_scrape_single(sys.argv[1])
    else:
        interactive_menu()
