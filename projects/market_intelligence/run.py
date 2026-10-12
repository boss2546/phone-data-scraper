#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.services.market_analyzer import MarketIntelligenceAnalyzer
from config.settings import EXPORTS_DIR

def print_banner():
    print("=" * 70)
    print("📊 Market Intelligence & Deal Hunter — วิเคราะห์ราคากลางสินค้าไอที")
    print("   เปรียบเทียบราคาทางการ (Apple Store) vs ราคามือสอง (CompAsia / Facebook)")
    print("=" * 70)

def run_analysis():
    print("\n⏳ กำลังรวบรวมข้อมูลราคากลางจากทุกฐานข้อมูล...")
    res = MarketIntelligenceAnalyzer.analyze_price_disparity()
    print("\n📈 ผลการวิเคราะห์ภาพรวมตลาด:")
    print(f"🍎 สินค้าทางการ Apple ที่ตรวจสอบ:  {res['apple_models_analyzed']} รายการ")
    print(f"🛍️ สินค้ามือสอง CompAsia ที่พร้อมเทียบ: {res['compasia_products_available']} รายการ")
    print(f"📄 บันทึกไฟล์รายงานราคากลาง:         {res['report_file']}\n")

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] รันวิเคราะห์เปรียบเทียบราคากลาง (Apple vs CompAsia)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 70)

        choice = input("👉 เลือกเมนู (0-1): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม Market Intelligence")
            break
        elif choice == "1":
            run_analysis()
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_analysis()
    else:
        interactive_menu()
