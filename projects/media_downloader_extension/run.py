#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎬 Universal Media Grabber — Chrome Extension & Local Transcoder Launcher
"""
import sys
import subprocess
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SERVER_SCRIPT = BASE_DIR / "src" / "companion_server.py"
GENERATE_SCRIPT = BASE_DIR / "src" / "generate_assets.py"
TEST_SCRIPT = BASE_DIR / "tests" / "test_e2e_media_grabber.py"
EXT_DIR = BASE_DIR / "extension"


def print_banner():
    print("=" * 74)
    print("🎬 Universal Media Grabber — Chrome Extension & Standard Media Converter")
    print("   วางเมาส์เหนือภาพ/วิดีโอแล้วโหลดเป็นไฟล์มาตรฐาน (.PNG / .JPG / .MP4) ทันที")
    print("=" * 74)
    print(f"📂 โฟลเดอร์สำหรับติดตั้งใน Chrome (Load unpacked): {EXT_DIR}")
    print("-" * 74)


def interactive_menu():
    while True:
        print_banner()
        print("เลือกเมนูการทำงาน:")
        print("  [1] 🚀 เปิดเซิร์ฟเวอร์แปลงไฟล์ & ห้องแล็บทดสอบ (Start Companion Server :8765)")
        print("  [2] 🧪 รันทดสอบ E2E ครบทุกนามสกุลภาพและวิดีโอ (Run Automated E2E Tests)")
        print("  [3] 🎨 สร้างไฟล์ตัวอย่างสำหรับทดสอบใหม่ครบทุกนามสกุล (Regenerate Test Assets)")
        print("  [4] 🌐 เปิดหน้าเว็บห้องแล็บทดสอบในเบราว์เซอร์ (http://127.0.0.1:8765/sandbox)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 74)

        choice = input("👉 เลือกเมนู (0-4): ").strip()
        if choice == "0":
            break
        elif choice == "1":
            subprocess.run([sys.executable, str(SERVER_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "2":
            subprocess.run([sys.executable, str(TEST_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "3":
            subprocess.run([sys.executable, str(GENERATE_SCRIPT)], cwd=str(BASE_DIR))
        elif choice == "4":
            webbrowser.open("http://127.0.0.1:8765/sandbox")
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["server", "start", "serve"]:
            subprocess.run([sys.executable, str(SERVER_SCRIPT)] + sys.argv[2:], cwd=str(BASE_DIR))
        elif cmd in ["test", "tests", "verify"]:
            rc = subprocess.run([sys.executable, str(TEST_SCRIPT)], cwd=str(BASE_DIR)).returncode
            sys.exit(rc)
        elif cmd in ["assets", "generate"]:
            subprocess.run([sys.executable, str(GENERATE_SCRIPT)], cwd=str(BASE_DIR))
        else:
            print("วิธีใช้: python3 run.py [server | test | assets]")
    else:
        interactive_menu()
