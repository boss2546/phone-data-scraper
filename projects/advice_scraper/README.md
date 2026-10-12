# 💻 Advice Scraper & Media Pipeline

โมดูลดึงข้อมูลสินค้าไอที สมาร์ทโฟน และอุปกรณ์เสริมจาก Advice.co.th

## ✨ ความสามารถหลัก (Features)
- **JSON-LD Schema Extractor**: สกัดข้อมูลมาตรฐาน Schema.org (SKU, Brand, Price, Availability)
- **HD Image Gallery**: สกัดและดาวน์โหลดรูปสินค้าขนาด 700px ความละเอียดสูงจาก CDN
- **Key Specs Parser**: สกัดสเปกหลัก (CPU, RAM, Storage) อัตโนมัติ
- **CSV & JSON Datasets**: ส่งออกข้อมูลอัตโนมัติพร้อมใช้งาน

## 🚀 วิธีใช้งาน (Usage)
```bash
# ใช้งานผ่านเมนูแบบ Interactive
python3 run.py

# ดึงข้อมูลจาก URL ตรง
python3 run.py "https://www.advice.co.th/product/smart-phone/..."
```
