# 🌐 แซนบล็อกดึงข้อมูล — Master Data Scraping & Interception Suite

> ศูนย์รวมสถาปัตยกรรมเครื่องมือดึงข้อมูล, ดักจับสเปกสินค้า, และวิเคราะห์ราคากลางอัจฉริยะ (Modular Multi-Project Monorepo)

---

## 🏛️ สถาปัตยกรรมระบบ (System Architecture)

โปรเจกต์นี้ได้รับการจัดระเบียบโครงสร้างใหม่เป็นแบบ **Modular Micro-Projects** โดยแต่ละระบบย่อยจะอยู่ภายใต้ไดเรกทอรี `projects/` มีสภาพแวดล้อม การตั้งค่า (`config`), ซอร์สโค้ด (`src`), ไฟล์รัน (`run.py`), ข้อมูล (`data`), และเอกสารประกอบ (`README.md`) ของตนเองอย่างเป็นอิสระ พร้อมระบบควบคุมศูนย์กลางผ่าน Master CLI ที่ Root (`run.py`)

```
แซนบล็อกดึงข้อมูล/
├── run.py                          # 🎛️ Master Launcher & Interactive CLI
├── requirements.txt                # 📦 รวบรวม Dependencies ทั้งหมดของระบบ
├── .gitignore                      # 🛡️ ละเว้นไฟล์ Caches, Sessions, Virtualenvs
├── README.md                       # 📖 คู่มือและสถาปัตยกรรมแม่บท
│
└── projects/                       # 📂 ศูนย์รวมโมดูลโปรเจกต์ย่อย (9 Subprojects)
    ├── apple_scraper/              # 🍎 Apple Official Store Crawler (188 รุ่น 515 สี + 4K Retina)
    ├── facebook_scraper/           # 📘 Facebook Groups & Post Intelligence
    ├── compasia_scraper/           # 🛍️ CompAsia Secondhand Phone Scraper
    ├── advice_scraper/             # 💻 Advice IT Products & Schema Scraper
    ├── instagram_scraper/          # 📸 Instagram Profile & Carousel Media Scraper
    ├── bma_weather_radar/          # 🌧️ BMA Real-time Weather Radar & Rain Tracker
    ├── market_intelligence/        # 📊 Cross-Platform Price Comparison & Deal Hunter
    ├── user_account_generator/     # 👥 Synthetic User Accounts & GraphQL Persona Generator
    └── rea_reverse_engineering/    # 🔬 Reverse Engineer Anything (MCP Server & Binary/HAR Inspector)
```

---

## 📋 ตารางสรุปโมดูลระบบทั้งหมด (Systems Catalog)

| # | โมดูลระบบ | ไดเรกทอรี | คำสั่งย่อ (Alias) | สถานะ | รายละเอียด |
|---|---|---|---|---|---|
| **1** | **Facebook Scraper** | `projects/facebook_scraper/` | `fb`, `facebook` | 🟢 พร้อมใช้งาน | สกัดโพสต์ Facebook, ชื่อรุ่น, แบตเตอรี่, ราคา และส่งออก CSV/JSON |
| **2** | **BMA Weather Radar** | `projects/bma_weather_radar/` | `radar`, `weather`, `bma` | 🟢 พร้อมใช้งาน | ดึงภาพเรดาร์สถานีหนองแขม/หนองจอก และรายงานฝน กทม. Real-time |
| **3** | **CompAsia Scraper** | `projects/compasia_scraper/` | `compasia`, `shopify` | 🟢 พร้อมใช้งาน | ดึงสินค้ามือสองผ่าน Shopify API, สกัดรุ่นย่อย, สุขภาพแบตเตอรี่ และรูปภาพ |
| **4** | **Instagram Scraper** | `projects/instagram_scraper/` | `ig`, `instagram` | 🟢 พร้อมใช้งาน | ดึงข้อมูลโปรไฟล์ สถิติผู้ติดตาม โพสต์ และภาพอัลบั้ม Carousel |
| **5** | **Advice Scraper** | `projects/advice_scraper/` | `advice` | 🟢 พร้อมใช้งาน | ดึงข้อมูลสินค้าไอทีจาก Advice.co.th, Schema JSON-LD และภาพ HD |
| **6** | **Market Intelligence** | `projects/market_intelligence/` | `market`, `analyze` | 🟢 พร้อมใช้งาน | วิเคราะห์เปรียบเทียบราคากลางทางการ vs มือสอง และตรวจหาดีลคุ้มค่า |
| **7** | **User Account Generator** | `projects/user_account_generator/` | `users`, `mod` | 🟢 พร้อมใช้งาน | สร้างบัญชีผู้ใช้จำลองสำหรับทดสอบ E-Commerce / GraphQL |
| **8** | **Apple Scraper** | `projects/apple_scraper/` | `apple`, `ap` | 🟢 สมบูรณ์ 100% | ดึงข้อมูลทางการ Apple Store Thailand ครบ 188 รุ่น 515 สี, SQLite, Web Studio |
| **9** | **REA Reverse Engineering** | `projects/rea_reverse_engineering/` | `rea`, `reverse` | 🟢 สมบูรณ์ 100% | วิเคราะห์ Binary (Mach-O/ELF), Codesign, Plist, Dynamic Libs & Network HAR |

