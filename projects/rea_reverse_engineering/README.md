# 🔬 REA Reverse Engineering Suite (โมดูลย้อนรอยและวิเคราะห์แอปพลิเคชัน)

> **"See a feature you like. Understand how it works, down to the binary level."**  
> เครื่องมือวิเคราะห์โครงสร้างแอปพลิเคชัน, Binary, Metadata และ Network Har ขับเคลื่อนโดย [morluto/rea](https://github.com/morluto/rea) (`rea-agents` v6.4.0)

---

## 📖 แนะนำ REA (Reverse Engineer Anything)

**REA** เป็นเครื่องมือและ MCP Server ระดับสากลที่ถูกออกแบบมาเพื่อช่วยให้นักพัฒนาและวิศวกรซอฟต์แวร์สามารถ **"ทำความเข้าใจการทำงานเบื้องลึกของแอปพลิเคชัน"** โดยไม่ต้องเดา:
- วิเคราะห์โครงสร้างไบนารีระดับ Mach-O, ELF, PE (Code Signatures, Certs, Architecture slices)
- ดึงข้อมูล Apple Info.plist และ Bundle configuration
- ตรวจสอบ Dynamic Library Dependencies (`LC_LOAD_DYLIB` / dyld load-path)
- ถอดรหัสและวิเคราะห์ไฟล์บันทึก Network Capture (`.har` และ mitmproxy)
- ทำหน้าที่เป็น MCP Server (170+ Tools) เชื่อมต่อกับ AI Agent

---

## 📂 โครงสร้างภายในโมดูล

```
projects/rea_reverse_engineering/
├── README.md               # เอกสารแนะนำการใช้งานภาษาไทย
├── requirements.txt        # รายการแพ็กเกจที่เกี่ยวข้อง
├── run.py                  # CLI Launcher แบบ Interactive และส่งคำสั่งด่วน
├── config/
│   └── config.json         # การตั้งค่าเป้าหมายทดสอบและโหมดการแสดงผล
├── src/
│   └── rea_runner.py       # Python Wrapper คลาส ReaRunner สำหรับสั่งการ REA
├── data/
│   ├── samples/            # ไฟล์ตัวอย่างสำหรับการทดสอบ (เช่น sample_api.har)
│   └── results/            # โฟลเดอร์เก็บผลลัพธ์การวิเคราะห์รูปแบบ JSON
└── tests/
    └── test_rea.py         # Unit Tests ตรวจสอบความถูกต้องของระบบ
```

---

## 🚀 วิธีการใช้งาน

### 1. เรียกผ่าน Master Runner ที่ Root โฟลเดอร์
```bash
python3 run.py rea
# หรือ
python3 run.py rea test       # สั่งรันการทดสอบ Diagnostics ทันที
python3 run.py rea doctor     # ตรวจสอบสถานะ MCP Server
```

### 2. เรียกผ่านโมดูลโดยตรง
```bash
cd projects/rea_reverse_engineering

# เปิดเมนู Interactive แบบมีเมนูให้เลือก
python3 run.py

# คำสั่งด่วนแบบ CLI
python3 run.py signature /bin/ls                     # ตรวจสอบ Digital Signature & Codesign
python3 run.py arch /bin/ls                          # ดูสถาปัตยกรรม CPU (x86_64, arm64e)
python3 run.py plist /System/Applications/Calculator.app # ถอดรหัส Info.plist
python3 run.py dylib /bin/ls                         # ตรวจสอบ Dynamic Library Linkages
python3 run.py har data/samples/sample_api.har       # วิเคราะห์ Network HAR
python3 run.py doctor                                # ตรวจสอบ MCP Server Health
python3 run.py test                                  # รัน Diagnostics ตรวจสอบทุกฟังก์ชัน
```

---

## 🧪 ตัวอย่างผลลัพธ์การวิเคราะห์จริง

### ตัวอย่าง: การวิเคราะห์ Codesign (`inspect-signature /bin/ls`)
```yaml
identifier: com.apple.ls
format: Mach-O universal (x86_64 arm64e)
authorities:
  - Software Signing
  - Apple Code Signing Certification Authority
  - Apple Root CA
designated_requirement: 'identifier "com.apple.ls" and anchor apple'
```

### ตัวอย่าง: การตรวจจับ Slices CPU (`list-architectures /bin/ls`)
```yaml
architectures:
  - name: x86_64 (Offset: 16384, Size: 48128 bytes)
  - name: arm64e (Offset: 65536, Size: 89088 bytes)
```

---

## 🛡️ มาตรฐานความปลอดภัยและข้อกำหนด
- โมดูลนี้มุ่งเน้นการศึกษาเชิงสถาปัตยกรรม (Architectural understanding) และการวิเคราะห์โครงสร้างไฟล์ไบนารี/เน็ตเวิร์กที่ได้รับอนุญาต
- การวิเคราะห์เครือข่ายกระทำกับไฟล์ Local HAR แบบออฟไลน์ (ไม่ส่ง request จริงออกสู่ภายนอก)
