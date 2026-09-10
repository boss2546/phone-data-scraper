# 🍎 Apple Scraper (ดึงข้อมูลสินค้า สเปก & ราคาจาก Apple Store)

โมดูลดึงข้อมูลสินค้าทางการ สเปกละเอียด (Tech Specs) และราคาจาก **Apple.com** (รองรับทั้ง Apple Store Thailand `apple.com/th` และ Global)

---

## 🌟 ฟีเจอร์หลัก (Features)

1. **ดึงข้อมูลภาพรวมสินค้า & ราคาทางการ (Product Overview & Official Pricing):**
   - สกัดชื่อรุ่น, ตระกูลสินค้า (iPhone, iPad, Mac, Watch)
   - สกัดราคาเริ่มต้นในไทย (THB) และราคาโปรโมชัน
   - ดึงรูปภาพสินค้าคุณภาพสูงจาก CDN ทางการของ Apple
2. **ดึงตารางข้อมูลทางเทคนิค (Tech Specs Parser):**
   - ชิปประมวลผล (Apple Silicon / A-Series)
   - หน้าจอและการแสดงผล (Super Retina XDR, ProMotion, ความสว่าง)
   - ความจุ (64GB, 128GB, 256GB, 512GB, 1TB, 2TB)
   - ระบบกล้อง ความละเอียด และการซูม
   - แบตเตอรี่และระบบการชาร์จ
   - ตัวเลือกสีและวัสดุตัวเครื่อง
3. **ส่งออกข้อมูล (Data Pipelines & Exports):**
   - บันทึก JSON สมบูรณ์ใน `data/json/<product_slug>.json`
   - สรุปตารางสินค้าเป็น CSV ใน `data/exports/apple_products_summary.csv`
   - ดาวน์โหลดรูปภาพสินค้าลงโฟลเดอร์ `data/images/<product_slug>/`

---

## 🚀 วิธีใช้งาน (Usage)

### 1. เรียกใช้งานผ่านโมดูลโดยตรง:
```bash
cd projects/apple_scraper

# เปิดเมนูแบบ Interactive
python3 run.py

# ดึงข้อมูลสินค้าระบุรุ่น
python3 run.py iphone-16-pro
python3 run.py https://www.apple.com/th/macbook-pro/
```

### 2. เรียกใช้งานผ่าน Master Orchestrator (Root CLI):
```bash
# รันผ่าน Alias
python3 run.py apple

# หรือเปิดเมนูรวมแล้วเลือก [8]
python3 run.py
```

---

## 📂 โครงสร้างโมดูล (Module Structure)

```text
projects/apple_scraper/
├── README.md
├── requirements.txt
├── run.py                       # ตัวรันคำสั่งประจำโมดูล
├── config/
│   └── settings.py              # การตั้งค่า Locale, Headers, Data Paths
├── src/
│   ├── scrapers/
│   │   ├── apple_scraper.py     # ดึงภาพรวมและราคา
│   │   └── tech_specs_scraper.py# ดึงตารางสเปกทางเทคนิค
│   └── services/
│       ├── formatter.py         # คลีนและแปลงข้อความ/ราคา
│       └── storage.py           # บันทึก JSON, CSV และดาวน์โหลดรูป
└── data/
    ├── raw_html/
    ├── json/
    ├── images/
    └── exports/
```
