# 📘 Facebook Scraper & Intelligence Suite

โมดูลดึงข้อมูลและประมวลผลโพสต์กลุ่ม Facebook สำหรับสินค้าโทรศัพท์และไอทีมือสอง

## ✨ ความสามารถหลัก (Features)
- **GraphQL / Post Interception**: รองรับการดักจับโพสต์จาก Facebook Groups / Pages
- **NLP Regex Extractor**: สกัดชื่อรุ่น (iPhone, iPad, Samsung Galaxy), ความจุ, ราคา (บาท), สุขภาพแบตเตอรี่ (%) และรูปภาพ
- **Multi-Format Export**: ส่งออกข้อมูลอัตโนมัติในรูปแบบ JSON สะอาด และ CSV พร้อมเปิดใน Excel
- **Playwright Automation**: ระบบเลื่อนหน้าจอจำลองผู้ใช้จริง พร้อม Auto "ดูเพิ่มเติม (See more)"

## 🚀 วิธีใช้งาน (Usage)
```bash
# 1. ใช้งานผ่านเมนูแบบ Interactive
python3 run.py

# 2. คลีนไฟล์ JSON ที่มีอยู่เป็น CSV/JSON
python3 run.py parse

# 3. สั่ง Playwright ไปดึงหน้ากลุ่ม Facebook
python3 run.py "https://www.facebook.com/groups/..."
```

## 📁 โครงสร้างไดเรกทอรี (Directory Structure)
```
facebook_scraper/
├── config/             # การตั้งค่า Headers, User session
├── data/
│   ├── exports/        # ไฟล์ CSV สรุปผล
│   ├── json/           # ข้อมูลดิบและข้อมูลที่คลีนแล้ว
│   └── session/        # Playwright Persistent Browser Cookies/Session
├── extension/          # Chrome Extension สำหรับดักจับข้อมูลจากหน้าเว็บ
├── src/
│   └── scrapers/       # FacebookScraper Class
├── requirements.txt    # แพ็กเกจที่ต้องใช้
└── run.py              # CLI Master Launcher
```
