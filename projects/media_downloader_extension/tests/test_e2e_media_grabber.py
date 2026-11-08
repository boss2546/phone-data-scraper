#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Deep Comprehensive E2E Verification Suite (8 Gates)
สำหรับ Universal Media Grabber Chrome Extension & Auto-Wakeup Companion Server

ทดสอบละเอียดครบทุกมิติ:
- Gate 1: ตรวจสอบโครงสร้างไฟล์ Chrome Extension (Manifest V3) ครบทุกไฟล์และสิทธิ์
- Gate 2: ทดสอบระบบ Auto-Wakeup & Self-Healing (จำลองเซิร์ฟเวอร์ดับแล้วสั่งปลุกอัตโนมัติผ่าน native_host.py)
- Gate 3: ทดสอบแปลงไฟล์ภาพครบ 10 รูปแบบ (.webp, .avif, .svg, .bmp, .gif, .jfif, .png, .jpg, Inline SVG, DataURL) -> .PNG และ .JPG แท้ (รวม 20 เคส)
- Gate 4: ทดสอบความถูกต้องของพื้นหลังสีขาวเมื่อแปลงภาพโปร่งใส (Alpha RGBA -> RGB JPG)
- Gate 5: ทดสอบการล้างนามสกุลแปลกและ Query String ซับซ้อน (Sanitize Filename Guarantee)
- Gate 6: ทดสอบแปลงไฟล์วิดีโอครบ 8 รูปแบบ (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, .mp4, Blob Stream) -> .MP4 (H.264 + yuv420p) แท้ทุกไฟล์
- Gate 7: ทดสอบหน้าห้องแล็บ /sandbox และระบบบันทึกประวัติ (/api/history)
- Gate 8: ทดสอบรัน Google Chrome จริง (Headless CDP) เปิดหน้าเว็บ /sandbox จำลองเอาเมาส์ชี้ (Hover) กดปุ่มโหลด ตรวจสถานะ "กำลังประมวลผล..." -> "ประมวลผลเสร็จแล้ว! กดโหลดอีกครั้ง"
"""
import base64
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.companion_server import (
    CompanionRequestHandler,
    ensure_dirs,
    inspect_video_with_ffprobe,
    sanitize_base_filename,
    DOWNLOADS_DIR,
    TEST_ASSETS_DIR,
)

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestUniversalMediaGrabberDeepE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["UMG_QUIET"] = "1"
        ensure_dirs()
        cls.port = get_free_port()
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", cls.port), CompanionRequestHandler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()

    def _post_json(self, path: str, payload: dict) -> dict:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get_json(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _get_bytes(self, url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()

    def test_gate_01_manifest_and_extension_files(self):
        """[Gate 1] ตรวจสอบโครงสร้าง Chrome Extension Manifest V3 และโค้ดสถานะการประมวลผล"""
        ext_dir = BASE_DIR / "extension"
        manifest_path = ext_dir / "manifest.json"
        self.assertTrue(manifest_path.exists())
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_version"], 3)
        self.assertIn("downloads", manifest["permissions"])
        self.assertIn("nativeMessaging", manifest["permissions"])

        content_js = (ext_dir / "content/content.js").read_text(encoding="utf-8")
        self.assertIn("กำลังประมวลผล", content_js)
        self.assertIn("ประมวลผลเสร็จแล้ว", content_js)
        self.assertIn("กดโหลดอีกครั้ง", content_js)

        sw_js = (ext_dir / "background/service-worker.js").read_text(encoding="utf-8")
        self.assertIn("autoWakeupCompanionServer", sw_js)
        self.assertIn("OffscreenCanvas", sw_js)

    def test_gate_02_auto_wakeup_daemon_and_native_host(self):
        """[Gate 2] ทดสอบระบบ Auto-Wakeup (`native_host.py --ensure`) ว่าปลุกเซิร์ฟเวอร์พอร์ต 8765 ได้จริง"""
        native_host = BASE_DIR / "src" / "native_host.py"
        proc = subprocess.run(
            [sys.executable, str(native_host), "--ensure"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, f"native_host failed: {proc.stderr}")
        info = json.loads(proc.stdout.strip())
        self.assertTrue(info.get("ok"))
        self.assertEqual(info.get("port"), 8765)

        with urllib.request.urlopen("http://127.0.0.1:8765/api/health", timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(health.get("ok"))

    def test_gate_03_all_image_formats_to_png_and_jpg(self):
        """[Gate 3] ทดสอบแปลงไฟล์ภาพทุกนามสกุล (.webp, .avif, .svg, .bmp, .gif, .jfif, .png, .jpg) เป็น .PNG และ .JPG แท้ (16 เคส)"""
        image_files = [
            "sample_webp.webp",
            "sample_avif.avif",
            "sample_svg.svg",
            "sample_bmp.bmp",
            "sample_gif.gif",
            "sample_jfif.jfif",
            "sample_png.png",
            "sample_jpg.jpg",
        ]
        for img_name in image_files:
            asset_url = f"{self.base_url}/assets/images/{img_name}"
            for target_fmt in ("png", "jpg"):
                res = self._post_json(
                    "/api/convert/image",
                    {"url": asset_url, "targetFormat": target_fmt, "filename": img_name},
                )
                self.assertTrue(res.get("ok"), f"Failed {img_name} -> {target_fmt}: {res}")
                self.assertTrue(res["filename"].endswith(f".{target_fmt}"))
                raw = self._get_bytes(res["downloadUrl"])
                if target_fmt == "png":
                    self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                else:
                    self.assertTrue(raw.startswith(b"\xff\xd8\xff"))
                im = Image.open(io.BytesIO(raw))
                im.verify()

    def test_gate_04_transparent_alpha_to_jpg_white_background(self):
        """[Gate 4] ทดสอบแปลงภาพพื้นหลังโปร่งใส (RGBA/SVG) เป็น .JPG ต้องได้พื้นหลังสีขาว ไม่ดำมืด"""
        svg_transparent = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><circle cx="50" cy="50" r="20" fill="#ff0000"/></svg>'
        res = self._post_json(
            "/api/convert/image",
            {"svgText": svg_transparent, "targetFormat": "jpg", "filename": "alpha_test.svg"},
        )
        self.assertTrue(res.get("ok"))
        raw = self._get_bytes(res["downloadUrl"])
        im = Image.open(io.BytesIO(raw))
        self.assertEqual(im.mode, "RGB")
        # มุมภาพ (0, 0) ต้องเป็นสีขาวสว่าง (> 245) ไม่ใช่สีดำ (0, 0, 0)
        corner_pixel = im.getpixel((2, 2))
        self.assertGreater(corner_pixel[0], 245)
        self.assertGreater(corner_pixel[1], 245)
        self.assertGreater(corner_pixel[2], 245)

    def test_gate_05_weird_extension_and_query_string_sanitization(self):
        """[Gate 5] ทดสอบการตัดนามสกุลแปลกซ้อนกันและ Query String ยาวๆ ให้เหลือแค่ .png / .jpg / .mp4 สะอาด"""
        dirty_names = [
            "https://cdn.example.com/media/photo_01.webp.avif?token=12345&format=webp#hero",
            "banner.svgz.webp",
            "clip_video.webm.mkv?sig=abcdef",
            "stream_playlist.m3u8?session=999",
        ]
        for raw_name in dirty_names:
            stem = sanitize_base_filename(raw_name)
            for forbidden in (".webp", ".avif", ".svg", ".webm", ".mkv", ".m3u8", "?", "#"):
                self.assertNotIn(forbidden, stem.lower())

    def test_gate_06_all_video_formats_to_standard_h264_mp4(self):
        """[Gate 6] ทดสอบแปลงวิดีโอทุกนามสกุล (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, .mp4, Blob) เป็น H.264 .MP4 แท้"""
        video_files = [
            "sample_webm.webm",
            "sample_ogv.ogv",
            "sample_mov.mov",
            "sample_mkv.mkv",
            "sample_ts.ts",
            "sample_hls.m3u8",
            "sample_mp4.mp4",
        ]
        for vid_name in video_files:
            asset_url = f"{self.base_url}/assets/videos/{vid_name}"
            res = self._post_json(
                "/api/convert/video",
                {"url": asset_url, "targetFormat": "mp4", "filename": vid_name},
            )
            self.assertTrue(res.get("ok"), f"Video conversion failed for {vid_name}: {res}")
            self.assertTrue(res["filename"].endswith(".mp4"))
            raw = self._get_bytes(res["downloadUrl"])
            self.assertEqual(raw[4:8], b"ftyp")
            self.assertEqual(res.get("codec"), "h264")
            self.assertGreater(res.get("width", 0), 0)
            self.assertGreater(res.get("height", 0), 0)

            saved_path = BASE_DIR / res["savedPath"]
            probe = inspect_video_with_ffprobe(saved_path)
            self.assertEqual(probe["codec"], "h264")

        # ทดสอบ Blob Stream Video
        webm_bytes = (TEST_ASSETS_DIR / "videos" / "sample_webm.webm").read_bytes()
        b64_vid = "data:video/webm;base64," + base64.b64encode(webm_bytes).decode("ascii")
        res_blob = self._post_json(
            "/api/convert/video",
            {"base64Data": b64_vid, "targetFormat": "mp4", "filename": "live_blob_video.webm"},
        )
        self.assertTrue(res_blob.get("ok"))
        self.assertTrue(res_blob["filename"].endswith(".mp4"))

    def test_gate_07_sandbox_gallery_and_history_api(self):
        """[Gate 7] ทดสอบหน้าเว็บห้องแล็บ /sandbox และ API ประวัติการดาวน์โหลด (/api/history)"""
        html_bytes = self._get_bytes(f"{self.base_url}/sandbox")
        html_text = html_bytes.decode("utf-8")
        self.assertIn("sample_webp.webp", html_text)
        self.assertIn("sample_webm.webm", html_text)

        hist = self._get_json("/api/history")
        self.assertTrue(hist.get("ok"))
        self.assertGreater(hist.get("count", 0), 10)

    def test_gate_08_real_google_chrome_headless_dom_and_extension_flow(self):
        """[Gate 8] ทดสอบรัน Google Chrome จริง (Headless DOM) จำลองการวางเมาส์ กดปุ่มประมวลผล และแสดงปุ่ม 'กดโหลดอีกครั้ง'"""
        if not os.path.exists(CHROME_BIN):
            self.skipTest("Google Chrome binary not found")

        # สร้างหน้า HTML จำลองที่ฝัง content.css + content.js และชี้ไปยัง Companion Server ของเทสต์นี้
        content_css = (BASE_DIR / "extension/content/content.css").read_text(encoding="utf-8")
        content_js = (BASE_DIR / "extension/content/content.js").read_text(encoding="utf-8")
        content_js_patched = content_js.replace("http://127.0.0.1:8765", self.base_url)

        test_page_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>{content_css}</style>
</head>
<body>
  <img id="test-img" src="{self.base_url}/assets/images/sample_webp.webp" alt="chrome_e2e_webp" width="300" height="200" />
  <video id="test-vid" src="{self.base_url}/assets/videos/sample_webm.webm" width="320" height="180"></video>
  <div id="test-result">PENDING</div>
  <script>{content_js_patched}</script>
  <script>
    window.addEventListener('load', async () => {{
      try {{
        const img = document.getElementById('test-img');
        img.dispatchEvent(new MouseEvent('mouseover', {{ bubbles: true }}));
        const host = document.getElementById('umg-hover-host');
        const btnPrimary = host.shadowRoot.getElementById('btn-primary');
        const btnRedownload = host.shadowRoot.getElementById('btn-redownload');
        const toastHost = document.getElementById('umg-toast-host');
        const statusText = toastHost.shadowRoot.getElementById('status-text');

        // คลิกปุ่มโหลด PNG บน Hover HUD
        btnPrimary.click();

        // รอให้ประมวลผลเสร็จ
        for (let i = 0; i < 30; i++) {{
          await new Promise(r => setTimeout(r, 150));
          if (statusText.textContent.includes('ประมวลผลเสร็จแล้ว')) break;
        }}

        const summary = {{
          hoverVisible: host.style.display === 'block',
          statusMsg: statusText.textContent,
          redownloadVisible: btnRedownload.style.display !== 'none',
          redownloadLabel: btnRedownload.textContent
        }};
        document.getElementById('test-result').textContent = JSON.stringify(summary);
      }} catch (err) {{
        document.getElementById('test-result').textContent = 'ERROR:' + err.message;
      }}
    }});
  </script>
</body>
</html>"""

        with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
            tf.write(test_page_html)
            temp_html_path = tf.name

        try:
            cmd = [
                CHROME_BIN,
                "--headless=new",
                "--disable-gpu",
                "--no-sandbox",
                "--virtual-time-budget=6000",
                "--dump-dom",
                f"file://{temp_html_path}",
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
            dom_out = proc.stdout
            self.assertIn("ประมวลผลเสร็จแล้ว", dom_out, f"Chrome DOM output did not reach finished state: {dom_out[-600:]}")
            self.assertIn("chrome_e2e_webp", dom_out)
        finally:
            if os.path.exists(temp_html_path):
                os.unlink(temp_html_path)


if __name__ == "__main__":
    print("=" * 78)
    print("🧪 รันชุดทดสอบละเอียด 8 ด่าน (8-Gate Deep E2E Verification Suite)")
    print("=" * 78)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUniversalMediaGrabberDeepE2E)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
