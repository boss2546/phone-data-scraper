# 📸 Instagram Scraper & Media Intelligence

โมดูลดึงข้อมูลโปรไฟล์ สถิติ และโพสต์รูปภาพ/แคปชันจาก Instagram ผ่าน Internal Web API

## ✨ ความสามารถหลัก (Features)
- **Profile Analytics**: สกัดชื่อผู้ใช้, Followers, Following, Bio, Verification badge
- **Post Extractor**: สกัดแคปชัน, จำนวนไลก์, คอมเมนต์, Timestamp และรหัส Shortcode
- **Carousel / Album Extractor**: ดึงรูปภาพหลายรูปในโพสต์เดียว (GraphSidecar)
- **Automatic Media Downloader**: ดาวน์โหลดรูปภาพทั้งหมดจัดเก็บแยกโฟลเดอร์ตามบัญชีผู้ใช้

## 🚀 วิธีใช้งาน (Usage)
```bash
# ใช้งานผ่านเมนูแบบ Interactive
python3 run.py

# ดึงข้อมูลจาก Username ตรง
python3 run.py "username"

# ดึงข้อมูลจาก URL
python3 run.py "https://www.instagram.com/username/"
```