---

## ⚡ เริ่มต้นใช้งาน (Quick Start)

### 1. ติดตั้ง Dependencies
```bash
# ติดตั้งแพ็กเกจทั้งหมดผ่าน Root
pip install -r requirements.txt

# (ทางเลือก) ติดตั้ง Chromium สำหรับระบบที่ใช้ Playwright
playwright install chromium
```

### 2. รันผ่าน Master Interactive CLI
```bash
python3 run.py
```
จะปรากฏเมนูควบคุมระบบหลักให้เลือกใช้งาน:
```text
========================================================================
🌐 แซนบล็อกดึงข้อมูล — Master Data Scraping & Interception Suite
   ศูนย์รวมเครื่องมือดึงข้อมูลและดักข้อมูลอัจฉริยะ (Modular Architecture)
========================================================================
กรุณาเลือกโมดูลระบบที่ต้องการสั่งการ:
  [1] 📘 Facebook Scraper (GraphQL Interceptor & Post Intelligence)
  [2] 🌧️ BMA Weather Radar (ดักจับภาพเรดาร์ & ข้อมูลฝน กทม. Real-time)
  [3] 🛍️ CompAsia Scraper (Shopify API & Multi-threaded Variants)
  [4] 📸 Instagram Scraper (ดึงโปรไฟล์ & รูปภาพ Carousel)
  [5] 💻 Advice Scraper (ดึงสินค้าไอที JSON-LD & HD Gallery)
  [6] 📊 Market Intelligence (วิเคราะห์ราคากลาง & Deal Hunter)
  [7] 👥 User Account Generator (สร้างบัญชี GraphQL อัตโนมัติ)
  [8] 🍎 Apple Scraper (ดึงข้อมูลสินค้าทางการ สเปก & ราคาจาก Apple Store)
  [9] 🔬 REA Reverse Engineering (วิเคราะห์ Binary, App & Runtime ด้วย MCP/CLI)
  ----------------------------------------------------------------------
  [s] 🗂️ ดูภาพรวมสถานะข้อมูลทุกระบบ (Inspect All Systems Status)
  [0] ออกจากโปรแกรม
------------------------------------------------------------------------
👉 เลือกเมนู (0-9 หรือ s): 
```

### 3. รันคำสั่งตรงผ่าน Shortcuts (CLI Aliases)
```bash
# ตรวจสอบภาพรวมสถานะและจำนวนไฟล์ของทุกระบบ
python3 run.py status

# รันระบบ REA Reverse Engineering (หรือทดสอบ: python3 run.py rea test)
python3 run.py rea

# รันระบบ Apple Scraper
python3 run.py apple

# รันวิเคราะห์ราคากลาง Market Intelligence
python3 run.py market run

# ดึงข้อมูลเรดาร์สภาพอากาศ กทม.
python3 run.py weather run

# ประมวลผลและคลีนข้อมูล Facebook Posts
python3 run.py fb parse

# สร้างบัญชีผู้ใช้จำลอง 20 บัญชี
python3 run.py users 20
```

---

## 🗄️ รูปแบบข้อมูลที่ส่งออก (Export Standards)
- **JSON**: ข้อมูลดิบและแบบจัดโครงสร้าง (`data/json/`)
- **CSV (Excel UTF-8 BOM)**: ตารางข้อมูลพร้อมเปิดใน Microsoft Excel ได้ทันที (`data/exports/`)
- **SQLite Relational DB**: ฐานข้อมูลเชิงสัมพันธ์พร้อม Views และ Foreign Keys (ใน `apple_scraper`)
- **Web UI Studio**: พรีวิวแบบอินเตอร์แอคทีฟ (เช่น `projects/apple_scraper/catalog_preview.html`)
