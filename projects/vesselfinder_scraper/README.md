# 🚢 VesselFinder Scraper & Live AIS Maritime Radar Suite

โมดูลแกะรอยและดึงข้อมูลการเดินเรือสมุทรแบบครบวงจรจาก **VesselFinder.com** โดยการถอดรหัสโปรโตคอลไบนารี (Reverse-Engineered Binary ArrayBuffer Protocol) ของ Web Worker ร่วมกับ JSON Telemetry API, 10-Sector Multi-Grid Scanner และ HTML Parser ทำให้สามารถดึงพิกัดเรือสดทั่วโลก เส้นทางเดินเรือย้อนหลัง (XOR Decoded) ฐานข้อมูลท่าเรือทั่วโลก และเรดาร์ตรวจจับเรือรบ/เรือตรวจการณ์ชายฝั่ง/เรือตำรวจน้ำครอบคลุม **น่านน้ำไทยทั้งหมดครบ 2 ฝั่งทะเล (อ่าวไทย 7 โซน + ทะเลอันดามัน 3 โซน รวม 10 โซน)** ได้โดยตรง รวดเร็ว และไม่ติด CAPTCHA

---

## 🔬 สถาปัตยกรรมโปรโตคอลที่ถอดรหัสได้ (Reverse-Engineered Endpoints)

| # | Endpoint | รูปแบบข้อมูล | หน้าที่และโครงสร้างข้อมูลที่สกัดได้ |
|---|---|---|---|
| **1** | `/api/pub/mp2?bbox=...&zoom=...` | **Binary ArrayBuffer** | กวาดเรดาร์ดึงเรือสดทุกลำใน Bounding Box (`lat`/`lon` หารด้วย `600,000`, `mmsi`, `name`, `heading_deg`, รหัสสีประเภทเรือ และขนาดตัวเรือเมื่อ `zoom > 13`) |
| **2** | `/api/pub/ms?name=<query>` | **Binary ArrayBuffer** | ค้นหาเรือทั่วโลกแบบ Real-time ได้ `imo` (`Int32`), `mmsi` (`Int32`), รหัสธงชาติ 2 ตัวอักษร, ชื่อเรือ และประเภทเรือ |
| **3** | `/api/pub/ml/<mmsi>` | **Binary ArrayBuffer** | ดึงพิกัดสดความละเอียดสูง 6 ตำแหน่ง (`lat`, `lon`), ความเร็ว `sog` (`Int16 / 10`), และสถานะดาวเทียม |
| **4** | `/api/pub/track/<mmsi>` | **XOR Binary (16B/pt)** | ดึงเส้นทางการเดินเรือย้อนหลัง ถอดรหัสด้วยคีย์ XOR `0x55555555` (`1431655765`) สำหรับ `lon`/`lat` และ `0x5555` (`21845`) สำหรับ `cog`/`sog` |
| **5** | `/api/pro/ports/v4/bin` | **Binary ArrayBuffer** | ถอดรหัสฐานข้อมูล **257 ประเทศ** และ **11,367 ท่าเรือทั่วโลก** (รวมท่าเรือไทย **49 แห่ง**) พร้อม `UN/LOCODE` และพิกัด `lat`/`lon` |
| **6** | `10-Sector Multi-Grid Radar` | **Multi-Source Radar** | กวาดเรดาร์น่านน้ำไทยครบ 2 ฝั่งทะเล 10 โซนย่อย (อ่าวไทย 16 ช่อง + ทะเลอันดามัน 3 ช่อง) ดึงเรือสด 1,350+ ลำ พร้อมตรวจจับเรือรบ เรือตรวจการณ์ และเรือตำรวจน้ำ 60+ ลำ |
| **7** | `/api/pub/click/<mmsi>` & `/vi2/<mmsi>` | **JSON API** | ดึงข้อมูลจำเพาะเรือ (IMO, GT, DWT, ปีที่สร้าง, กินน้ำลึก, รูปภาพเรือ HD) พร้อมท่าเรือต้นทาง (`ATD`) และท่าเรือปลายทาง (`ETA`) |
| **8** | `/api/pub/weather/at/<mmsi>` | **JSON API** | ดึงสภาพอากาศกลางทะเล ณ จุดที่เรือแล่นอยู่ (อุณหภูมิ °C, ความเร็วลม knots, ทิศทางลม, ความสูงคลื่นเมตร) |
| **9** | `/api/pub/ship/vu/<imo>/<year>` | **JSON API** | ดึงสถิติการเดินเรือรายปี (จำนวนครั้งเข้าเทียบท่า, ความเร็วเฉลี่ย/สูงสุด, รายชื่อท่าเรือและประเทศที่ไปเยือน) |
| **10** | `/vessels` & `/vessels/details/<imo>` | **HTML DOM** | สกัดตารางแคตตาล็อกเรือเดินสมุทรและตารางข้อมูลทางเทคนิคเชิงลึก (Engine, Builder, Classification, Dimensions) |

