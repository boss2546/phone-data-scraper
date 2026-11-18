# 📱 Apple App Store & Google Play Store Media Scraper

โมดูลดึงรูปภาพตัวอย่างหน้าจอ (Screenshots) ความละเอียดสูงสุดระดับ **Retina 4K (iPhone สูงสุด 1290×2796 / iPad Pro สูงสุด 2048×2732)** และโลโก้ทางการความละเอียดสูง (1024×1024) ของ **35 แอปยอดนิยม** ในสโตร์ประเทศไทย (TH Storefront) พร้อมหน้า Interactive Web Studio สไตล์ Pastel Mint

---

## ✨ ความสามารถหลัก (Features)

1. **🍎 Apple App Store Screenshots Scraper (`download_appstore_screenshots.py`)**:
   - ดึงภาพ Screenshots ความละเอียดสูงสุดระดับ Retina/4K ของ iPhone และ iPad จาก Apple Official iTunes Storefront API
   - แยกโฟลเดอร์รายแอปอย่างเป็นระบบใน `data/appstore_screenshots/<app_id>/`:
     - `logo.png`: โลโก้แอป 1024×1024 คมชัดสูงสุด
     - `iphone/screenshot_*.png`: ภาพหน้าจอ iPhone (1290×2796)
     - `ipad/screenshot_*.png`: ภาพหน้าจอ iPad Pro (2048×2732)
     - `info.json`: ข้อมูล Metadata ละเอียดครบถ้วน (เรตติ้ง, ผู้พัฒนา, ขนาดไฟล์, หมวดหมู่)
   - รองรับการค้นหาแอปใดๆ ใน App Store ผ่านคำสั่งค้นหา (Search Mode)
   - มีปุ่ม **"1-Click Copy Prompt AI"** สำหรับนำข้อมูลและรูปภาพไปให้ AI วิเคราะห์ UI/UX หรือเขียนโค้ดต่อได้ทันที

2. **🤖 Google Play Store Screenshots Scraper (`download_playstore_screenshots.py`)**:
   - สกัดและดาวน์โหลดภาพตัวอย่างหน้าจอของฝั่ง Android รวม **460 ภาพ** ใน `data/app_screenshots/<app_id>/`

3. **🎨 App Logos Scraper (`download_app_logos.py`)**:
   - ดึงโลโก้ทางการความละเอียดสูงของ 35 แอป พร้อมสร้าง `data/app_logos/apps_catalog.json`

4. **🌟 Interactive Web Studios**:
   - `appstore_screenshots_studio.html`: แดชบอร์ดแกเลอรี Apple App Store ธีม Ultra-Luxury Pastel Mint & Emerald Glassmorphism พร้อมระบบ Lightbox ซูมภาพ 4K, ตัวสลับ iPhone/iPad, ตัวกรองหมวดหมู่ และค้นหาแบบเรียลไทม์
   - `app_screenshots_studio.html`: แดชบอร์ดฝั่ง Android Play Store

---

## 🚀 วิธีใช้งาน (Usage)

### ผ่าน Interactive CLI:
```bash
# เรียกผ่าน Master CLI ที่ Root
python3 run.py appstore

# หรือเรียกในโฟลเดอร์โมดูลโดยตรง
cd projects/app_store_scraper
python3 run.py
```

### คำสั่งด่วน (Command-line Shortcuts):
```bash
# ดึงภาพหน้าจอ Apple App Store ทั้งหมด 35 แอป
python3 run.py appstore

# ค้นหาและดึงภาพแอปเฉพาะใน Apple App Store (เช่น TikTok หรือ Line)
python3 run.py search "TikTok"

# เปิดแดชบอร์ด Apple App Store Studio ทันที
python3 run.py studio-ios

# ดูสถิติจำนวนภาพในคลัง
python3 run.py status
```
