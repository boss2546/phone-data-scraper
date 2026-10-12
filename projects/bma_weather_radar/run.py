#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.radar_scraper import BMAWeatherRadarScraper
from config.settings import WEATHER_DIR

def print_banner():
    print("=" * 70)
    print("🌧️ BMA Weather Radar — เรดาร์ตรวจจับกลุ่มฝน กทม. แบบ Real-time")
    print("   ศูนย์ข้อมูลเรดาร์หนองแขม (NK) และหนองจอก (NC) สำนักการระบายน้ำ กทม.")
    print("=" * 70)

def run_fetch():
    print("\n⏳ กำลังดึงข้อมูลรายงานและภาพเรดาร์ล่าสุด...")
    data = BMAWeatherRadarScraper.fetch_latest_radar()
    print("\n📡 ผลการตรวจวัดล่าสุด:")
    print(f"🕒 เวลาอัปเดต:  {data['last_updated_iso']}")
    print(f"📊 สถานะฝน:     {'🟢 ปลอดโปร่ง (ไม่พบกลุ่มฝน)' if data['status'] == 'clear' else '🌧️ ตรวจพบกลุ่มฝน'}")
    print(f"📝 รายงาน กทม.:  {data['bulletin_raw']}")
    print(f"🖼️ ภาพเรดาร์:    บันทึกไว้ใน data/weather/")
    print(f"🔗 ลิงก์ต้นทาง:  {data['source_url']}\n")

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] ดึงข้อมูลสภาพฝนและภาพเรดาร์ กทม. ล่าสุด")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 70)

        choice = input("👉 เลือกเมนู (0-1): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม BMA Weather Radar")
            break
        elif choice == "1":
            run_fetch()
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_fetch()
    else:
        interactive_menu()
