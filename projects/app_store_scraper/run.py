#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 App Store & Google Play Store Scraper CLI
ระบบดึงโลโก้และภาพหน้าจอตัวอย่าง (Preview Screenshots) ของ 35 แอปพลิเคชันยอดนิยม
"""
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGOS_SCRIPT = BASE_DIR / "download_app_logos.py"
SCREENSHOTS_SCRIPT = BASE_DIR / "download_playstore_screenshots.py"
LOGOS_HTML = BASE_DIR / "app_logos_preview.html"
SCREENSHOTS_HTML = BASE_DIR / "app_screenshots_studio.html"


def print_banner():
    print("=" * 72)
    print("📱 App Store & Play Store Media Scraper (35 Popular Apps Suite)")
    print("   ระบบดึงโลโก้ความละเอียดสูง & ภาพตัวอย่างหน้าจอแอป พร้อม Web Studio")
    print("=" * 72)


def print_status():
    logos_dir = BASE_DIR / "data" / "app_logos" / "images"
    screens_dir = BASE_DIR / "data" / "app_screenshots"
    logo_count = len(list(logos_dir.glob("*.*"))) if logos_dir.exists() else 0
    screen_count = sum(1 for f in screens_dir.rglob("screenshot_*.png")) if screens_dir.exists() else 0
    app_folders = sum(1 for d in screens_dir.iterdir() if d.is_dir()) if screens_dir.exists() else 0

    print(f"\n📊 สถานะคลังข้อมูลปัจจุบัน:")
    print(f"   • โลโก้แอปความละเอียดสูง (App Logos):       {logo_count} ไฟล์")
    print(f"   • โฟลเดอร์แอป (App Folders):                {app_folders} แอป")
    print(f"   • ภาพหน้าจอตัวอย่าง (Preview Screenshots):  {screen_count} ภาพ")
    print(f"   • หน้าเว็บพรีวิวโลโก้:                      {LOGOS_HTML.name}")
    print(f"   • หน้าเว็บพรีวิวภาพหน้าจอ (Studio):         {SCREENSHOTS_HTML.name}\n")


def interactive_menu():
    while True:
        print_banner()
        print_status()
        print("เลือกเมนูการทำงาน:")
        print("  [1] 🎨 ดึงโลโก้ความละเอียดสูงทั้ง 35 แอป (Run App Logos Scraper)")
        print("  [2] 📸 ดึงภาพตัวอย่างหน้าจอ Play Store ทั้ง 35 แอป (Run Screenshots Scraper)")
        print("  [3] 🌐 เปิดหน้าเว็บ App Screenshots Studio ในเบราว์เซอร์")
        print("  [4] 🖼️ เปิดหน้าเว็บ App Logos Preview ในเบราว์เซอร์")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 72)

        choice = input("👉 เลือกเมนู (0-4): ").strip()
        if choice == "0":
            print("👋 ออกจากโมดูล App Store Scraper")
            break
        elif choice == "1":
            subprocess.run([sys.executable, str(LOGOS_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "2":
            subprocess.run([sys.executable, str(SCREENSHOTS_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "3":
            webbrowser.open(f"file://{SCREENSHOTS_HTML}")
            print(f"✅ เปิด {SCREENSHOTS_HTML} ในเบราว์เซอร์แล้ว")
        elif choice == "4":
            webbrowser.open(f"file://{LOGOS_HTML}")
            print(f"✅ เปิด {LOGOS_HTML} ในเบราว์เซอร์แล้ว")
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["logos", "logo"]:
            subprocess.run([sys.executable, str(LOGOS_SCRIPT)], cwd=str(BASE_DIR))
        elif cmd in ["screenshots", "screens", "playstore"]:
            subprocess.run([sys.executable, str(SCREENSHOTS_SCRIPT)], cwd=str(BASE_DIR))
        elif cmd in ["status", "info"]:
            print_banner()
            print_status()
        elif cmd in ["open", "studio"]:
            webbrowser.open(f"file://{SCREENSHOTS_HTML}")
        else:
            print("วิธีใช้: python3 run.py [logos | screenshots | status | studio]")
    else:
        interactive_menu()

