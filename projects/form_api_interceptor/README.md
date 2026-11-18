# 🎯 Form & API Interceptor — ชุดดักจับ API & บันทึกโครงสร้างฟอร์มเพื่อสร้างบอทอัตโนมัติ

> ส่วนขยาย Google Chrome (Manifest V3) และชุดเครื่องมือ Python อัจฉริยะสำหรับดักจับ Network API (Headers, Payload, Response) ควบคู่กับการบันทึกแผนที่ DOM Elements ทุกฟิลด์ที่มนุษย์กรอกจริง เพื่อนำไปสร้างระบบบอทอัตโนมัติ (Python Direct API, Playwright, และ AI Browser Agents)

---

## 🌟 จุดเด่นและสถาปัตยกรรม 2 เส้นทาง (Dual-Engine Automation Strategy)

เมื่อคุณเปิดโหมดบันทึกและกรอกฟอร์มจริงบนหน้าเว็บ ระบบจะทำงาน **2 เลเยอร์พร้อมกัน**:

```
                       [ 🌐 หน้าเว็บเป้าหมาย / ฟอร์มที่กรอก ]
                                      │
                                      ▼
             ┌──────────────────────────────────────────────────┐
             │  🧩 Chrome Extension: Form & API Interceptor     │
             └───────────────┬──────────────────┬───────────────┘
                             │                  │
                [ เส้นทางหลัก: Direct API ]     [ เส้นทางสำรอง: DOM Elements ]
                             │                  │
                             ▼                  ▼
                    ดัก fetch & XHR สดๆ        บันทึก CSS Selector, XPath,
                    เก็บ Headers, Auth,         Label, Value, Placeholder,
                    Payload JSON & Response     และปุ่ม Submit ของทุกช่อง
                             │                  │
                             ▼                  ▼
                    🐍 โค้ด Python Requests      🎭 สคริปต์ Playwright &
                    (ยิงตรง เร็ว ไม่ต้องเปิดจอ)    🤖 AI Browser Agent Schema
```

1. **🚀 เส้นทางหลัก (Primary Route — Direct API)**:
   - ดักจับ `fetch` และ `XMLHttpRequest` ขาออกขณะที่หน้าเว็บทำการส่งข้อมูล
   - ดัก `Authorization: Bearer ...`, `Cookie`, `X-CSRF-Token` และ Request Body
   - **ข้อดี**: แปลงเป็นสคริปต์ Python (`requests`) หรือ cURL ยิงตรงเข้า Server ปลายทางได้ทันที รวดเร็วระดับมิลลิวินาที ไม่ต้องเปิดหน้าเว็บ

2. **🛡️ เส้นทางสำรอง (Fallback Route — Browser UI & AI Automation)**:
   - เหมาะสำหรับกรณีที่ **ยิง API ตรงไม่ได้** (เช่น ติด Cloudflare WAF, Google reCAPTCHA, Cloudflare Turnstile, หรือ Dynamic Signatures ที่เปลี่ยนทุกครั้ง)
   - บันทึกพิกัดของทุก Input Element (Unique CSS Selector, Absolute/Relative XPath, Name, ID, Label) และพฤติกรรมการกรอก
   - **ข้อดี**: แปลงเป็นสคริปต์ **Playwright** เปิดเบราว์เซอร์อัตโนมัติกรอกฟอร์มเหมือนมนุษย์ 100% หรือส่งออกเป็น **JSON Schema สำหรับ AI Browser Agents** (เช่น Skyvern, Browser-use, Claude Computer Use) ไปสั่งงานต่อได้ทันที

---

## 📦 วิธีติดตั้ง Extension บน Google Chrome

1. เปิดเบราว์เซอร์ **Google Chrome**
2. ไปที่หน้าจัดการส่วนขยาย:
   ```text
   chrome://extensions/
   ```
3. เปิดสวิตช์ **"Developer mode" (โหมดนักพัฒนา)** ที่มุมขวาบน
4. กดปุ่ม **"Load unpacked" (โหลดส่วนขยายที่คลายการบีบอัดแล้ว)**
5. เลือกโฟลเดอร์:
   ```text
   projects/form_api_interceptor/extension/
   ```
6. ไอคอน 🎯 **Form & API Interceptor** จะปรากฏบน Toolbar ของ Chrome พร้อมใช้งานทันทีค่ะ!

