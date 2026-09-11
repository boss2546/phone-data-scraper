# 📖 คู่มือการนำฐานข้อมูล Apple Store Thailand ไปใช้งาน (Developer & Data Guide)

> **เวอร์ชัน:** 3.0.0 (Unified Edition)  
> **แหล่งข้อมูล:** Apple Store Thailand ทางการ (Official Catalog & CDN Assets)  
> **มาตรฐาน:** รองรับทั้งแบบ JSON, Web SDK (JavaScript), ฐานข้อมูล SQLite/SQL Dump และตาราง Excel CSV

---

## ⚡ สรุปเร็ว: "จะทำอะไร... ต้องใช้ไฟล์ไหน?" (Quickstart Decision Matrix)

ไม่ต้องเดาหรือสับสนระหว่างหลายไฟล์ ตารางนี้จะบอกทันทีว่างานของคุณเหมาะกับไฟล์ใดที่สุด:

| สิ่งที่คุณต้องการทำ | ไฟล์ที่ต้องใช้ | พาธไฟล์ในโปรเจกต์ |
|---|---|---|
| 🌟 **รวมทุกอย่างในไฟล์เดียว 100%** (สเปก, รุ่นย่อย, สี, รูปโปร่งใส, รูปต้นฉบับ, แกลเลอรี 4K) | **Master Unified JSON** | `data/exports/apple_unified_catalog.json` |
| ⚡ **ทำเว็บ Frontend ทันที ไม่ต้องต่อ Backend** (เรียกผ่าน `<script>` ได้ตัวแปร `APPLE_CATALOG`) | **Web JavaScript SDK** | `data/exports/apple_unified_catalog.js` |
| 🛒 **ทำ Dropdown เลือกรุ่น/สี/ความจุ หน้าเว็บขายของ** (Tree Cascade Selector) | **Tree JSON** | `data/exports/apple_catalog_tree.json` |
| 🗄️ **ทำ Backend API (FastAPI, Express, Django)** ค้นหาเร็ว <5ms | **SQLite Database** | `data/exports/apple_catalog.db` *(ดู View: `v_unified_products`, `v_unified_variants`)* |
| 🚀 **นำเข้าฐานข้อมูลระดับองค์กร (MySQL, PostgreSQL, Supabase)** | **SQL Dump Script** | `data/exports/apple_catalog.sql` |
| 📊 **เปิดดูใน Microsoft Excel / Google Sheets** สำหรับฝ่ายการตลาดและจัดซื้อ | **Master CSV (UTF-8 BOM)** | `data/exports/apple_all_variants.csv` |
| 🔍 **ดูเฉพาะคลังรูปภาพ 4K เจาะลึก 6,242 ภาพ** (ชิป, ในกล่อง, กล้อง, AI) | **Deep Media JSON** | `data/exports/apple_deep_assets_catalog.json` |
| 🎨 **ไฟล์ภาพไดคัตโปร่งใส 100% ไร้พื้นหลังขาว** | **Transparent PNG Folder** | `data/images_transparent/{category}/{product}/{color}.png` |
| 📷 **ไฟล์ภาพต้นฉบับทางการ 4K Retina** | **Original JPG Folder** | `data/images/{category}/{product}/{color}.jpg` |

---

## 📂 โครงสร้างและแผนผังไดเรกทอรี (Directory Architecture)