---

## 🚀 วิธีใช้งาน (Quick Start)

### 1. เรียกผ่าน Master CLI ที่ Root ของโปรเจกต์
```bash
# เปิดเมนู Interactive ของ VesselFinder
python3 run.py vessel

# สแกนเรดาร์เรือสดครบทุกช่องทั่วทะเลไทยทั้ง 2 ฝั่ง (อ่าวไทย 7 โซน + อันดามัน 3 โซน)
python3 run.py vessel radar

# สแกนเจาะจงเฉพาะอ่าวไทย (Full Gulf 16-Channel Sweep)
python3 run.py vessel radar gulf_of_thailand_all

# สแกนเจาะจงเฉพาะทะเลอันดามันฝั่งไทย (ระนอง พังงา ภูเก็ต กระบี่ ตรัง สตูล)
python3 run.py vessel radar andaman_th

# 🛡️ สแกนและกรองเฉพาะเรือรบ เรือตรวจการณ์ชายฝั่ง และเรือตำรวจน้ำ ทั่ว 2 ฝั่งทะเลไทย
python3 run.py vessel patrol

# 📸 กวาดและดาวน์โหลดรูปถ่ายเรือ HD ทั้งหมดลงเครื่องแบบมัลติเธรด (Multi-Photo Harvester)
python3 run.py vessel photos

# ปลดล็อกและสแกนเรือสดในท่าเรือแหลมฉบัง (THLCH001) หรือท่าเรือกรุงเทพ (THBKK001)
python3 run.py vessel port THLCH001

# ค้นหาเรือทั่วโลกด้วยชื่อเรือ / IMO / MMSI
python3 run.py vessel search evergreen

# เจาะลึกข้อมูลเรือรายลำ 360° (พร้อมถอดรหัสเส้นทาง XOR Track + โหลดรูปเรือ HD)
python3 run.py vessel ship 352002065

# ดึงฐานข้อมูลท่าเรือทั่วโลก 11,367 แห่ง และท่าเรือไทย 49 แห่ง
python3 run.py vessel ports th

# รันดึงข้อมูลครบวงจรทุกโหมดในคำสั่งเดียว
python3 run.py vessel all
```

### 2. รันเป็น Standalone Microservice (ไม่ต้องใช้ Docker)
```bash
# สตาร์ท API Microservice สดๆ ที่พอร์ต 8000
python3 run.py vessel api

# หรือระบุพอร์ตที่ต้องการ (เช่น พอร์ต 8088)
python3 run.py vessel api 8088
```

### 3. แพ็กและรันด้วย Docker (Standalone Container นำไปต่อที่ไหนก็ได้ 100%)
```bash
# เข้าโฟลเดอร์โปรเจกต์นี้
cd projects/vesselfinder_scraper

# สั่งสร้างและสตาร์ทตู้ Docker ขึ้นมาทำงานเบื้องหลัง 24/7
docker compose up -d

# ดูบันทึกการทำงานสดใน Docker
docker compose logs -f

# หยุดการทำงาน
docker compose down
```

---

## 🌐 ตาราง Endpoints ของ Microservice API (Zero-Auth & Universal CORS)
> 🔓 **ไม่ต้องใช้ API Key / ไม่ต้องมี Header ความปลอดภัยใดๆ ทั้งสิ้น**: ยิงขอข้อมูลจาก React, Vue, Flutter, Node.js, Python, PHP, cURL หรือ Postman ได้ทันที รองรับ `CORS: *` 100%!