---

## ⚡ วิธีใช้งานแบบ Step-by-Step

### ขั้นตอนที่ 1: เริ่มต้นการดักจับ
1. เปิดหน้าเว็บที่ต้องการกรอกฟอร์ม หรือเปิดห้องแล็บทดสอบด้วยคำสั่ง:
   ```bash
   python3 run.py test
   ```
2. คลิกที่ไอคอน 🎯 ของ Extension บนแถบเครื่องมือ
3. กดปุ่ม **"🔴 เริ่มบันทึก (Start Recording)"** (จะมีแท็ก REC สีแดงกะพริบที่มุมจอ)

### ขั้นตอนที่ 2: กรอกฟอร์มจริง
- กรอกข้อมูลลงในฟอร์มอย่างเป็นธรรมชาติ (ชื่อ, อีเมล, ตัวเลือก, หมายเหตุ)
- กดปุ่ม **"Submit / บันทึก"** บนหน้าเว็บจริง

### ขั้นตอนที่ 3: ตรวจสอบผลลัพธ์และสร้างโค้ดอัตโนมัติ
- คลิกที่แถบ REC มุมล่างขวา หรือคลิกไอคอน Extension แล้วกด **"📖 เปิดสตูดิโอเต็มจอ (Side Panel)"**
- จะพบแท็บควบคุม 4 ส่วน:
  - 🌐 **Network API**: ดู Headers, Payload, และ Response ที่ส่งออกไป พร้อมปุ่ม **"🚀 ทดสอบยิง (Replay)"**
  - 📝 **ฟอร์ม & Elements**: ดูรายชื่อฟิลด์, Selector, XPath และปุ่ม **"⚡ สั่งกรอกหน้านี้ซ้ำ (Re-Fill)"**
  - 🤖 **เจนโค้ดบอท (Code)**: เลือกรูปแบบที่ต้องการ แล้วกด **"📋 คัดลอกโค้ด"**
    - 🐍 Python Script (`requests`)
    - 🎭 Playwright Python Browser Automation
    - 🤖 AI Agent / Skyvern Schema (JSON)
    - ⚡ cURL Command
    - 🌐 Node.js Fetch

---

## 🔌 การเชื่อมต่อ Local Webhook Server (บันทึกอัตโนมัติลงเครื่อง)

หากต้องการให้ Extension ส่งข้อมูล JSON ที่ดักจับได้ตรงเข้าเครื่องคอมพิวเตอร์ของคุณอัตโนมัติ:

1. สตาร์ท Local Webhook Server:
   ```bash
   python3 run.py server
   ```
   (เซิร์ฟเวอร์จะเปิดรอรับข้อมูลที่ `http://127.0.0.1:8091/api/capture`)
2. ในหน้า Side Panel ของ Extension ให้ไปที่แท็บ **"💾 ประวัติ & ตั้งค่า"**
3. ติ๊กเปิดสวิตช์ **"ส่งออโต้"** แล้วกด **"💾 บันทึกการตั้งค่า"**
4. ทุกครั้งที่คุณกด "หยุดบันทึก" ข้อมูลจะถูกส่งมาบันทึกลง:
   - `data/captures/<session_id>.json` (ข้อมูลดิบ)
   - `data/exports/<session_id>_direct_api.py` (สคริปต์ Python API)
   - `data/exports/<session_id>_playwright_bot.py` (สคริปต์บอท Playwright)

---

## 🎛️ คำสั่งควบคุมผ่าน Master CLI (`run.py`)

```bash
# เปิดเมนูแบบ Interactive
python3 run.py

# เปิดหน้าห้องแล็บทดสอบ
python3 run.py test

# สตาร์ท Local Webhook Server (Port 8091)
python3 run.py server

# แปลง Session JSON ล่าสุดเป็นสคริปต์ Python ทันที
python3 run.py generate

# ดูคำแนะนำการติดตั้ง Extension
python3 run.py install
```

---

## 📘 เอกสารอ้างอิง API (API Documentation)
* [Plane API Integration & Reference Manual (ฉบับสมบูรณ์)](./docs/PLANE_API_DOCUMENTATION.md) — คู่มือการเชื่อมต่อ Plane API v1 อย่างละเอียด พร้อมรายชื่อ UUID States, Labels, Priority, โครงสร้าง Request/Response JSON และ Production-Ready Python Client

