#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

# Base Directory
BASE_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = BASE_DIR / "projects"

PROJECTS = {
    "1": ("facebook_scraper", "📘 Facebook Scraper (GraphQL Interceptor & Post Intelligence)", "projects/facebook_scraper/run.py"),
    "2": ("bma_weather_radar", "🌧️ BMA Weather Radar (ดักจับภาพเรดาร์ & ข้อมูลฝน กทม. Real-time)", "projects/bma_weather_radar/run.py"),
    "3": ("compasia_scraper", "🛍️ CompAsia Scraper (Shopify API & Multi-threaded Variants)", "projects/compasia_scraper/run.py"),
    "4": ("instagram_scraper", "📸 Instagram Scraper (ดึงโปรไฟล์ & รูปภาพ Carousel)", "projects/instagram_scraper/run.py"),
    "5": ("advice_scraper", "💻 Advice Scraper (ดึงสินค้าไอที JSON-LD & HD Gallery)", "projects/advice_scraper/run.py"),
    "6": ("market_intelligence", "📊 Market Intelligence (วิเคราะห์ราคากลาง & Deal Hunter)", "projects/market_intelligence/run.py"),
    "7": ("user_account_generator", "👥 User Account Generator (สร้างบัญชี GraphQL อัตโนมัติ)", "projects/user_account_generator/run.py"),
    "8": ("apple_scraper", "🍎 Apple Scraper (ดึงข้อมูลสินค้าทางการ สเปก & ราคาจาก Apple Store)", "projects/apple_scraper/run.py"),
}

ALIASES = {
    "fb": "1", "facebook": "1",
    "radar": "2", "weather": "2", "bma": "2",
    "compasia": "3", "shopify": "3",
    "ig": "4", "instagram": "4",
    "advice": "5",
    "market": "6", "analyze": "6",
    "users": "7", "mod": "7",
    "apple": "8", "ap": "8"
}

def print_banner():
    print("=" * 72)
    print("🌐 แซนบล็อกดึงข้อมูล — Master Data Scraping & Interception Suite")
    print("   ศูนย์รวมเครื่องมือดึงข้อมูลและดักข้อมูลอัจฉริยะ (Modular Architecture)")
    print("=" * 72)

def launch_subproject(proj_key: str, extra_args: list = None):
    if proj_key not in PROJECTS:
        print(f"❌ ไม่พบโปรเจกต์หมายเลข: {proj_key}")
        return

    folder_name, title, script_rel_path = PROJECTS[proj_key]
    proj_dir = PROJECTS_DIR / folder_name
    script_path = BASE_DIR / script_rel_path

    if not script_path.exists():
        print(f"❌ ไม่พบไฟล์รันของโปรเจกต์: {script_path}")
        return

    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(f"\n🚀 กำลังเปิดใช้งาน: {title} ...")
    print(f"📁 Working Directory: projects/{folder_name}/")
    print("-" * 72)
    try:
        subprocess.run(cmd, cwd=str(proj_dir))
    except KeyboardInterrupt:
        print("\n👋 ยกเลิกการทำงาน")

def print_status_overview():
    print("\n" + "=" * 72)
    print("🗂️  ภาพรวมสถานะข้อมูลและไฟล์ในแต่ละระบบ (Systems Status Overview)")
    print("=" * 72)
    
    for key, (folder, title, _) in PROJECTS.items():
        p_dir = PROJECTS_DIR / folder
        data_dir = p_dir / "data"
        
        file_count = 0
        if data_dir.exists():
            file_count = sum(1 for f in data_dir.rglob("*") if f.is_file() and not f.name.startswith("."))

        dashboards = [f.name for f in p_dir.glob("*.html")]
        dash_str = f" | 🌐 Web UI: {', '.join(dashboards)}" if dashboards else ""

        print(f"[{key}] {title}")
        print(f"    ↳ โฟลเดอร์: projects/{folder}/ | 📦 ไฟล์ข้อมูล: {file_count} ไฟล์{dash_str}")
        print()

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกโมดูลระบบที่ต้องการสั่งการ:")
        for key, (_, title, _) in PROJECTS.items():
            print(f"  [{key}] {title}")
        print("  ----------------------------------------------------------------------")
        print("  [9] 🗂️ ดูภาพรวมสถานะข้อมูลทุกระบบ (Inspect All Systems Status)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 72)

        choice = input("👉 เลือกเมนู (0-9): ").strip()

        if choice == "0":
            print("👋 ออกจากโปรแกรม ขอบคุณครับ!")
            sys.exit(0)
        elif choice == "9":
            print_status_overview()
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        elif choice in PROJECTS:
            launch_subproject(choice)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["status", "overview", "info"]:
            print_banner()
            print_status_overview()
        elif arg in ALIASES:
            proj_key = ALIASES[arg]
            launch_subproject(proj_key, extra_args=sys.argv[2:])
        elif arg in PROJECTS:
            launch_subproject(arg, extra_args=sys.argv[2:])
        else:
            print(f"❌ ไม่รู้จักคำสั่ง '{arg}'")
            print("💡 คำสั่งที่รองรับ: fb, radar, compasia, ig, advice, market, users, apple, status")
    else:
        interactive_menu()
