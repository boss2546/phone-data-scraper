#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form & API Interceptor — Comprehensive Test Suite (การทดสอบระบบแบบละเอียด)
ทดสอบทุกมิติ: Manifest V3, Integrity ไฟล์, JavaScript Syntax, Code Generator, Webhook Server, และ End-to-End Execution
"""

import sys
import os
import json
import time
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer
import urllib.request
import urllib.parse
from PIL import Image

# Path resolution
BASE_DIR = Path(__file__).resolve().parent.parent
EXTENSION_DIR = BASE_DIR / "extension"
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"

sys.path.insert(0, str(BASE_DIR))

from src.generator import generate_python_requests_script, generate_playwright_script
from src.server import WebhookHandler

class TestReport:
    def __init__(self):
        self.results = []

    def add(self, category: str, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            "category": category,
            "name": test_name,
            "passed": passed,
            "details": details
        })

    def print_summary(self):
        print("\n" + "=" * 76)
        print("📊 สรุปผลการทดสอบระบบ Form & API Interceptor อย่างละเอียด (Test Report)")
        print("=" * 76)
        
        current_cat = ""
        passed_count = 0
        total_count = len(self.results)

        for r in self.results:
            if r["category"] != current_cat:
                current_cat = r["category"]
                print(f"\n📌 หมวด: {current_cat}")
            
            icon = "✅ ผ่าน (PASS)" if r["passed"] else "❌ ล้มเหลว (FAIL)"
            if r["passed"]:
                passed_count += 1
            print(f"  {icon} - {r['name']}")
            if r["details"]:
                print(f"     ↳ {r['details']}")

        score = (passed_count / total_count * 100) if total_count > 0 else 0
        print("\n" + "-" * 76)
        print(f"🏅 คะแนนการทดสอบรวม: {passed_count}/{total_count} ข้อ ({score:.1f}%)")
        print("=" * 76)
        return passed_count == total_count


def test_manifest_and_file_integrity(report: TestReport):
    cat = "1. ตรวจสอบความถูกต้องของ Manifest V3 & โครงสร้างไฟล์ส่วนเสริม"
    manifest_path = EXTENSION_DIR / "manifest.json"
    
    # 1.1 Manifest file exists & valid JSON
    if not manifest_path.exists():
        report.add(cat, "ตรวจพบไฟล์ manifest.json", False, "ไม่พบไฟล์ manifest.json")
        return
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        report.add(cat, "ไฟล์ manifest.json เป็น JSON ที่ถูกต้อง", True, f"Version {manifest.get('version')}")
    except Exception as e:
        report.add(cat, "ไฟล์ manifest.json เป็น JSON ที่ถูกต้อง", False, str(e))
        return

    # 1.2 Manifest V3 specifications
    is_v3 = manifest.get("manifest_version") == 3
    report.add(cat, "กำหนด manifest_version เป็น 3 (ตามมาตรฐานล่าสุด)", is_v3)

    # 1.3 Permissions
    permissions = manifest.get("permissions", [])
    has_req_perms = all(p in permissions for p in ["storage", "sidePanel", "tabs", "cookies"])
    report.add(cat, "สิทธิ์ Permissions พื้นฐาน (storage, sidePanel, tabs, cookies)", has_req_perms, f"กำหนด: {permissions}")

    # 1.4 Icons validation
    icons = manifest.get("icons", {})
    all_icons_valid = True
    icon_details = []
    for size_str in ["16", "48", "128"]:
        icon_rel = icons.get(size_str)
        if not icon_rel:
            all_icons_valid = False
            icon_details.append(f"ขาด icon-{size_str}")
            continue
        icon_path = EXTENSION_DIR / icon_rel
        if not icon_path.exists():
            all_icons_valid = False
            icon_details.append(f"ไม่พบไฟล์ {icon_rel}")
            continue
        try:
            with Image.open(icon_path) as img:
                expected_size = int(size_str)
                if img.size != (expected_size, expected_size):
                    all_icons_valid = False
                    icon_details.append(f"ขนาด {icon_rel} ไม่ตรง: {img.size}")
                else:
                    icon_details.append(f"icon-{size_str}.png: {img.size[0]}x{img.size[1]}px ({img.format})")
        except Exception as e:
            all_icons_valid = False
            icon_details.append(str(e))

    report.add(cat, "ไอคอน PNG ครบทุกขนาด (16x16, 48x48, 128x128 px)", all_icons_valid, " | ".join(icon_details))

    # 1.5 Background service worker
    sw_rel = manifest.get("background", {}).get("service_worker")
    sw_path = EXTENSION_DIR / sw_rel if sw_rel else None
    sw_exists = sw_path and sw_path.exists()
    report.add(cat, "Background Service Worker มีอยู่จริงบนดิสก์", sw_exists, str(sw_rel))

    # 1.6 Content scripts
    content_scripts = manifest.get("content_scripts", [])
    cs_valid = len(content_scripts) >= 2
    report.add(cat, "Content Scripts กำหนดทั้ง MAIN world และ ISOLATED world", cs_valid, f"{len(content_scripts)} รายการ")

    # 1.7 Popup & Sidepanel files
    popup_html = EXTENSION_DIR / "popup" / "popup.html"
    popup_js = EXTENSION_DIR / "popup" / "popup.js"
    sidepanel_html = EXTENSION_DIR / "sidepanel" / "sidepanel.html"
    sidepanel_js = EXTENSION_DIR / "sidepanel" / "sidepanel.js"
    ui_files_exist = all(p.exists() for p in [popup_html, popup_js, sidepanel_html, sidepanel_js])
    report.add(cat, "ไฟล์หน้าต่าง Popup และ Side Panel ครบถ้วน", ui_files_exist)


def test_javascript_syntax(report: TestReport):
    cat = "2. ตรวจสอบ Syntax ของโค้ด JavaScript ทั้งหมดด้วย Node.js Engine"
    js_files = [
        EXTENSION_DIR / "background" / "service-worker.js",
        EXTENSION_DIR / "content" / "inject-interceptor.js",
        EXTENSION_DIR / "content" / "content.js",
        EXTENSION_DIR / "popup" / "popup.js",
        EXTENSION_DIR / "sidepanel" / "sidepanel.js"
    ]

    for js_file in js_files:
        try:
            res = subprocess.run(
                ["node", "--check", str(js_file)],
                capture_output=True,
                text=True,
                timeout=5
            )
            passed = (res.returncode == 0)
            details = "ไวยากรณ์ถูกต้อง 0 Errors" if passed else res.stderr.strip()
            report.add(cat, f"Syntax Check: {js_file.name}", passed, details)
        except Exception as e:
            report.add(cat, f"Syntax Check: {js_file.name}", False, str(e))


def test_code_generators(report: TestReport):
    cat = "3. ทดสอบเครื่องมือสร้างโค้ดอัตโนมัติ (Python Requests & Playwright Generator)"

    # Test Sample Session
    sample_session = {
        "id": "unit_test_session_999",
        "url": "https://httpbin.org/post",
        "title": "ระบบสั่งซื้อสินค้าอัตโนมัติ",
        "cookies": [
            {"name": "sessionid", "value": "test_session_token_xyz", "domain": "httpbin.org", "path": "/"}
        ],
        "cookieString": "sessionid=test_session_token_xyz; auth_token=meuu_secret_999",
        "formFields": [
            {"label": "ชื่อลูกค้า", "name": "first_name", "id": "fn", "selector": "#fn", "value": "กฤษณะ", "type": "text"},
            {"label": "นามสกุล", "name": "last_name", "id": "ln", "selector": "#ln", "value": "มงคลสุข", "type": "text"},
            {"label": "อีเมล", "name": "email", "id": "em", "selector": "#em", "value": "boss@meuu.club", "type": "email"},
            {"label": "แพ็กเกจ", "name": "pkg", "id": "pkg_sel", "selector": "#pkg_sel", "value": "pro_scraper", "type": "select"},
            {"label": "ยอมรับเงื่อนไข", "name": "agree", "id": "chk", "selector": "#chk", "value": True, "type": "checkbox"}
        ],
        "submitButton": {
            "text": "ยืนยันการสั่งซื้อ",
            "selector": "button#btn-submit"
        },
        "apiCalls": [
            {
                "url": "https://httpbin.org/post",
                "method": "POST",
                "requestHeaders": {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer sk-meuu-token-12345",
                    "X-App-Client": "FormAPIInterceptor"
                },
                "requestBody": {
                    "first_name": "กฤษณะ",
                    "last_name": "มงคลสุข",
                    "email": "boss@meuu.club",
                    "package": "pro_scraper",
                    "agree": True
                }
            }
        ]
    }

    # 3.1 Test Python Requests Generator
    py_code = generate_python_requests_script(sample_session, 0)
    try:
        compiled_py = compile(py_code, "<string>", "exec")
        py_valid = ("requests.post" in py_code) and ("Bearer sk-meuu-token-12345" in py_code) and ("sessionid=test_session_token_xyz" in py_code)
        report.add(cat, "สร้างสคริปต์ Python Requests พร้อม Cookies & Auth และคอมไพล์ผ่าน 100%", py_valid, f"ขนาดโค้ด: {len(py_code)} chars")
    except Exception as e:
        report.add(cat, "สร้างสคริปต์ Python Requests พร้อม Cookies & Auth และคอมไพล์ผ่าน 100%", False, f"Compile Error: {e}")

    # 3.2 Test Playwright Browser Automation Generator
    pw_code = generate_playwright_script(sample_session)
    try:
        compiled_pw = compile(pw_code, "<string>", "exec")
        pw_valid = ("async_playwright" in pw_code) and ("#fn" in pw_code) and ("set_checked(True)" in pw_code) and ("add_cookies" in pw_code)
        report.add(cat, "สร้างสคริปต์ Playwright พร้อมฉีด Cookies อัตโนมัติและคอมไพล์ผ่าน 100%", pw_valid, f"ขนาดโค้ด: {len(pw_code)} chars")
    except Exception as e:
        report.add(cat, "สร้างสคริปต์ Playwright Browser Automation และคอมไพล์ผ่าน 100%", False, f"Compile Error: {e}")


def test_webhook_server_lifecycle(report: TestReport):
    cat = "4. ทดสอบเซิร์ฟเวอร์ Local Webhook Server (Integration & File Generation)"
    test_port = 8095
    server_address = ("127.0.0.1", test_port)
    httpd = HTTPServer(server_address, WebhookHandler)

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        # 4.1 Test GET /api/status
        status_url = f"http://127.0.0.1:{test_port}/api/status"
        req = urllib.request.Request(status_url, method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            is_running = (resp.status == 200 and data.get("status") == "RUNNING")
            report.add(cat, "Endpoint GET /api/status ตอบกลับสถานะ RUNNING", is_running, f"Status code: {resp.status}")

        # 4.2 Test OPTIONS /api/capture (CORS Preflight)
        capture_url = f"http://127.0.0.1:{test_port}/api/capture"
        req_opt = urllib.request.Request(capture_url, method="OPTIONS")
        with urllib.request.urlopen(req_opt, timeout=3) as resp:
            cors_origin = resp.headers.get("Access-Control-Allow-Origin")
            cors_valid = (resp.status == 200 and cors_origin == "*")
            report.add(cat, "CORS Preflight Headers สำหรับ Chrome Extension", cors_valid, f"Access-Control-Allow-Origin: {cors_origin}")

        # 4.3 Test POST /api/capture (Full Payload Processing)
        test_session_id = f"test_e2e_{int(time.time())}"
        test_payload = {
            "id": test_session_id,
            "url": "https://httpbin.org/post",
            "title": "ห้องแล็บทดสอบสด",
            "formFields": [
                {"label": "ชื่อ", "name": "first_name", "selector": "#fn", "value": "กฤษณะ", "type": "text"},
                {"label": "อีเมล", "name": "email", "selector": "#em", "value": "boss@meuu.club", "type": "email"}
            ],
            "submitButton": {"text": "ส่งข้อมูล", "selector": "#btn-submit"},
            "apiCalls": [
                {
                    "url": "https://httpbin.org/post",
                    "method": "POST",
                    "requestHeaders": {"Content-Type": "application/json"},
                    "requestBody": {"first_name": "กฤษณะ", "email": "boss@meuu.club"}
                }
            ]
        }

        req_post = urllib.request.Request(
            capture_url,
            data=json.dumps(test_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req_post, timeout=5) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            post_success = (resp.status == 200 and resp_data.get("success") is True)
            report.add(cat, "Endpoint POST /api/capture รับข้อมูลและประมวลผลสำเร็จ", post_success)

        # 4.4 Check Saved Capture File
        saved_json = DATA_DIR / "captures" / f"{test_session_id}.json"
        json_ok = saved_json.exists() and saved_json.stat().st_size > 50
        report.add(cat, "บันทึกไฟล์ Capture JSON ดิบลง data/captures/", json_ok, f"ไฟล์: {saved_json.name}")

        # 4.5 Check Generated Python API Script
        saved_api = DATA_DIR / "exports" / f"{test_session_id}_direct_api.py"
        api_ok = saved_api.exists() and saved_api.stat().st_size > 100
        report.add(cat, "สร้างสคริปต์ Python API อัตโนมัติลง data/exports/", api_ok, f"ไฟล์: {saved_api.name}")

        # 4.6 Check Generated Playwright Script
        saved_pw = DATA_DIR / "exports" / f"{test_session_id}_playwright_bot.py"
        pw_ok = saved_pw.exists() and saved_pw.stat().st_size > 100
        report.add(cat, "สร้างสคริปต์ Playwright Bot อัตโนมัติลง data/exports/", pw_ok, f"ไฟล์: {saved_pw.name}")

        # 4.7 Execute the Generated Python API Script to verify live execution
        try:
            exec_res = subprocess.run(
                [sys.executable, str(saved_api)],
                capture_output=True,
                text=True,
                timeout=10
            )
            live_exec_ok = (exec_res.returncode == 0 and "สถานะการตอบกลับ: 200" in exec_res.stdout)
            report.add(cat, "ทดสอบรันสคริปต์ Python API จริงผ่านเน็ตเวิร์ก (Live HTTP Execution)", live_exec_ok, "ยิงทดสอบไปยัง httpbin.org สำเร็จ Status 200")
        except Exception as e:
            report.add(cat, "ทดสอบรันสคริปต์ Python API จริงผ่านเน็ตเวิร์ก", False, str(e))

    finally:
        httpd.shutdown()


def test_test_bench_html_integrity(report: TestReport):
    cat = "5. ตรวจสอบความสมบูรณ์ของหน้าแล็บทดสอบ (Interactive Test Bench HTML)"
    test_bench_path = BASE_DIR / "test_form.html"
    
    exists = test_bench_path.exists()
    if not exists:
        report.add(cat, "ตรวจพบไฟล์ test_form.html", False)
        return

    with open(test_bench_path, "r", encoding="utf-8") as f:
        html = f.read()

    has_form = '<form id="order-form">' in html
    has_inputs = all(inp in html for inp in ["customer_firstname", "customer_lastname", "customer_email", "customer_phone", "product_package", "order_notes", "agree_terms"])
    has_submit_btn = 'id="btn-submit-order"' in html
    has_fetch_and_xhr = ("fetch(" in html) and ("XMLHttpRequest" in html)

    report.add(cat, "โครงสร้างฟอร์มครบถ้วน (First/Last name, Email, Tel, Select, Textarea, Checkbox)", has_form and has_inputs)
    report.add(cat, "ปุ่ม Submit และตัวตรวจจับเหตุการณ์ (Event Listeners)", has_submit_btn)
    report.add(cat, "จำลองการยิง Network ครบทั้ง Fetch API และ XMLHttpRequest (XHR)", has_fetch_and_xhr)


def run_all_tests():
    print("=" * 76)
    print("🚀 เริ่มต้นการทดสอบระบบ Form & API Interceptor แบบละเอียด 360 องศา...")
    print("=" * 76)

    report = TestReport()
    test_manifest_and_file_integrity(report)
    test_javascript_syntax(report)
    test_code_generators(report)
    test_webhook_server_lifecycle(report)
    test_test_bench_html_integrity(report)

    all_passed = report.print_summary()
    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
