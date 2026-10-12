# 🛍️ CompAsia Scraper & Data Pipeline

โมดูลดึงข้อมูลสินค้าสมาร์ทโฟนมือสองจาก CompAsia (Thailand) ผ่าน Shopify Products JSON API

## ✨ ความสามารถหลัก (Features)
- **Shopify Catalog Ingestion**: ดึงข้อมูลสินค้าทุกชิ้นแบบ Paginated จาก API ทางการ
- **Variant Extractor**: สกัดแยกรุ่นย่อย สี ความจุ ราคา เกรดสินค้า และสถานะสต็อก
- **Battery & Warranty Parsing**: สกัดสุขภาพแบตเตอรี่ (%) และระยะเวลารับประกันสินค้า
- **Multi-threaded Media Downloader**: ดาวน์โหลดรูปภาพสินค้าทุกมุมมองเก็บลงในเครื่อง

## 🚀 วิธีใช้งาน (Usage)
```bash
# ใช้งานผ่านเมนูแบบ Interactive
python3 run.py

# ดึงเฉพาะรายการลิงก์
python3 run.py links

# สกัดข้อมูลละเอียดและรูปภาพ
python3 run.py extract

# รันดึงใหม่ทั้งหมด
python3 run.py all
```