```
projects/apple_scraper/
├── 📁 data/
│   ├── 📁 exports/                          <- 🌟 โฟลเดอร์ไฟล์ข้อมูลหลัก (Production Exports)
│   │   ├── apple_unified_catalog.json       <- มาสเตอร์ JSON รวมทุกฟิลด์ 100% (Single Source of Truth)
│   │   ├── apple_unified_catalog.js         <- Web SDK พร้อม Helper methods (window.APPLE_CATALOG)
│   │   ├── apple_catalog.db                 <- SQLite Relational DB (พร้อม Tables & Views)
│   │   ├── apple_catalog.sql                <- สคริปต์ SQL Dump สำหรับนำเข้า RDBMS อื่นๆ
│   │   ├── apple_all_variants.csv           <- ตาราง Master CSV ภาษาไทย (เปิดใน Excel ได้เลย)
│   │   ├── apple_catalog_tree.json          <- โครงสร้างต้นไม้ 4 ระดับ สำหรับหน้าสั่งซื้อ
│   │   └── apple_deep_assets_catalog.json   <- คลังข้อมูลภาพ 4K เจาะลึก 6,242 ภาพ
│   │
│   ├── 📁 images/                           <- ภาพถ่ายตัวเครื่องต้นฉบับทางการ (.jpg 2560x2560)
│   │   ├── iphone/ (iphone-16-pro, iphone-16, iphone-15, ฯลฯ)
│   │   ├── ipad/ (ipad-pro-m4, ipad-air-m2, ฯลฯ)
│   │   ├── mac/ (macbook-pro, macbook-air, imac, ฯลฯ)
│   │   └── watch/ (apple-watch-series-10, ultra-2, se)
│   │
│   ├── 📁 images_transparent/               <- ภาพถ่ายตัวเครื่องไดคัตโปร่งใส 100% (.png 4K Alpha)
│   │   └── [โครงสร้างหมวดหมู่และชื่อสีตรงกับ images/]
│   │
│   ├── 📁 images_deep/                      <- ภาพเจาะลึกความละเอียดสูงที่ดาวน์โหลดเก็บออฟไลน์
│   │   └── {product_id}/ (01_hardware.jpg, 02_box.jpg, 03_chip.jpg, ฯลฯ)
│   │
│   └── 📁 products_deep/                    <- ไฟล์ JSON เจาะลึกเฉพาะรายรุ่น 17 ไฟล์
│       ├── iphone-16-pro_deep_assets.json
│       ├── ipad-pro_deep_assets.json
│       └── ... (ครบ 17 รุ่น)
│
├── 🌐 catalog_preview.html                  <- หน้าเว็บพรีวิว Interactive Showcase & Deep Gallery
├── 📜 DATA_GUIDE.md                         <- คู่มือการนำข้อมูลไปใช้งานฉบับนี้
└── ⚙️ run.py                                 <- CLI ควบคุมระบบการดึงข้อมูลและจัดการฐานข้อมูล
```

---

## 🌳 ผังโครงสร้างข้อมูลระดับ Entity (Data Hierarchy)

ข้อมูลใน `apple_unified_catalog.json` จัดเรียงเป็นลำดับชั้นอย่างมีตรรกะชัดเจน ไม่ซ้ำซ้อน:

```
Category (4 หมวด: iphone, ipad, mac, watch)
   └── Product (17 สินค้าหลัก เช่น iPhone 16 Pro, MacBook Pro, iMac)
         ├── Sub-Models (รุ่นย่อยเจาะจง 40 รุ่น เช่น 16 Pro vs 16 Pro Max พร้อมมิติ/น้ำหนัก/จอ/กล้อง/แบต)
         ├── Finishes (สีตัวเครื่อง เช่น ดำ, ขาว, ไทเทเนียมธรรมชาติ พร้อมทั้งรูป JPG และ PNG โปร่งใส)
         ├── Variants (SKU ทางการ 343 รายการ พร้อมรหัส Part Number, ความจุ, ราคา และลิงก์ซื้อ)
         └── Deep Media (แกลเลอรีภาพทางการ 4K Retina แยก 6 หมวดหมู่อย่างเด็ดขาด)
               ├── 🎨 hardware_angles (มุมมองตัวเครื่องและสีสันทุกองศา)
               ├── 📦 in_the_box (ของในกล่อง บรรจุภัณฑ์ สายชาร์จถัก อะแดปเตอร์)
               ├── ⚡ chip_internal (ชิปเปลือย Die Shot, บอร์ด, แผ่นระบายความร้อน, กล้อง)
               ├── 🤖 apple_intelligence (หน้าจอ UI ฟีเจอร์ AI, Siri Glow, Clean Up)
               ├── 📸 camera_samples (ตัวอย่างภาพถ่ายจริงจากกล้อง 48MP, 5x, Macro)
               └── 💼 workflow_accessories (การใช้งานระดับโปร, ปากกา, คีย์บอร์ด, แอปพลิเคชัน)
```

---

## 📋 อภิธานศัพท์ข้อมูล (Data Dictionary & JSON Schema)

