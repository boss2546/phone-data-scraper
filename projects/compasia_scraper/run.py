#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.compasia_scraper import fetch_compasia_links
from src.services.compasia_full_extractor import run_compasia_extractor
from config.settings import DATA_DIR, COMPASIA_DIR, EXPORTS_DIR

def print_banner():
    print("=" * 68)
    print("🛍️ CompAsia Scraper & Data Pipeline")
    print("   ดึงสินค้าโทรศัพท์มือสอง, สเปก, สุขภาพแบตเตอรี่, ราคา และรูปภาพจาก CompAsia")
    print("=" * 68)

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] ดึงลิงก์สินค้าทั้งหมดจาก Shopify API (หน้า 1-3)")
        print("  [2] สกัดข้อมูลเชิงลึกทั้งหมด + แยกตัวเลือกสินค้า + ดาวน์โหลดรูปภาพ")
        print("  [3] ดึงข้อมูลครบวงจร (ดึงลิงก์ใหม่ -> สกัดเชิงลึกทันที)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 68)

        choice = input("👉 เลือกเมนู (0-3): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม CompAsia Scraper")
            break
        elif choice == "1":
            fetch_compasia_links(pages=[1, 2, 3])
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "2":
            run_compasia_extractor(download_photos=True)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "3":
            fetch_compasia_links(pages=[1, 2, 3])
            run_compasia_extractor(download_photos=True)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py            # เปิดเมนู Interactive")
            print("  python3 run.py links      # ดึงเฉพาะรายการลิงก์สินค้า")
            print("  python3 run.py extract    # สกัดข้อมูลละเอียดและรูปภาพ")
            print("  python3 run.py all        # ดึงครบทั้งระบบอัตโนมัติ")
        elif arg in ["links", "fetch"]:
            fetch_compasia_links()
        elif arg in ["extract", "full"]:
            run_compasia_extractor()
        elif arg in ["all", "run"]:
            fetch_compasia_links()
            run_compasia_extractor()
        else:
            print(f"❌ ไม่รู้จักคำสั่ง '{arg}'")
    else:
        interactive_menu()
