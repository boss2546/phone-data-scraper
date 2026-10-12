#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.facebook_scraper import FacebookScraper
from config.settings import DATA_DIR, JSON_DIR, EXPORTS_DIR

def print_banner():
    print("=" * 70)
    print("📘 Facebook Scraper & Intelligence Suite")
    print("   ระบบดึงโพสต์กลุ่ม/เพจ, สกัดสเปกโทรศัพท์มือสอง, ราคา และส่งออก CSV/JSON")
    print("=" * 70)

def run_parse(file_path: Path = None):
    target = file_path or (JSON_DIR / "facebook_group_posts.json")
    if not target.exists():
        legacy_path = BASE_DIR.parent.parent / "_archive_legacy" / "data" / "facebook" / "facebook_group_posts.json"
        if legacy_path.exists():
            target = legacy_path

    if not target.exists():
        print(f"❌ ไม่พบไฟล์เป้าหมาย: {target}")
        print("💡 กรุณาวางไฟล์ JSON ใน data/json/facebook_group_posts.json หรือรัน Playwright เพื่อดึงใหม่")
        return

    print(f"\n⏳ กำลังประมวลผลข้อมูลจาก: {target.name}...")
    result = FacebookScraper.parse_facebook_json(target)
    if result.get("status") == "success":
        print(f"🎉 ประมวลผลสำเร็จ!")
        print(f"📦 จำนวนโพสต์ที่พบ: {result['total_posts']} โพสต์")
        print(f"📄 บันทึก JSON สะอาด: {result['output_json']}")
        print(f"📊 ส่งออก CSV:      {result['output_csv']}")
    else:
        print(f"❌ เกิดข้อผิดพลาด: {result.get('message')}")

def run_crawler(url: str, scrolls: int = 10):
    print(f"\n🚀 กำลังเปิด Browser เพื่อดึงข้อมูลจาก: {url}")
    print(f"📜 จำนวนรอบการเลื่อนหน้า: {scrolls} รอบ")
    asyncio.run(FacebookScraper.scrape_with_playwright(url, scrolls=scrolls))

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] ประมวลผลและคลีนโพสต์จากไฟล์ JSON (facebook_group_posts.json -> CSV/JSON)")
        print("  [2] เปิด Playwright ดึงข้อมูลกลุ่มสดจาก URL Facebook")
        print("  [3] ระบุไฟล์ JSON เองที่ต้องการคลีน")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 70)

        choice = input("👉 เลือกเมนู (0-3): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม Facebook Scraper")
            break
        elif choice == "1":
            run_parse()
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "2":
            url = input("🔗 ใส่ URL กลุ่มหรือหน้า Facebook: ").strip()
            if url:
                s_count = input("📜 จำนวนรอบที่ต้องการเลื่อน (ค่าเริ่มต้น 10): ").strip()
                scrolls = int(s_count) if s_count.isdigit() else 10
                run_crawler(url, scrolls)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "3":
            path_str = input("📄 ใส่ Path ของไฟล์ JSON: ").strip()
            if path_str:
                run_parse(Path(path_str))
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py                  # เปิดเมนู Interactive")
            print("  python3 run.py parse            # คลีนข้อมูลจาก JSON เป็น CSV")
            print("  python3 run.py <Facebook_URL>   # รัน Playwright ดึงจาก URL")
        elif arg == "parse":
            run_parse()
        elif arg.startswith("http://") or arg.startswith("https://"):
            run_crawler(sys.argv[1])
        else:
            run_parse(Path(sys.argv[1]))
    else:
        interactive_menu()
