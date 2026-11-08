# 🎬 Universal Media Grabber — Chrome Extension (PNG / JPG / MP4)

ส่วนขยายเบราว์เซอร์ (Chrome Extension Manifest V3) คู่กับ Local Companion Transcoder สำหรับดึงภาพและวิดีโอจากทุกหน้าเว็บเพียงแค่ **วางเมาส์เหนือภาพหรือวิดีโอแล้วคลิกปุ่มดาวน์โหลด** หรือ **ลากมาวาง (Drag & Drop)** โดยระบบจะกำจัดนามสกุลแปลกๆ (`.webp`, `.avif`, `.svg`, `.bmp`, `.jfif`, `.webm`, `.ogv`, `.mov`, `.mkv`, `.ts`, `.m3u8`, `blob:`) และแปลงให้เป็นไฟล์มาตรฐานทั่วไป (**`.png`**, **`.jpg`**, และ **`.mp4` H.264**) อัตโนมัติ 100%

---

## ✨ ฟีเจอร์หลัก
1. **Hover HUD Button**: วางเมาส์บนรูป (`<img>`, `<svg>`, `<canvas>`, CSS `background-image`) หรือวิดีโอ (`<video>`, HLS, Blob) จะมีปุ่มลอยขึ้นมาให้กด **`⬇ โหลด PNG`**, **`⬇ โหลด JPG`**, หรือ **`⬇ โหลด MP4`** ทันที
2. **Right-Click Context Menu**: คลิกขวาที่ภาพหรือวิดีโอเพื่อเลือกบันทึกเป็น `.PNG`, `.JPG`, หรือ `.MP4`
3. **Popup & Drag-and-Drop Zone**: ลากรูปหรือวิดีโอมาวางในกล่อง Popup หรือกดสแกนทั้งหน้าเว็บเพื่อโหลดได้ทันที
4. **ไม่เอานามสกุลแปลก**: บังคับแปลงด้วย Pillow (RGB/RGBA) และ FFmpeg (H.264 + AAC `ftyp` MP4) พร้อมตรวจสอบ Magic Bytes ทุกไฟล์

---

## 🚀 วิธีติดตั้งและใช้งาน
1. รัน Companion Server:
   ```bash
   python3 run.py media server
   ```
2. เปิด Chrome ไปที่ `chrome://extensions/` ➔ เปิด **Developer mode** ➔ กด **Load unpacked** ➔ เลือกโฟลเดอร์:
   `projects/media_downloader_extension/extension`
3. ทดสอบบนหน้า Sandbox ที่รวมภาพและวิดีโอทุกนามสกุล:
   `http://127.0.0.1:8765/sandbox`
4. รันชุดทดสอบอัตโนมัติ (E2E Verification):
   ```bash
   python3 run.py media test
   ```

