# 🤖 [AI Prompt & Developer Instructions] Apple App Store Media Scraper

> **สำหรับ AI Assistant (Claude / ChatGPT / Cursor / Antigravity / Windsurf):**
> คุณสามารถใช้ชุดเครื่องมือนี้ในการค้นหา, ดึงข้อมูล Metadata, ดาวน์โหลดโลโก้ (1024×1024) และรูปภาพตัวอย่างหน้าจอ (Screenshots) ระดับ Retina 4K (iPhone 1290×2796 / iPad Pro 2048×2732) จาก Apple App Store ได้ทันที **โดยไม่ต้องติดตั้ง pip packages ใดๆ เพิ่มเติม (Zero External Dependencies - ใช้เฉพาะ Python 3 Standard Library)**

---

## ⚡ 1. คำสั่งรันผ่าน Terminal (CLI Usage)

```bash
# ดึงภาพหน้าจอและโลโก้ของแอปเดียว
python3 appstore_scraper.py "Netflix"

# ดึงหลายแอปพร้อมกัน
python3 appstore_scraper.py "Netflix" "YouTube" "CapCut"

# ระบุโฟลเดอร์ปลายทาง
python3 appstore_scraper.py "TikTok" -o "./downloads"

# ดึงเฉพาะ iPhone (ไม่เอา iPad)
python3 appstore_scraper.py "Spotify" --devices iphone

# ดึงเฉพาะ Metadata JSON (ไม่ดาวน์โหลดรูปภาพ - เหมาะสำหรับ AI เรียกดูข้อมูลเร็ว)
python3 appstore_scraper.py "ChatGPT" --no-media --json
```

---

## 🐍 2. วิธี Import ใช้งานในโค้ด Python

```python
from appstore_scraper import AppStoreScraper

# สร้าง Object (ระบุโฟลเดอร์และรหัสประเทศได้)
scraper = AppStoreScraper(output_dir="./downloads", country="th")

# 1. ดึงเฉพาะข้อมูล Metadata (เร็วมาก ไม่โหลดรูป)
meta = scraper.fetch_metadata("Netflix")
# หรือใช้ URL: scraper.fetch_metadata("https://apps.apple.com/th/app/netflix/id363590051")
# หรือใช้ ID:  scraper.fetch_metadata("363590051")

# 2. ดึงข้อมูลพร้อมดาวน์โหลดภาพ Retina/4K ทั้งหมด
app_data = scraper.scrape_app("Canva", download_media=True, devices=["iphone", "ipad"])

print("ชื่อแอป:", app_data["track_name"])
print("ผู้พัฒนา:", app_data["artist_name"])
print("เรตติ้ง:", app_data["rating"])
print("ภาพ iPhone ที่โหลดได้:", len(app_data["iphone_screenshots"]))
```

---

## 📁 3. โครงสร้างโฟลเดอร์ที่บันทึก (Output Structure)

```text
appstore_output/
└── <app_name>_<track_id>/
    ├── logo.png                   # โลโก้แอป 1024×1024 uncompressed
    ├── info.json                  # ข้อมูล Metadata ครบทุกฟิลด์
    ├── iphone/
    │   ├── screenshot_01.png      # ภาพหน้าจอ iPhone 1290×2796
    │   ├── screenshot_02.png
    │   └── ...
    └── ipad/
        ├── screenshot_01.png      # ภาพหน้าจอ iPad Pro 2048×2732
        ├── screenshot_02.png
        └── ...
```

---

## 📑 4. โครงสร้างข้อมูล JSON (`info.json`)

```json
{
  "status": "success",
  "track_id": 363590051,
  "track_name": "Netflix",
  "artist_name": "Netflix, Inc.",
  "bundle_id": "com.netflix.Netflix",
  "category": "Entertainment",
  "genres": ["Entertainment", "Movies"],
  "version": "16.12.0",
  "price": "Free",
  "rating": 4.6,
  "rating_count": 185000,
  "file_size_mb": 95.4,
  "appstore_url": "https://apps.apple.com/th/app/netflix/id363590051",
  "description": "...",
  "release_notes": "...",
  "logo_path": ".../logo.png",
  "iphone_screenshots": [
    {
      "index": 1,
      "file_path": ".../iphone/screenshot_01.png",
      "url": "https://is1-ssl.mzstatic.com/.../1290x2796bb.png"
    }
  ],
  "ipad_screenshots": [
    {
      "index": 1,
      "file_path": ".../ipad/screenshot_01.png",
      "url": "https://is1-ssl.mzstatic.com/.../2048x2732bb.png"
    }
  ]
}
```
