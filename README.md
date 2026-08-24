# 📱 Data Scraping & Product Catalog System

ระบบดึงข้อมูลและจัดเก็บสินค้าจาก **Instagram, Facebook Groups และ Advice** จัดเก็บอย่างเป็นระเบียบ พร้อมระบบค้นหาและเปิดดูข้อมูล

---

## 📂 โครงสร้างโฟลเดอร์ที่เป็นระเบียบ (Clean Project Structure)

```text
เล่นๆ/
├── 📁 config/
│   └── settings.py                        # ค่า Config Path และ Headers
│
├── 📁 data/
│   ├── 📁 exports/                        # ไฟล์ Excel / CSV ที่ Clean เรียบร้อยแล้ว (ไม่มีบรรทัดแตก)
│   │   ├── instagram_products_cleaned.csv # ตารางสินค้า Instagram (รุ่น, ความจุ, ราคา, แบต, รูป)
│   │   └── facebook_products_cleaned.csv  # ตารางสินค้า Facebook Group
│   │
│   ├── 📁 instagram/                      # ข้อมูลดิบและ JSON รวมของ Instagram (228 โพสต์)
│   │   ├── all_posts_data.json
│   │   └── instagram_products_cleaned.json
│   │
│   ├── 📁 facebook/                       # ข้อมูลดิบและ JSON ของ Facebook Group
│   │   └── facebook_group_posts.json
│   │
│   ├── 📁 images/                         # รูปภาพสินค้าทั้งหมดที่ดาวน์โหลดลงเครื่อง
│   │   └── 📁 instagram/                  # รูปภาพแยกโฟลเดอร์ post_001 ถึง post_228
│   │
│   └── 📁 links/                          # ไฟล์รวบรวมลิงก์ทั้งหมด
│       ├── instagram_all_links.txt        # 228 ลิงก์ Instagram
│       ├── instagram_post_links.txt
│       └── facebook_post_links.txt
│
├── 📁 src/
│   ├── 📁 scrapers/                       # โมดูล Scraper (Advice, Instagram, Facebook)
│   └── 📁 services/                       # เซอร์วิสประมวลผลข้อมูล จัดระเบียบ และดาวน์โหลดรูป
│
├── 🌐 catalog.html                        # แดชบอร์ดเปิดดูแคตตาล็อกสินค้าพร้อมรูปภาพผ่านเว็บเบราว์เซอร์
├── 📄 run.py                              # ตัวรันคำสั่งดึงข้อมูล
└── 📄 README.md
```

---

## 🚀 การเปิดดูข้อมูล

1. **เปิดดูแบบตาราง Excel / Numbers:**
   - เปิดไฟล์ [`data/exports/instagram_products_cleaned.csv`](file:///Users/meuu/Desktop/เล่นๆ/data/exports/instagram_products_cleaned.csv)
   - เปิดไฟล์ [`data/exports/facebook_products_cleaned.csv`](file:///Users/meuu/Desktop/เล่นๆ/data/exports/facebook_products_cleaned.csv)

2. **เปิดดูแบบแกลเลอรีเว็บ (Interactive Dashboard):**
   - ดับเบิลคลิกเปิดไฟล์ [`catalog.html`](file:///Users/meuu/Desktop/เล่นๆ/catalog.html) ในเบราว์เซอร์ เพื่อดูภาพสินค้า ค้นหารุ่น และกรองราคาได้ทันที
