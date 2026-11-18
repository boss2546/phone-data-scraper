#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form & API Interceptor — CLI Runner & Orchestrator
ศูนย์ควบคุมเครื่องมือดักจับ API, บันทึกฟอร์ม และสร้างสคริปต์บอทอัตโนมัติ
"""

import sys
import os
import json
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
EXTENSION_DIR = BASE_DIR / "extension"
TEST_FORM_PATH = BASE_DIR / "test_form.html"
TEST_CRYPTO_BENCH_PATH = BASE_DIR / "test_encryption_bench.html"
CAPTURES_DIR = BASE_DIR / "data" / "captures"
EXPORTS_DIR = BASE_DIR / "data" / "exports"

sys.path.insert(0, str(BASE_DIR))

from src.generator import generate_python_requests_script, generate_playwright_script

def print_banner():
    print("=" * 72)
    print("🎯 Form & API Interceptor — ชุดเครื่องมือดัก API & แผนที่ฟอร์มอัจฉริยะ")
    print("   รวบรวมข้อมูลจริงจากการกรอก เพื่อสร้างระบบอัตโนมัติ (API & Browser Bots)")
    print("=" * 72)

def show_install_guide():
    print("\n" + "=" * 72)
    print("📦 วิธีติดตั้ง Extension บน Google Chrome (ใช้เวลาไม่เกิน 30 วินาที):")
    print("=" * 72)
    print("1. เปิด Google Chrome แล้วพิมพ์ในช่อง URL:")
    print("   👉 chrome://extensions/")
    print("2. เปิดสวิตช์ 'Developer mode' (โหมดนักพัฒนา) ที่มุมบนขวา")
    print("3. กดปุ่ม 'Load unpacked' (โหลดส่วนขยายที่คลายการบีบอัดแล้ว)")
    print(f"4. เลือกโฟลเดอร์นี้:")
    print(f"   📁 {EXTENSION_DIR.resolve()}")
    print("5. ไอคอน 🎯 'Form & API Interceptor' จะปรากฏบนแถบเครื่องมือของ Chrome ทันที!")
    print("=" * 72)

def open_test_bench():
    print(f"\n🧪 กำลังเปิดห้องแล็บทดสอบ: {TEST_FORM_PATH.resolve()} ในเบราว์เซอร์...")
    webbrowser.open(TEST_FORM_PATH.resolve().as_uri())

def open_crypto_bench():
    print(f"\n🔐 กำลังเปิดห้องแล็บทดสอบการเข้ารหัส (Pastel Green UI): {TEST_CRYPTO_BENCH_PATH.resolve()} ในเบราว์เซอร์...")
    webbrowser.open(TEST_CRYPTO_BENCH_PATH.resolve().as_uri())

def start_webhook_server():
    from src.server import start_server
    start_server(port=8091)

def generate_scripts_from_latest():
    CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    json_files = sorted(CAPTURES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not json_files:
        print("\n❌ ยังไม่พบไฟล์ Session JSON ในโฟลเดอร์ data/captures/")
        print("👉 แนะนำให้เปิดโหมดบันทึกใน Extension แล้วลองกรอกฟอร์มก่อนนะคะ")
        return

    latest_file = json_files[0]
    print(f"\n📂 กำลังประมวลผลไฟล์ล่าสุด: {latest_file.name} ...")

    with open(latest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    session_id = data.get("id") or latest_file.stem
    api_script = generate_python_requests_script(data, 0)
    browser_script = generate_playwright_script(data)

    api_path = EXPORTS_DIR / f"{session_id}_direct_api.py"
    browser_path = EXPORTS_DIR / f"{session_id}_playwright_bot.py"

    with open(api_path, "w", encoding="utf-8") as f:
        f.write(api_script)
    os.chmod(api_path, 0o755)

    with open(browser_path, "w", encoding="utf-8") as f:
        f.write(browser_script)
    os.chmod(browser_path, 0o755)

    print("✅ สร้างสคริปต์อัตโนมัติสำเร็จเรียบร้อยแล้วค่ะ:")
    print(f"  1. 🐍 สคริปต์ยิง API ตรง: {api_path.relative_to(BASE_DIR)}")
    print(f"  2. 🎭 สคริปต์ Playwright เบราว์เซอร์: {browser_path.relative_to(BASE_DIR)}")

def run_test_suite():
    from tests.test_suite import run_all_tests
    run_all_tests()

def run_gemini_live_chat(new_chat=False):
    python_bin = "/Users/meuu/Desktop/รวมโปรเจ็ค/ai_qa_court/.venv/bin/python"
    script_path = str(SRC_DIR / "gemini_live_chat.py")
    args = [python_bin, script_path]
    if new_chat:
        args.append("--new")
    os.execv(python_bin, args)

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่งการทำงาน:")
        print("  [1] 🧪 เปิดห้องแล็บฟอร์มทั่วไป (Standard Test Bench HTML)")
        print("  [2] 🔐 เปิดห้องแล็บทดสอบการเข้ารหัสพรีเมียมพาสเทล (Encryption Test Bench)")
        print("  [3] 🔌 เริ่มต้น Local Webhook Server (Port 8091)")
        print("  [4] 🤖 แปลง JSON ล่าสุดเป็นสคริปต์อัตโนมัติ (Python & Playwright)")
        print("  [5] 📖 ดูวิธีติดตั้ง Extension บน Google Chrome")
        print("  [6] 🔬 รันชุดทดสอบระบบแบบละเอียด (Comprehensive 24-Point Test Suite)")
        print("  [7] 💬 รันบอทสนทนาอัตโนมัติบนหน้าเว็บจริง (Gemini Live Chat - Headed Mode)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 72)
        choice = input("👉 เลือกเมนู (0-7): ").strip()

        if choice == "1":
            open_test_bench()
            break
        elif choice == "2":
            open_crypto_bench()
            break
        elif choice == "3":
            start_webhook_server()
            break
        elif choice == "4":
            generate_scripts_from_latest()
            break
        elif choice == "5":
            show_install_guide()
            break
        elif choice == "6":
            run_test_suite()
            break
        elif choice == "7":
            run_gemini_live_chat()
            break
        elif choice == "0":
            print("👋 ขอบคุณค่ะบอส!")
            break
        else:
            print("❌ เลือกเมนูไม่ถูกต้อง ลองใหม่อีกครั้งค่ะ")

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["test", "lab", "bench"]:
            open_test_bench()
        elif cmd in ["crypto", "encrypt", "encryption"]:
            open_crypto_bench()
        elif cmd in ["server", "webhook"]:
            start_webhook_server()
        elif cmd in ["gen", "generate", "code"]:
            generate_scripts_from_latest()
        elif cmd in ["install", "guide", "help"]:
            show_install_guide()
        elif cmd in ["suite", "tests", "test-suite", "check"]:
            run_test_suite()
        elif cmd in ["chat", "gemini", "bot"]:
            run_gemini_live_chat()
        elif cmd in ["chat-new", "gemini-new"]:
            run_gemini_live_chat(new_chat=True)
        else:
            print(f"❌ คำสั่งไม่ถูกต้อง: {cmd}")
            print("การใช้งาน: python3 run.py [test | crypto | server | generate | install | suite | chat]")
    else:
        interactive_menu()

if __name__ == "__main__":
    main()
