#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.services.account_generator import UserAccountGenerator
from config.settings import JSON_DIR, EXPORTS_DIR

def print_banner():
    print("=" * 70)
    print("👥 User Account Generator — เครื่องมือสร้างบัญชีผู้ใช้จำลองอัตโนมัติ")
    print("   สำหรับทดสอบ E-Commerce, GraphQL Authentication, Persona Database")
    print("=" * 70)

def run_generate(count: int = 10):
    print(f"\n⏳ กำลังสร้างบัญชีผู้ใช้จำลอง {count} รายการ...")
    users = UserAccountGenerator.generate_accounts(count)
    print(f"\n🎉 สร้างบัญชีสำเร็จ {len(users)} รายการ!")
    print(f"📄 บันทึกไฟล์ JSON: {JSON_DIR / 'generated_users.json'}")
    print(f"📊 ส่งออกไฟล์ CSV:  {EXPORTS_DIR / 'generated_users.csv'}")

    print("\n🔍 ตัวอย่างบัญชีแรกที่สร้าง:")
    first = users[0]
    print(f"   👤 ชื่อ-สกุล: {first['full_name']}")
    print(f"   📧 Email:    {first['email']}")
    print(f"   🔑 รหัสผ่าน:  {first['password']}")
    print(f"   📱 เบอร์โทร: {first['phone']}\n")

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] สร้างบัญชีจำลอง 10 รายการ")
        print("  [2] กำหนดจำนวนบัญชีที่ต้องการสร้างเอง")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 70)

        choice = input("👉 เลือกเมนู (0-2): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม User Account Generator")
            break
        elif choice == "1":
            run_generate(10)
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice == "2":
            c_str = input("🔢 ใส่จำนวนบัญชีที่ต้องการสร้าง: ").strip()
            if c_str.isdigit():
                run_generate(int(c_str))
            input("กด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        run_generate(int(sys.argv[1]))
    else:
        interactive_menu()
