#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form & API Interceptor — Local Webhook Server (Port 8091)
รับข้อมูล JSON ที่ Extension ดักจับได้แบบ Real-time และเจนสคริปต์อัตโนมัติทันที
"""

import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
CAPTURES_DIR = BASE_DIR / "data" / "captures"
EXPORTS_DIR = BASE_DIR / "data" / "exports"

CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

from src.generator import generate_python_requests_script, generate_playwright_script

class WebhookHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self, status=200):
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(200)

    def do_GET(self):
        if self.path == "/api/status":
            captures = list(CAPTURES_DIR.glob("*.json"))
            res = {
                "status": "RUNNING",
                "service": "Form & API Interceptor Local Relay",
                "port": 8091,
                "captured_sessions_count": len(captures),
                "timestamp": datetime.now().isoformat()
            }
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        if self.path == "/api/capture":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")

            try:
                data = json.loads(body)
                session_id = data.get("id") or f"session_{int(datetime.now().timestamp())}"
                
                # 1. บันทึกไฟล์ JSON ดิบ
                json_path = CAPTURES_DIR / f"{session_id}.json"
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                # 2. เจนสคริปต์ Python Direct API อัตโนมัติ
                api_script = generate_python_requests_script(data, 0)
                api_path = EXPORTS_DIR / f"{session_id}_direct_api.py"
                with open(api_path, "w", encoding="utf-8") as f:
                    f.write(api_script)
                os.chmod(api_path, 0o755)

                # 3. เจนสคริปต์ Playwright Browser Fallback อัตโนมัติ
                browser_script = generate_playwright_script(data)
                browser_path = EXPORTS_DIR / f"{session_id}_playwright_bot.py"
                with open(browser_path, "w", encoding="utf-8") as f:
                    f.write(browser_script)
                os.chmod(browser_path, 0o755)

                fields_count = len(data.get("formFields", []))
                api_count = len(data.get("apiCalls", []))

                print("\n" + "=" * 65)
                print(f"🎯 [WEBHOOK CAPTURED] ได้รับข้อมูลใหม่จาก Extension!")
                print(f"📁 Session ID: {session_id}")
                print(f"📝 ฟอร์มที่กรอก: {fields_count} ช่อง | 🌐 API ที่ดักได้: {api_count} รายการ")
                print(f"💾 ไฟล์ข้อมูลดิบ: {json_path.relative_to(BASE_DIR)}")
                print(f"🐍 สคริปต์ Python API: {api_path.relative_to(BASE_DIR)}")
                print(f"🎭 สคริปต์ Playwright: {browser_path.relative_to(BASE_DIR)}")
                print("=" * 65)

                self._set_cors_headers(200)
                resp = {
                    "success": True,
                    "session_id": session_id,
                    "json_file": str(json_path),
                    "api_script": str(api_path),
                    "browser_script": str(browser_path)
                }
                self.wfile.write(json.dumps(resp).encode("utf-8"))
            except Exception as e:
                print(f"❌ Error parsing capture: {e}", file=sys.stderr)
                self._set_cors_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self._set_cors_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

def start_server(port=8091):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, WebhookHandler)
    print("=" * 65)
    print(f"🔌 Form & API Interceptor — Local Webhook Server พร้อมทำงาน!")
    print(f"🌐 กำลังรอรับข้อมูลจาก Extension ที่: http://127.0.0.1:{port}/api/capture")
    print(f"📡 ตรวจสอบสถานะ: http://127.0.0.1:{port}/api/status")
    print("👉 กด Ctrl+C เพื่อหยุดการทำงาน")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 ปิดเซิร์ฟเวอร์ Webhook เรียบร้อยค่ะ")

if __name__ == "__main__":
    start_server()
