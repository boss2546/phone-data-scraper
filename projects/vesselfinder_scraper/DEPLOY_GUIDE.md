# 🚀 คู่มือการนำ VesselFinder Microservice ไปใช้งานจริงในระดับ Production

คู่มือนี้สรุปขั้นตอนการนำโมดูล **VesselFinder Standalone Maritime Radar Microservice** ไปติดตั้ง ใช้งาน และเชื่อมต่อกับระบบอื่นในโปรดักชันจริงอย่างละเอียด 100%

---

## 📦 1. ส่วนประกอบในแพ็กเกจส่งมอบ (`vesselfinder_microservice.zip`)

เมื่อแตกไฟล์ซิปออกมา จะได้โครงสร้างโปรเจกต์ที่สมบูรณ์ในตัวเอง (Self-contained) ดังนี้:

```text
vesselfinder_scraper/
├── Dockerfile                      # อิมเมจ Docker พร้อมระบบ Healthcheck
├── docker-compose.yml              # คอนฟิก Docker พร้อม Log Rotation & Named Volume
├── requirements.txt                # รายการไลบรารี Python (FastAPI, Uvicorn, Requests)
├── .env.example & .env             # ตัวแปรสภาพแวดล้อม (Port 8088, โซน, เธรด)
├── start.sh                        # สคริปต์สั่งรันอัตโนมัติ (ตรวจจับ Docker หรือ Python ให้เอง)
├── stop.sh                         # สคริปต์สั่งหยุดทำงานอย่างปลอดภัย
├── test.sh                         # สคริปต์ตรวจสุขภาพและทดสอบ API ทุกเส้นทาง
├── vesselfinder.service            # ไฟล์คอนฟิก Systemd Service สำหรับ Linux VPS
├── nginx_vesselfinder.conf.example # คอนฟิก Reverse Proxy NGINX ต่อกับโดเมน/SSL
├── run.py                          # Master CLI ควบคุมระบบ (เรดาร์, ท่าเรือ, กวาดรูป, API)
├── vesselfinder_studio.html        # หน้าเว็บแสดงผล Interactive Radar Studio
├── config/                         # การตั้งค่าโซนน่านน้ำไทย 10 โซน และหัวอ่านไบนารี
├── src/
│   ├── api.py                      # เซิร์ฟเวอร์ FastAPI Microservice (Zero-Auth & CORS *)
│   ├── scrapers/                   # โมดูลถอดรหัส ArrayBuffer & XOR Tracks
│   └── services/
│       ├── photo_harvester.py      # เครื่องยนต์กวาดภาพถ่ายเรือ HD & Multi-Gallery (8 Threads)
│       └── storage_service.py      # โมดูลส่งออก JSON, CSV, GeoJSON, JS SDK
└── data/
    ├── images/                     # 📸 คลังภาพถ่ายเรือ HD จริง (163 ไฟล์ พร้อมใช้ทันที)
    ├── json/                       # 💾 ฐานข้อมูลเรือสด 1,220 ลำ, ท่าเรือโลก 11,367 แห่ง
    └── exports/                    # 📊 ไฟล์ส่งออก Excel CSV, GeoJSON, JS SDK
```

---

## 🛠️ 2. วิธีนำไปติดตั้งและรันใช้งานจริง (3 รูปแบบ)

### 🐳 แบบที่ 1: รันผ่าน Docker Compose (แนะนำที่สุดสำหรับ Production)
เหมาะสำหรับนำไปวางบน Server, Cloud VPS, หรือเครื่องใดก็ได้ที่มี Docker ติดตั้งอยู่:

```bash
# 1. แตกไฟล์ซิปและเข้าไปที่โฟลเดอร์
unzip vesselfinder_microservice.zip
cd vesselfinder_scraper

# 2. สั่งรันขึ้นมาทำงานเบื้องหลัง 24/7
docker compose up -d

# 3. ตรวจสอบสถานะคอนเทนเนอร์
docker compose ps

# 4. ดู Log การทำงานสด
docker compose logs -f

# 5. สั่งหยุดการทำงาน
docker compose down
```

---

### 🐍 แบบที่ 2: รันด้วยคำสั่งสคริปต์เดียว (`./start.sh` - รองรับทั้ง Mac / Linux / Windows WSL)
เหมาะสำหรับรันตรงบนเครื่องโดยไม่ต้องเปิด Docker:

```bash
# สั่งรันผ่านสคริปต์อัจฉริยะ (จะเช็ค venv และติดตั้ง dependencies ให้เอง)
./start.sh

# หรือระบุพอร์ตเองโดยตรงผ่านคำสั่ง Python:
python3 run.py api 8088
```

---

