import sys
import json
import urllib.parse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.advice_scraper import AdviceScraper
from src.scrapers.instagram_scraper import InstagramScraper
from src.scrapers.compasia_scraper import fetch_compasia_links
from src.scrapers.facebook_scraper import FacebookScraper
from src.scrapers.html_scraper import RawHtmlScraper
from src.services.storage import StorageService
from src.services.compasia_full_extractor import run_compasia_extractor
from src.services.download_all_instagram_posts import process_all_posts as process_all_ig
from config.settings import JSON_DIR, DATA_DIR

def print_banner():
    print("=" * 65)
    print("🛒 Multi-Source Web Scraper & Product Data Pipeline")
    print("   รองรับ: Advice | Instagram | CompAsia | Facebook | Raw HTML")
    print("=" * 65)

def run_advice(url: str):
    print(f"\n🚀 กำลังดึงข้อมูลจาก Advice: {url}")
    scraper = AdviceScraper()
    result = scraper.fetch_product(url)

    if result.get("status") != "success":
        print(f"❌ เกิดข้อผิดพลาด: {result.get('message')}")
        return

    data = result["data"]
    print("\n✅ ดึงข้อมูลสินค้าสำเร็จ!")
    print(f"📦 ชื่อสินค้า: {data.get('name')}")
    print(f"🏷️  รหัสสินค้า (SKU): {data.get('sku')}")
    print(f"🏢 แบรนด์: {data.get('brand')}")
    print(f"💰 ราคา: {data.get('price'):,} {data.get('currency')}" if data.get('price') else "💰 ราคา: -")
    print(f"📊 สถานะ: {'มีสินค้า (In Stock)' if data.get('in_stock') else 'สินค้าหมด (Out of Stock)'}")
    print(f"⚡ สเปกย่อ: {data.get('key_specs')}")

    json_file = StorageService.save_product_json(data)
    catalog_file = StorageService.update_catalog(data)
    csv_file = StorageService.export_to_csv()
    image_files = StorageService.download_product_images(data)

    print("\n📁 บันทึกข้อมูลเรียบร้อยแล้ว:")
    print(f"   📄 JSON: {json_file}")
    print(f"   📊 CSV:  {csv_file}")
    print(f"   🖼️  ดาวน์โหลดรูป: {len(image_files)} รูป ใน data/images/{data.get('sku')}/")

def run_instagram(username_or_url: str):
    print(f"\n📸 กำลังดึงข้อมูลจาก Instagram: {username_or_url}")
    scraper = InstagramScraper()
    result = scraper.fetch_profile_and_posts(username_or_url)

    if result.get("status") != "success":
        print(f"❌ เกิดข้อผิดพลาด: {result.get('message')}")
        return

    profile = result["profile"]
    posts = result["posts"]
    print(f"✅ ดึงข้อมูล Instagram สำเร็จ!")
    print(f"👤 บัญชี: @{profile.get('username')} ({profile.get('full_name')})")
    print(f"👥 ผู้ติดตาม: {profile.get('followers'):,} คน | โพสต์ทั้งหมด: {profile.get('total_posts'):,} โพสต์")
    print(f"📥 ดึงโพสต์ล่าสุด: {len(posts)} โพสต์")

    file_path = JSON_DIR / f"instagram_{profile.get('username')}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📁 บันทึกข้อมูลเรียบร้อยแล้ว: {file_path}")

def run_compasia(fetch_full: bool = True):
    print("\n🛍️ กำลังดึงข้อมูลสินค้าจาก CompAsia...")
    fetch_compasia_links(pages=[1, 2])
    if fetch_full:
        print("\n⏳ กำลังสกัดรายละเอียดเชิงลึกและดาวน์โหลดรูปภาพทั้งหมด...")
        run_compasia_extractor(max_workers=6)

def run_html_download(url: str):
    print(f"\n📄 กำลังดาวน์โหลด Raw HTML: {url}")
    saved_file = RawHtmlScraper.save_raw_html(url)
    if saved_file:
        RawHtmlScraper.inspect_html(saved_file)

def interactive_menu():
    print_banner()
    print("กรุณาเลือกประเภทการดึงข้อมูล:")
    print("  [1] ดึงข้อมูลสินค้าจาก Advice (ใส่ URL สินค้า)")
    print("  [2] ดึงข้อมูลร้านค้า/โพสต์จาก Instagram (ใส่ URL หรือ @Username)")
    print("  [3] ดึงสินค้าทั้งหมดจาก CompAsia (33 รายการ + ทุกตัวเลือก + รูปภาพ)")
    print("  [4] ดึงโพสต์ทั้งหมดจาก Instagram Links ที่มีอยู่ (228 โพสต์ + รูปภาพ)")
    print("  [5] ดาวน์โหลด Raw HTML ทั้งหน้าเว็บเก็บไว้ในเครื่อง")
    print("  [6] จัดระเบียบและคลีนข้อมูลทั้งหมด (Organize Datasets)")
    print("  [0] ออกจากโปรแกรม")
    print("-" * 65)

    choice = input("👉 เลือกเมนู (0-6): ").strip()

    if choice == "1":
        url = input("🔗 ใส่ URL สินค้า Advice: ").strip()
        if url:
            run_advice(url)
    elif choice == "2":
        target = input("📸 ใส่ Instagram URL หรือ Username: ").strip()
        if target:
            run_instagram(target)
    elif choice == "3":
        run_compasia(fetch_full=True)
    elif choice == "4":
        print("⏳ กำลังเริ่มดึงโพสต์ Instagram ทั้งหมด 228 โพสต์...")
        process_all_ig(max_workers=8)
    elif choice == "5":
        url = input("🌐 ใส่ URL หน้าเว็บที่ต้องการเซฟ HTML: ").strip()
        if url:
            run_html_download(url)
    elif choice == "6":
        from src.services.organize_workspace import BASE_DIR
        import subprocess
        subprocess.run([sys.executable, str(BASE_DIR / "src" / "services" / "organize_workspace.py")])
    elif choice == "0":
        print("👋 ออกจากโปรแกรมเรียบร้อย")
    else:
        print("⚠️ ตัวเลือกไม่ถูกต้อง")

def main():
    if len(sys.argv) == 1:
        interactive_menu()
        return

    arg = sys.argv[1]

    # Command Router
    if arg in ["--help", "-h"]:
        print_banner()
        print("การใช้งาน:")
        print("  python3 run.py                              # เปิดเมนูแบบ Interactive")
        print("  python3 run.py <URL_Advice>                 # ดึงสินค้า Advice")
        print("  python3 run.py <URL_Instagram>              # ดึงโพสต์ Instagram")
        print("  python3 run.py compasia                     # ดึงสินค้า CompAsia")
        print("  python3 run.py html <URL>                   # ดาวน์โหลด Raw HTML")
        return

    if arg.lower() == "compasia":
        run_compasia(fetch_full=True)
        return
    elif arg.lower() == "html" and len(sys.argv) > 2:
        run_html_download(sys.argv[2])
        return

    # Auto detect URL type
    if "instagram.com" in arg.lower():
        run_instagram(arg)
    elif "compasia.co.th" in arg.lower():
        run_compasia(fetch_full=True)
    elif "advice.co.th" in arg.lower():
        run_advice(arg)
    elif arg.startswith("http://") or arg.startswith("https://"):
        run_html_download(arg)
    else:
        run_instagram(arg)

if __name__ == "__main__":
    main()