### ตัวอย่างโครงสร้าง Product ใน `apple_unified_catalog.json`:

```json
{
  "id": "iphone-16-pro",
  "category_id": "iphone",
  "name_th": "iPhone 16 Pro",
  "name_en": "iPhone 16 Pro",
  "chip": "ชิป A18 Pro พร้อม CPU 6-core...",
  "pricing": {
    "min_price_thb": 39900,
    "max_price_thb": 64900,
    "formatted_min": "฿39,900",
    "formatted_max": "฿64,900"
  },
  "hero_images": {
    "original_jpg": "data/images/iphone/iphone-16-pro/desert-titanium.jpg",
    "transparent_png": "data/images_transparent/iphone/iphone-16-pro/desert-titanium.png",
    "cdn_highres": "https://store.storeimages.cdn-apple.com/..."
  },
  "sub_models": [
    {
      "id": "iphone-16-pro",
      "name_th": "iPhone 16 Pro",
      "screen_size": "6.3\"",
      "dimensions_mm": "149.6 x 71.5 x 8.25 มม.",
      "weight_grams": "199 กรัม",
      "display_specs": "Super Retina XDR จอภาพ OLED ทั้งหน้าจอ...",
      "camera_specs": "ระบบกล้องระดับโปร (Fusion 48MP + อัลตร้าไวด์ 48MP + เทเล 5x)...",
      "battery_specs": "เล่นวิดีโอนานสูงสุด 27 ชั่วโมง...",
      "box_contents": "iPhone พร้อม iOS 18, สายชาร์จ USB-C..."
    }
  ],
  "finishes": [
    {
      "color_id": "desert-titanium",
      "name_th": "ไทเทเนียมทะเลทราย",
      "name_en": "Desert Titanium",
      "hex": "#C2A891",
      "images": {
        "original_jpg": "data/images/iphone/iphone-16-pro/desert-titanium.jpg",
        "transparent_png": "data/images_transparent/iphone/iphone-16-pro/desert-titanium.png",
        "cdn_highres": "https://store.storeimages.cdn-apple.com/..."
      }
    }
  ],
  "deep_media": {
    "total_images": 368,
    "summary_by_category": {
      "hardware_angles": 232,
      "in_the_box": 8,
      "chip_internal": 34,
      "apple_intelligence": 32,
      "camera_samples": 6,
      "workflow_accessories": 56
    },
    "gallery": [
      {
        "id": "iphone-16-pro-chip_internal-001",
        "category": "chip_internal",
        "category_th": "⚡ ชิปและวิศวกรรมสถาปัตยกรรมภายใน",
        "badge": "A18 Pro",
        "title_th": "ชิปประมวลผล A18 Pro สถาปัตยกรรม Apple Silicon",
        "description_th": "ภาพโครงสร้างวงจรรวมระดับนาโนเมตร...",
        "image_url": "https://www.apple.com/v/iphone/home/ck/images/overview/consider/chip__fh5j5on49p2e_large_2x.jpg",
        "resolution": "3840x2160 (Ultra HD 4K)",
        "aspect_ratio": "16:9"
      }
    ]
  }
}
```

---

## 💻 ตัวอย่างโค้ดการนำไปใช้งาน (Ready-to-Use Snippets)

### 1. JavaScript / HTML Frontend (Web Application)
โหลดไฟล์ `apple_unified_catalog.js` เพียงบรรทัดเดียว แล้วเรียกใช้ API ได้ทันที:

```html
<script src="data/exports/apple_unified_catalog.js"></script>

<script>
  // 1. ดึงสินค้าเดี่ยว
  const iphone16Pro = APPLE_CATALOG.getProduct('iphone-16-pro');
  console.log(iphone16Pro.name_th); // "iPhone 16 Pro"
  console.log(iphone16Pro.pricing.formatted_min); // "฿39,900"

  // 2. ดึงรูปภาพไดคัตโปร่งใส (Transparent PNG) ของสีไทเทเนียมทะเลทราย
  const finishes = iphone16Pro.finishes;
  const desertColor = finishes.find(f => f.color_id === 'desert-titanium');
  const transparentImgUrl = desertColor.images.transparent_png;

  // 3. ดึงรูปเจาะลึกเฉพาะหมวด "ชิปและวิศวกรรมภายใน"
  const chipAssets = APPLE_CATALOG.getDeepAssets('iphone-16-pro', 'chip_internal');
  console.log(`พบรูปชิปทั้งหมด ${chipAssets.length} รูป`);
</script>
```

