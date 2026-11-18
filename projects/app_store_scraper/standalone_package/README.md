# 🍎 Apple App Store Media Scraper (Portable AI-Ready Suite)

ชุดเครื่องมือสกัดรูปภาพและข้อมูลจาก **Apple App Store** แบบพกพา (Standalone)
พร้อมนำไปหยอดใส่โปรเจกต์อื่นๆ หรือส่งให้ AI ผู้ช่วย (Cursor, Claude, ChatGPT, Antigravity) ใช้งานได้ทันที **ไม่ต้องลง Library เพิ่มเติมแม้แต่ตัวเดียว (Zero-dependency Python)**

---

## 🚀 รันด่วนใน 1 วินาที:
```bash
# ดึงภาพหน้าจอระดับ Retina 4K ของแอป Netflix
python3 appstore_scraper.py "Netflix"

# ดึงเฉพาะข้อมูล Metadata JSON แบบรวดเร็ว
python3 appstore_scraper.py "ChatGPT" --no-media --json

# รันไฟล์ตัวอย่าง
python3 demo.py
```

## 📖 คู่มือสำหรับส่งให้ AI ใช้งาน:
สามารถส่งไฟล์ `AI_INSTRUCTIONS.md` ให้ AI ในโปรเจกต์ใหม่ เพื่อให้ AI เข้าใจวิธีสั่งงานและประมวลผลข้อมูลได้ทันที 100%