### 🐧 แบบที่ 3: ติดตั้งเป็น Background Service บน Linux VPS (Ubuntu / Debian Systemd)
สำหรับรันให้ทำงานอัตโนมัติตอนเปิดเครื่อง Server:

```bash
# 1. ย้ายโฟลเดอร์ไปที่ /opt
sudo mv vesselfinder_scraper /opt/

# 2. ติดตั้งไฟล์ Service
sudo cp /opt/vesselfinder_scraper/vesselfinder.service /etc/systemd/system/

# 3. โหลดและสั่งเปิดระบบ
sudo systemctl daemon-reload
sudo systemctl enable --now vesselfinder

# 4. ตรวจสอบสถานะการทำงาน
sudo systemctl status vesselfinder
```

---

## 🧪 3. การทดสอบความสมบูรณ์หลังติดตั้ง (1-Click Verification)

เพียงรันคำสั่งเดียว ระบบจะยิงตรวจสุขภาพและทดสอบ API ทุกเส้นทางให้ทันที:

```bash
./test.sh
```

ผลลัพธ์ที่ได้จะเป็นสีเขียวผ่านทุกจุด 100%:
```text
  • Testing Service Health (/health)...         PASS (HTTP 200)
  • Testing Swagger Docs (/docs)...             PASS (HTTP 200)
  • Testing Live Radar Cache (/api/radar)...     PASS (HTTP 200)
  • Testing Patrol & Navy Fleet (/api/patrol)... PASS (HTTP 200)
  • Testing Fishing Vessels (/api/fishing)...    PASS (HTTP 200)
  • Testing Photo Gallery Stats (/api/photos)... PASS (HTTP 200)
  • Testing HD Photo Stream (/api/vessel/...)... PASS (HTTP 200)
```

---

## 🌐 4. การเชื่อมต่อไปยังระบบอื่น (Integration Guide)

ระบบนี้ออกแบบตามหลัก **Zero-Auth & Universal CORS (`*`)** ทำให้เชื่อมต่อง่ายที่สุด ไม่ต้องตั้งค่า API Key หรือ Token ใดๆ ทั้งสิ้น:

### 1) เชื่อมต่อผ่าน Frontend (React / Vue / Next.js / HTML)
```javascript
// ดึงข้อมูลเรือสดทั้งหมดในน่านน้ำไทย
fetch("http://localhost:8088/api/radar")
  .then(res => res.json())
  .then(data => console.log("เรือสดในน่านน้ำไทย:", data.vessels));

// แสดงภาพถ่ายเรือ HD ลำแรก
const imgUrl = "http://localhost:8088/api/vessel/567002940/photo?index=1";
```

### 2) เชื่อมต่อผ่าน Backend (Node.js / Express)
```javascript
const axios = require('axios');

async function getThaiNavyShips() {
  const response = await axios.get('http://localhost:8088/api/patrol');
  console.log(`พบเรือตรวจการณ์และเรือรบ: ${response.data.count} ลำ`);
  return response.data.vessels;
}
```

### 3) เชื่อมต่อผ่าน Python
```python
import requests

# ดึงข้อมูลเรือประมงไทยทั้งหมด
r = requests.get("http://localhost:8088/api/fishing")
fishing_fleet = r.json()["vessels"]
print(f"จำนวนเรือประมงไทย: {len(fishing_fleet)} ลำ")
```

---

## 🛡️ 5. ข้อแนะนำในการดูแลรักษาระบบ (Ops & Maintenance)

1. **การบันทึก Log ไม่ล้นฮาร์ดดิสก์ (Log Rotation)**:
   ใน `docker-compose.yml` มีการจำกัดขนาด Log ไม่เกิน 10MB และเก็บย้อนหลังสูงสุด 3 ไฟล์ (`max-size: "10m"`, `max-file: "3"`) ทำให้เซิร์ฟเวอร์ไม่มีวันดิสก์เต็มจาก Log แน่นอนค่ะ
2. **การสำรองข้อมูลภาพและฐานข้อมูล**:
   ข้อมูลเรือสดและภาพถ่ายทั้งหมดอยู่ในโฟลเดอร์ `data/` เพียงแค่ Backup โฟลเดอร์ `data/` ก็จะได้ข้อมูลครบถ้วน 100% เสมอค่ะ
3. **การสั่งกวาดรูปถ่ายเพิ่มเติม**:
   เมื่อมีเรือใหม่ๆ เข้ามา สามารถสั่งกวาดรูปถ่ายเพิ่มได้ตลอดเวลาผ่านคำสั่ง:
   ```bash
   python3 run.py photos
   ```
   หรือยิงผ่าน API: `POST http://localhost:8088/api/photos/harvest`

