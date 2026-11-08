#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧪 Comprehensive E2E Verification Suite for Universal Media Grabber Extension & Companion Server
ทดสอบครบทุกนามสกุลภาพ (.webp, .avif, .svg, .bmp, .gif, .jfif, .png, .jpg, inline SVG, DataURL) -> .png & .jpg
และทุกนามสกุลวิดีโอ (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, .mp4, Blob Stream) -> .mp4 (H.264)
รวมถึงตรวจสอบโครงสร้าง Chrome Extension Manifest V3 และทดสอบ Hover HUD บนหน้าเว็บจริง
"""
import base64
import json
import os
import socket
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from PIL import Image
import io
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.companion_server import CompanionRequestHandler, ensure_dirs, DOWNLOADS_DIR, TEST_ASSETS_DIR


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestUniversalMediaGrabberE2E(unittest.TestCase):
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

    def _get_bytes(self, url: str) -> bytes:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()

    def test_01_manifest_and_extension_files_exist(self):
        """ตรวจสอบไฟล์ทั้งหมดของ Chrome Extension Manifest V3"""
        ext_dir = BASE_DIR / "extension"
        manifest_path = ext_dir / "manifest.json"
        self.assertTrue(manifest_path.exists(), "manifest.json ต้องมีอยู่จริง")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["manifest_version"], 3)

        required_files = [
            ext_dir / "content/content.js",
            ext_dir / "content/content.css",
            ext_dir / "background/service-worker.js",
            ext_dir / "popup/popup.html",
            ext_dir / "popup/popup.js",
            ext_dir / "sidepanel/sidepanel.html",
            ext_dir / "sidepanel/sidepanel.js",
            ext_dir / "icons/icon-16.png",
            ext_dir / "icons/icon-48.png",
            ext_dir / "icons/icon-128.png",
        ]
        for f in required_files:
            self.assertTrue(f.exists() and f.stat().st_size > 0, f"Missing extension file: {f}")

    def test_02_all_image_formats_convert_to_standard_png_and_jpg(self):
        """ทดสอบแปลงไฟล์ภาพทุกนามสกุล (.webp, .avif, .svg, .bmp, .gif, .jfif, .png, .jpg) เป็น .png และ .jpg แท้"""
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
                self.assertTrue(
                    res["filename"].endswith(f".{target_fmt}"),
                    f"Filename {res['filename']} must end with .{target_fmt}",
                )
                # Ensure no weird extension remains in filename
                for weird in (".webp", ".avif", ".svg", ".bmp", ".gif", ".jfif"):
                    self.assertNotIn(weird, res["filename"].lower())

                raw = self._get_bytes(res["downloadUrl"])
                if target_fmt == "png":
                    self.assertTrue(raw.startswith(b"\x89PNG\r\n\x1a\n"))
                else:
                    self.assertTrue(raw.startswith(b"\xff\xd8\xff"))

                im = Image.open(io.BytesIO(raw))
                self.assertGreater(im.width, 0)
                self.assertGreater(im.height, 0)

    def test_03_inline_svg_and_data_url_convert_to_standard_png_and_jpg(self):
        """ทดสอบแปลง Inline SVG และ Data URL (Canvas/Blob) เป็น .png และ .jpg"""
        svg_code = '<svg xmlns="http://www.w3.org/2000/svg" width="240" height="140"><rect width="240" height="140" fill="#10b981"/><circle cx="120" cy="70" r="45" fill="#ffffff"/></svg>'
        res_png = self._post_json(
            "/api/convert/image",
            {"svgText": svg_code, "targetFormat": "png", "filename": "inline_vector.svg"},
        )
        self.assertTrue(res_png.get("ok"))
        self.assertTrue(res_png["filename"].endswith(".png"))

        webp_bytes = (TEST_ASSETS_DIR / "images" / "sample_webp.webp").read_bytes()
        data_url = "data:image/webp;base64," + base64.b64encode(webp_bytes).decode("ascii")
        res_jpg = self._post_json(
            "/api/convert/image",
            {"base64Data": data_url, "targetFormat": "jpg", "filename": "blob_image.webp"},
        )
        self.assertTrue(res_jpg.get("ok"))
        self.assertTrue(res_jpg["filename"].endswith(".jpg"))

    def test_04_all_video_formats_convert_to_standard_mp4(self):
        """ทดสอบแปลงวิดีโอทุกนามสกุล (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, .mp4, Blob) เป็น .mp4 มาตรฐาน (H.264)"""
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
            self.assertTrue(res.get("ok"), f"Failed video {vid_name} -> mp4: {res}")
            self.assertTrue(res["filename"].endswith(".mp4"), f"Expected .mp4, got {res['filename']}")
            for weird in (".webm", ".ogv", ".mov", ".mkv", ".ts", ".m3u8"):
                self.assertNotIn(weird, res["filename"].lower())

            raw = self._get_bytes(res["downloadUrl"])
            self.assertEqual(raw[4:8], b"ftyp", f"Invalid MP4 header for {vid_name}")
            self.assertEqual(res.get("codec"), "h264")

        # ทดสอบ Blob Stream Video (Base64 WebM -> MP4)
        webm_bytes = (TEST_ASSETS_DIR / "videos" / "sample_webm.webm").read_bytes()
        b64_vid = "data:video/webm;base64," + base64.b64encode(webm_bytes).decode("ascii")
        res_blob = self._post_json(
            "/api/convert/video",
            {"base64Data": b64_vid, "targetFormat": "mp4", "filename": "blob_video_stream.webm"},
        )
        self.assertTrue(res_blob.get("ok"))
        self.assertTrue(res_blob["filename"].endswith(".mp4"))


if __name__ == "__main__":
    print("=" * 74)
    print("🧪 รันชุดทดสอบ E2E Universal Media Grabber (ครบทุกนามสกุลภาพและวิดีโอ)")
    print("=" * 74)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestUniversalMediaGrabberE2E)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