| Method | Endpoint | หน้าที่และการตอบกลับ | ตัวอย่าง Response เวลาตอบสนอง |
|---|---|---|:---:|
| `GET` | `/health` | ตรวจสอบสถานะการทำงานของ Microservice, จำนวนเรือในหน่วยความจำ และเวลาอัปเดตล่าสุด | `< 2 ms` |
| `GET` | `/` | แสดงหน้าเว็บ **Interactive Maritime Radar Studio** แสดงหมุดเรือสดบนแผนที่เรดาร์ | `< 5 ms` |
| `GET` | `/docs` | หน้า **Interactive Swagger UI** ทดสอบกดเรียก API ได้ทุกเส้นทางผ่านเบราว์เซอร์ | Web UI |
| `GET` | `/api/radar` | ดึงข้อมูลเรือสดทั่วไทย 10 โซน (1,355 ลำ) ตอบกลับทันทีจาก In-Memory Cache (ใส่ `?refresh=true` เมื่อต้องการกวาดสด) | `< 15 ms` |
| `GET` | `/api/patrol` | ดึงข้อมูลเฉพาะ **เรือรบ • เรือตรวจการณ์ • ตำรวจน้ำ • กู้ภัย SAR • เรือนำร่อง** (62 ลำ) | `< 10 ms` |
| `GET` | `/api/fishing` | ดึงข้อมูลเฉพาะ **เรือประมงไทย** กำลังออกหาปลาทั่วประเทศ (273 ลำ) | `< 10 ms` |
| `GET` | `/api/vessel/{mmsi}` | เจาะลึกเรือรายลำ: ข้อมูลสเปกเรือ, พิกัดสด, ท่าเรือต้นทาง-ปลายทาง, สภาพอากาศกลางทะเล, เส้นทางย้อนหลัง XOR Track และแกลเลอรีรูปถ่าย | `< 800 ms` |
| `GET` | `/api/vessel/{mmsi}/photo` | สตรีมไฟล์ภาพถ่ายเรือ HD (`image/jpeg`) ตรงลงหน้าจอ ใส่ `?index=1, 2...` เลือกลำดับภาพได้ | `< 10 ms` |
| `GET` | `/api/vessel/{mmsi}/photos` | ดึงแกลเลอรีรูปถ่ายเรือทุกลำดับภาพ (Full Photos Array) พร้อมลิงก์ดาวน์โหลด และขนาดไฟล์ | `< 5 ms` |
| `GET` | `/api/photos/stats` | ดูสรุปสถิติรูปถ่ายเรือทั้งหมดในระบบ: จำนวนไฟล์บนดิสก์, พื้นที่ความจุ MB, จำนวนเรือที่มีรูป | `< 5 ms` |
| `POST` | `/api/photos/harvest` | สั่งให้ระบบกวาดดาวน์โหลดรูปถ่ายเรือแบบขนาน 8 Threads ทั้งหมดทันที | Background |
| `GET` | `/api/ports?country=th` | ดึงรายชื่อท่าเรือไทย 49 แห่ง (หรือใส่ `country=all` สำหรับท่าเรือทั่วโลก 11,367 แห่ง) | `< 5 ms` |
| `GET` | `/api/search?q={name}` | ค้นหาเรือทั่วโลกแบบ Real-time ด้วยชื่อเรือ / IMO / MMSI | `< 300 ms` |

---

### 4. เปิดหน้า Interactive Maritime Radar Studio
เปิดไฟล์ [`vesselfinder_studio.html`](./vesselfinder_studio.html) บนเบราว์เซอร์เพื่อสำรวจแผนที่เรดาร์เดินเรือสดทั่วทะเลไทย ท่าเรือไทย 49 แห่ง เส้นทางเดินเรือย้อนหลัง และการ์ดข้อมูลเรือพร้อมรูปภาพ HD

---

## 📂 โครงสร้างข้อมูลที่ส่งออก (`data/`)
- `data/json/live_radar_thailand_all_seas.json`: ข้อมูลเรือสดทั่วทะเลไทย 10 โซน (1,350+ ลำ)
- `data/exports/vessels_thailand_all_seas.csv`: ตารางข้อมูลเรือสดทั่วทะเลไทยพร้อมเปิดใน Excel (1,350+ แถว)
- `data/json/patrol_and_military_vessels.json`: บันทึกข้อมูลเรือรบ เรือตรวจการณ์ และเรือตำรวจน้ำทั่วไทย (60+ ลำ)
- `data/exports/patrol_and_military_vessels.csv`: ตารางเรือตรวจการณ์และเรือรบทั่วไทย (60+ แถว)
- `data/json/thailand_ports.json` & `global_ports_all.json`: ฐานข้อมูลท่าเรือไทย 49 แห่ง และทั่วโลก 11,367 แห่ง
- `data/exports/radar_thailand_all_seas.geojson`: ไฟล์แผนที่มาตรฐาน GeoJSON (Points + Voyage LineStrings)
- `data/exports/vesselfinder_live_bundle.js`: JavaScript SDK สำหรับหน้าเว็บ `vesselfinder_studio.html`
- `data/images/`: รูปถ่ายเรือเดินสมุทรความละเอียดสูง (`.jpg`)

