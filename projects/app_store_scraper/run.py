#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📱 App Store & Google Play Store Scraper CLI
ระบบดึงโลโก้และภาพหน้าจอตัวอย่าง (Preview Screenshots) ของ 35 แอปพลิเคชันยอดนิยม
รองรับทั้ง Apple App Store (Retina 4K iPhone/iPad) และ Google Play Store
"""
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGOS_SCRIPT = BASE_DIR / "download_app_logos.py"
PLAYSTORE_SCRIPT = BASE_DIR / "download_playstore_screenshots.py"
APPSTORE_SCRIPT = BASE_DIR / "download_appstore_screenshots.py"

LOGOS_HTML = BASE_DIR / "app_logos_preview.html"
PLAYSTORE_HTML = BASE_DIR / "app_screenshots_studio.html"
APPSTORE_HTML = BASE_DIR / "appstore_screenshots_studio.html"


def print_banner():
    print("=" * 76)
    print("📱 Dual App Store & Play Store Media Scraper (35 Popular Apps Suite)")
    print("   ระบบดึงภาพหน้าจอ Retina/4K จาก Apple App Store & Google Play Store")
    print("=" * 76)


def print_status():
    logos_dir = BASE_DIR / "data" / "app_logos" / "images"
    ps_screens_dir = BASE_DIR / "data" / "app_screenshots"
    as_screens_dir = BASE_DIR / "data" / "appstore_screenshots"

    logo_count = len(list(logos_dir.glob("*.*"))) if logos_dir.exists() else 0
    ps_screen_count = sum(1 for f in ps_screens_dir.rglob("screenshot_*.png")) if ps_screens_dir.exists() else 0
    ps_app_folders = sum(1 for d in ps_screens_dir.iterdir() if d.is_dir()) if ps_screens_dir.exists() else 0

    as_screen_count = sum(1 for f in as_screens_dir.rglob("screenshot_*.png")) if as_screens_dir.exists() else 0
    as_app_folders = sum(1 for d in as_screens_dir.iterdir() if d.is_dir()) if as_screens_dir.exists() else 0
    as_iphone = sum(1 for f in as_screens_dir.rglob("iphone/screenshot_*.png")) if as_screens_dir.exists() else 0
    as_ipad = sum(1 for f in as_screens_dir.rglob("ipad/screenshot_*.png")) if as_screens_dir.exists() else 0

    print(f"\n📊 สถานะคลังข้อมูลปัจจุบัน:")
    print(f"   🍎 Apple App Store (Retina 4K):")
    print(f"      • โฟลเดอร์แอป (App Folders):                {as_app_folders} แอป")
    print(f"      • ภาพหน้าจอ iPhone (1290x2796):             {as_iphone} ภาพ")
    print(f"      • ภาพหน้าจอ iPad Pro (2048x2732):           {as_ipad} ภาพ")
    print(f"      • ภาพหน้าจอ Apple รวมทั้งหมด:               {as_screen_count} ภาพ")
    print(f"      • หน้าเว็บ Apple Studio:                    {APPSTORE_HTML.name}")
    print(f"   🤖 Google Play Store (Android):")
    print(f"      • โฟลเดอร์แอป:                              {ps_app_folders} แอป")
    print(f"      • ภาพหน้าจอ Android รวม:                    {ps_screen_count} ภาพ")
    print(f"      • หน้าเว็บ Play Store Studio:               {PLAYSTORE_HTML.name}")
    print(f"   🎨 โลโก้แอปความละเอียดสูง (App Logos):         {logo_count} ไฟล์ ({LOGOS_HTML.name})\n")


def interactive_menu():
    while True:
        print_banner()
        print_status()
        print("เลือกเมนูการทำงาน:")
        print("  [1] 🍎 ดึงภาพหน้าจอ Apple App Store ทั้ง 35 แอป (Retina 4K iPhone/iPad)")
        print("  [2] 🔍 ค้นหาและดึงภาพแอปใดๆ ใน Apple App Store (Search Custom App)")
        print("  [3] 🌟 เปิดหน้าเว็บ Apple App Store Screenshots Studio (Retina Gallery)")
        print("  [4] 🤖 ดึงภาพหน้าจอ Google Play Store ทั้ง 35 แอป (Android)")
        print("  [5] 🌐 เปิดหน้าเว็บ Google Play Store Studio")
        print("  [6] 🎨 ดึงโลโก้ความละเอียดสูงทั้ง 35 แอป (App Logos)")
        print("  [7] 🖼️ เปิดหน้าเว็บ App Logos Preview")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 76)

        choice = input("👉 เลือกเมนู (0-7): ").strip()
        if choice == "0":
            print("👋 ออกจากโมดูล App Store Scraper")
            break
        elif choice == "1":
            subprocess.run([sys.executable, str(APPSTORE_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "2":
            query = input("🔍 ป้อนชื่อแอปที่ต้องการค้นหาใน App Store: ").strip()
            if query:
                subprocess.run([sys.executable, str(APPSTORE_SCRIPT), "search", query], cwd=str(BASE_DIR))
        elif choice == "3":
            if APPSTORE_HTML.exists():
                webbrowser.open(f"file://{APPSTORE_HTML}")
                print(f"✅ เปิด {APPSTORE_HTML} ในเบราว์เซอร์แล้ว")
            else:
                print(f"⚠️ ยังไม่ได้สร้าง {APPSTORE_HTML.name} กรุณารันข้อ [1] ดึงภาพก่อน")
        elif choice == "4":
            subprocess.run([sys.executable, str(PLAYSTORE_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "5":
            if PLAYSTORE_HTML.exists():
                webbrowser.open(f"file://{PLAYSTORE_HTML}")
                print(f"✅ เปิด {PLAYSTORE_HTML} ในเบราว์เซอร์แล้ว")
            else:
                print(f"⚠️ ยังไม่ได้สร้าง {PLAYSTORE_HTML.name}")
        elif choice == "6":
            subprocess.run([sys.executable, str(LOGOS_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "7":
            if LOGOS_HTML.exists():
                webbrowser.open(f"file://{LOGOS_HTML}")
                print(f"✅ เปิด {LOGOS_HTML} ในเบราว์เซอร์แล้ว")
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["appstore", "ios", "apple"]:
            args = [sys.executable, str(APPSTORE_SCRIPT)] + sys.argv[2:]
            subprocess.run(args, cwd=str(BASE_DIR))
        elif cmd in ["search", "find"] and len(sys.argv) > 2:
            args = [sys.executable, str(APPSTORE_SCRIPT), "search", " ".join(sys.argv[2:])]
            subprocess.run(args, cwd=str(BASE_DIR))
        elif cmd in ["playstore", "android", "screenshots", "screens"]:
            subprocess.run([sys.executable, str(PLAYSTORE_SCRIPT)], cwd=str(BASE_DIR))
        elif cmd in ["logos", "logo"]:
            subprocess.run([sys.executable, str(LOGOS_SCRIPT)], cwd=str(BASE_DIR))
        elif cmd in ["studio-ios", "apple-studio", "appstore-studio"]:
            if APPSTORE_HTML.exists():
                webbrowser.open(f"file://{APPSTORE_HTML}")
            else:
                print(f"⚠️ ไม่พบไฟล์ {APPSTORE_HTML}")
        elif cmd in ["studio", "studio-android", "playstore-studio"]:
            if PLAYSTORE_HTML.exists():
                webbrowser.open(f"file://{PLAYSTORE_HTML}")
        elif cmd in ["status", "info"]:
            print_banner()
            print_status()
        else:
            print("วิธีใช้:")
            print("  python3 run.py appstore           # ดึงภาพ Apple App Store ทั้งหมด")
            print("  python3 run.py search <ชื่อแอป>   # ค้นหาและดึงภาพแอปเฉพาะ")
            print("  python3 run.py studio-ios         # เปิด Apple App Store Studio")
            print("  python3 run.py playstore          # ดึงภาพ Google Play Store")
            print("  python3 run.py logos              # ดึงโลโก้ 35 แอป")
            print("  python3 run.py status             # ดูสถิติคลังรูปภาพ")
    else:
        interactive_menu()