---

### 2. Node.js Backend / API
```javascript
const fs = require('fs');
const catalog = JSON.parse(fs.readFileSync('data/exports/apple_unified_catalog.json', 'utf8'));

// หาสินค้าที่ราคาเริ่มต้นไม่เกิน 30,000 บาท
const affordableProducts = catalog.products.filter(p => p.pricing.min_price_thb <= 30000);
console.log(affordableProducts.map(p => `${p.name_th} (${p.pricing.formatted_min})`));
```

---

### 3. Python Backend (FastAPI / Flask / Django)
```python
import json
from pathlib import Path

catalog_path = Path("data/exports/apple_unified_catalog.json")
with open(catalog_path, "r", encoding="utf-8") as f:
    catalog = json.load(f)

def get_product_specs(product_id: str):
    product = next((p for p in catalog["products"] if p["id"] == product_id), None)
    if not product:
        return None
    return {
        "name": product["name_th"],
        "chip": product["chip"],
        "sub_models": product["sub_models"],
        "colors": [f["name_th"] for f in product["finishes"]],
        "starting_price": product["pricing"]["formatted_min"]
    }

print(get_product_specs("macbook-pro"))
```

---

### 4. SQLite / SQL Queries (10 คำสั่งยอดฮิต)
เปิดไฟล์ `data/exports/apple_catalog.db` แล้วรันได้ทันที:

```sql
-- 1. ดูสรุปสินค้าทั้งหมด พร้อมช่วงราคา จำนวนรุ่นย่อย และจำนวนรูปภาพ 4K
SELECT id, category_name_th, product_name, min_price_thb, max_price_thb, deep_assets_count 
FROM v_unified_products;

-- 2. หาสินค้ารุ่นที่ราคาไม่เกิน 25,000 บาท
SELECT product_name, sub_model_name, color_th, storage, formatted_price, transparent_png
FROM v_unified_variants
WHERE price_thb <= 25000;

-- 3. ดึงเฉพาะรูปภาพโครงสร้างภายในหรือภาพ Die ชิป ของทุกสินค้า
SELECT product_id, title_th, resolution, image_url
FROM product_deep_assets
WHERE category = 'chip_internal';

-- 4. ดึงเฉพาะภาพ "ของในกล่อง" (In-The-Box) ของ iPhone 16 Pro
SELECT title_th, description_th, image_url 
FROM product_deep_assets 
WHERE product_id = 'iphone-16-pro' AND category = 'in_the_box';

-- 5. ค้นหาสินค้าตามคำค้นหา เช่น "ไทเทเนียม" หรือ "M4"
SELECT product_name, color_th, storage, formatted_price 
FROM v_unified_variants 
WHERE chip LIKE '%M4%' OR color_th LIKE '%ไทเทเนียม%';
```

---

## 🛠️ การอัปเดตและสั่งการผ่าน CLI

หากต้องการรันเพื่อดึงข้อมูลใหม่ ลบพื้นหลัง หรือสร้างไฟล์ทั้งหมดใหม่ สามารถสั่งผ่านไฟล์ `run.py` ได้ง่ายๆ:

```bash
# 1. รันเมนูแบบ Interactive เพื่อเลือกทำงานทีละขั้นตอน
python3 projects/apple_scraper/run.py

# 2. อัปเดตและสร้างฐานข้อมูลมาสเตอร์ใหม่ทั้งหมด (JSON, SQLite, SQL, CSV)
python3 projects/apple_scraper/run.py build-db

# 3. รันเจาะลึกรูปภาพ 4K ทุกสินค้า ทั้ง 17 รุ่น
python3 projects/apple_scraper/run.py deep-assets

# 4. ประมวลผลลบพื้นหลังรูปภาพทั้งหมดเป็น Transparent PNG
python3 projects/apple_scraper/run.py remove-bg

# 5. รวมและจัดระเบียบ Master Unified Catalog ใหม่อัตโนมัติ
python3 projects/apple_scraper/src/services/unified_catalog_builder.py
```
