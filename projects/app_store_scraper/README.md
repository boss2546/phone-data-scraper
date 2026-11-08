# 📱 App Store & Google Play Store Media Scraper

โมดูลดึงโลโก้ทางการความละเอียดสูง (512×512 / 1024×1024) และภาพตัวอย่างหน้าจอแอปพลิเคชัน (Preview Screenshots ความละเอียดต้นฉบับ) ของ **35 แอปยอดนิยม** (สตรีมมิ่ง OTT, ซีรีส์สั้น, ตัดต่อ/ดีไซน์, เพลง, และ AI Tools) พร้อมหน้าเว็บ Interactive Studio

---

## ✨ ความสามารถหลัก (Features)
- **App Logos Scraper (`download_app_logos.py`)**: ดึงโลโก้ทางการของ 35 แอป พร้อมสร้าง `data/app_logos/apps_catalog.json` และหน้าพรีวิว `app_logos_preview.html`
- **Play Store Screenshots Scraper (`download_playstore_screenshots.py`)**: สกัดและดาวน์โหลดภาพตัวอย่างหน้าจอ (Preview Screenshots) ความละเอียดสูงรวม **460 ภาพ** แยกโฟลเดอร์รายแอปใน `data/app_screenshots/<app_id>/` พร้อม `screenshots_manifest.json`
- **Interactive Web Studio (`app_screenshots_studio.html`)**: แดชบอร์ดพรีวิวภาพหน้าจอทุกแอป พร้อมตัวกรองหมวดหมู่, แถบเลื่อน Carousel และระบบ Lightbox ซูมภาพขนาดใหญ่

---

## 🚀 วิธีใช้งาน (Usage)
```bash
# เรียกผ่าน Master CLI ที่ Root
python3 run.py appstore
python3 run.py appstore status
python3 run.py appstore logos
python3 run.py appstore screenshots

# หรือเรียกในโฟลเดอร์โมดูลโดยตรง
cd projects/app_store_scraper
python3 run.py
```

