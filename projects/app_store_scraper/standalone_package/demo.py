#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ตัวอย่างการเรียกใช้ AppStoreScraper ในสคริปต์ Python อื่นๆ (5 บรรทัดจบ)
"""

from appstore_scraper import AppStoreScraper

# 1. สร้างตัวดึงข้อมูล
scraper = AppStoreScraper(output_dir="./my_app_downloads", country="th")

# 2. ดึงข้อมูลและรูปภาพความละเอียดสูงของแอป (รองรับชื่อ, Track ID หรือ URL)
app_name = "ChatGPT"
print(f"กำลังดึงภาพและข้อมูลของ: {app_name} ...")
result = scraper.scrape_app(app_name, download_media=True, devices=["iphone", "ipad"])

# 3. นำข้อมูลไปใช้งานต่อ
if result.get("status") == "success":
    print(f"✅ สำเร็จ: {result['track_name']}")
    print(f"⭐ เรตติ้ง: {result['rating']} ({result['rating_count']:,} รีวิว)")
    print(f"📱 ภาพ iPhone: {len(result['iphone_screenshots'])} ภาพ")
    print(f"📟 ภาพ iPad: {len(result['ipad_screenshots'])} ภาพ")
    print(f"📂 บันทึกไว้ที่: {result['logo_path']}")
else:
    print(f"❌ ผิดพลาด: {result.get('message')}")
