#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import json
import csv
import urllib.request
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.scrapers.instagram_scraper import InstagramScraper
from config.settings import DATA_DIR, JSON_DIR, EXPORTS_DIR, IMAGES_DIR, DEFAULT_HEADERS

def print_banner():
    print("=" * 68)
    print("📸 Instagram Scraper & Media Intelligence")
    print("   ดึงข้อมูลโปรไฟล์, สถิติผู้ติดตาม, โพสต์ล่าสุด และรูปภาพ Carousel")
    print("=" * 68)

def download_images(images, post_id, username):
    dest_dir = IMAGES_DIR / username / post_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []
    for idx, img_url in enumerate(images, 1):
        dest = dest_dir / f"img_{idx}.jpg"
        if not dest.exists():
            try:
                req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
                with urllib.request.urlopen(req, timeout=10) as res:
                    with open(dest, "wb") as f:
                        f.write(res.read())
                downloaded.append(dest)
            except Exception:
                pass
        else:
            downloaded.append(dest)
    return downloaded

def run_scrape(target: str, download_media: bool = True):
    print(f"\n🚀 กำลังดึงข้อมูลจาก Instagram: {target}")
    scraper = InstagramScraper()
    result = scraper.fetch_profile_and_posts(target)

    if result.get("status") != "success":
        print(f"❌ เกิดข้อผิดพลาด: {result.get('message')}")
        return

    profile = result["profile"]
    posts = result["posts"]
    username = profile.get("username")

    print("\n✅ ดึงข้อมูล Instagram สำเร็จ!")
    print(f"👤 บัญชี:       @{username} ({profile.get('full_name') or '-'})")
    print(f"👥 ผู้ติดตาม:    {profile.get('followers'):,} คน | กำลังติดตาม: {profile.get('following'):,} คน")
    print(f"📦 โพสต์ทั้งหมด: {profile.get('total_posts'):,} โพสต์ (ดึงมา {len(posts)} โพสต์)")
    if profile.get("biography"):
        print(f"📝 Bio:         {profile.get('biography')[:100]}...")

    # 1. บันทึก JSON
    json_path = JSON_DIR / f"instagram_{username}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # 2. ส่งออก CSV
    csv_path = EXPORTS_DIR / f"instagram_{username}_posts.csv"
    if posts:
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["post_id", "shortcode", "likes", "comments", "images_count", "url", "caption"])
            writer.writeheader()
            for p in posts:
                writer.writerow({
                    "post_id": p.get("post_id"),
                    "shortcode": p.get("shortcode"),
                    "likes": p.get("likes"),
                    "comments": p.get("comments"),
                    "images_count": p.get("images_count"),
                    "url": p.get("url"),
                    "caption": p.get("caption", "").replace("\n", " ")[:200]
                })

    # 3. ดาวน์โหลดรูปภาพ
    if download_media and posts:
        print(f"\n🖼️ กำลังดาวน์โหลดรูปภาพจากโพสต์...")
        total_dl = 0
        for p in posts[:5]:
            imgs = download_images(p.get("images", []), p.get("shortcode", "unknown"), username)
            total_dl += len(imgs)
        print(f"   ↳ ดาวน์โหลดรูปภาพสำเร็จ {total_dl} ภาพ ใน data/images/{username}/")

    print("\n📁 บันทึกข้อมูลเรียบร้อย:")
    print(f"   📄 JSON: {json_path}")
    print(f"   📊 CSV:  {csv_path}")

def interactive_menu():
    while True:
        print_banner()
        print("กรุณาเลือกคำสั่ง:")
        print("  [1] ดึงข้อมูลโปรไฟล์และโพสต์ (ระบุ @Username หรือ URL)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 68)

        choice = input("👉 เลือกเมนู (0-1): ").strip()
        if choice == "0":
            print("👋 ออกจากโปรแกรม Instagram Scraper")
            break
        elif choice == "1":
            target = input("📸 ใส่ Instagram @Username หรือ URL: ").strip()
            if target:
                run_scrape(target)
            input("\nกด Enter เพื่อกลับสู่เมนูหลัก...")
        else:
            print("⚠️ ตัวเลือกไม่ถูกต้อง กรุณาลองใหม่\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ["--help", "-h"]:
            print_banner()
            print("วิธีใช้:")
            print("  python3 run.py                 # เปิดเมนู Interactive")
            print("  python3 run.py <@Username>     # ดึงข้อมูลจาก Username")
            print("  python3 run.py <Instagram_URL> # ดึงข้อมูลจาก URL")
        else:
            run_scrape(sys.argv[1])
    else:
        interactive_menu()
