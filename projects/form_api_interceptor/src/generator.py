#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Form & API Interceptor — Code Generator Engine
แปลงข้อมูล Session JSON ที่ได้จากการดักจับ เป็นสคริปต์ Python / Playwright อัตโนมัติ
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

def generate_python_requests_script(session: Dict[str, Any], api_index: int = 0) -> str:
    """สร้างสคริปต์ Python Requests สำหรับยิง API ตรงโดยไม่ต้องเปิดเบราว์เซอร์ พร้อม Cookies & Auth อัตโนมัติ"""
    api_calls = session.get("apiCalls", [])
    if not api_calls or api_index >= len(api_calls):
        return "# ❌ ไม่พบรายการ API ที่บันทึกไว้ในเซสชันนี้"

    api = api_calls[api_index]
    url = api.get("url", "")
    method = api.get("method", "GET").upper()
    headers = api.get("requestHeaders", {})
    body = api.get("requestBody")

    # Clean headers that python requests handles automatically
    headers_clean = {k: v for k, v in headers.items() if k.lower() not in ["host", "content-length"]}

    # Inject Captured Cookies automatically!
    cookie_str = session.get("cookieString", "")
    if not cookie_str and session.get("cookies"):
        parts = [f"{c['name']}={c['value']}" for c in session.get("cookies", []) if "name" in c and "value" in c]
        cookie_str = "; ".join(parts)
    
    if cookie_str and "cookie" not in [k.lower() for k in headers_clean]:
        headers_clean["Cookie"] = cookie_str

    # Inject Authorization Header or API Keys if detected
    auth_summary = session.get("authSummary", {})
    if auth_summary:
        bearer_tokens = auth_summary.get("bearerTokens", [])
        if bearer_tokens and "authorization" not in [k.lower() for k in headers_clean]:
            headers_clean["Authorization"] = f"Bearer {bearer_tokens[0]}"
        for k, v in auth_summary.get("apiKeys", {}).items():
            if k not in headers_clean:
                headers_clean[k] = v

    headers_repr = json.dumps(headers_clean, indent=4, ensure_ascii=False)
    
    body_arg = ""
    body_repr = ""
    if method in ["POST", "PUT", "PATCH"] and body is not None:
        if isinstance(body, dict):
            body_repr = f"payload = {json.dumps(body, indent=4, ensure_ascii=False)}\n"
            body_arg = ", json=payload"
        else:
            body_repr = f"payload = {repr(body)}\n"
            body_arg = ", data=payload"

    code = f'''#!/usr/bin/env python3
# ==============================================================================
# 🚀 Python Direct API Automation Script (Ready-to-Run with Cookies 🍪 & Auth 🔑)
# Generated automatically from Form & API Interceptor capture
# Target URL: {url}
# Method: {method}
# ==============================================================================

import requests
import json
import sys

def execute_request():
    url = "{url}"
    headers = {headers_repr}
    {body_repr}
    print(f"📡 กำลังส่งคำขอ [{method}] ไปยัง: {{url}} ...")
    try:
        response = requests.{method.lower()}(
            url,
            headers=headers{body_arg},
            timeout=15
        )
        print(f"📥 สถานะการตอบกลับ: {{response.status_code}} ({{response.reason}})")
        
        try:
            data = response.json()
            print("📄 ข้อมูลที่ได้รับ (JSON):")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            return data
        except Exception:
            print("📄 ข้อมูลที่ได้รับ (Text):")
            print(response.text[:1000])
            return response.text
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {{e}}", file=sys.stderr)
        return None

if __name__ == "__main__":
    execute_request()
'''
    return code


def generate_playwright_script(session: Dict[str, Any]) -> str:
    """สร้างสคริปต์ Playwright อัตโนมัติสำหรับกรอกฟอร์มจริงทาง UI ในกรณีที่ยิง API ตรงไม่ได้"""
    url = session.get("url", "https://example.com")
    fields = session.get("formFields", [])
    submit_btn = session.get("submitButton")

    lines = []
    for f in fields:
        label = f.get("label") or f.get("name") or f.get("id") or "ฟิลด์"
        selector = f.get("selector") or (f"#{f.get('id')}" if f.get("id") else f"[name='{f.get('name')}']")
        val = f.get("value", "")
        f_type = f.get("type", "text")

        safe_val = str(val).replace("'", "\\'")
        if f_type == "checkbox":
            lines.append(f"        # {label}")
            lines.append(f"        await page.locator('{selector}').set_checked({bool(val)})")
        elif f_type == "radio":
            lines.append(f"        # {label}")
            lines.append(f"        await page.locator('{selector}').check()")
        else:
            lines.append(f"        # {label}")
            lines.append(f"        await page.locator('{selector}').fill('{safe_val}')")

    fields_code = "\n".join(lines) if lines else "        # ไม่พบรายการฟิลด์ที่บันทึก"

    submit_action = ""
    if submit_btn and submit_btn.get("selector"):
        submit_action = f"        # กดปุ่ม {submit_btn.get('text', 'Submit')}\n        await page.locator('{submit_btn['selector']}').click()"
    else:
        submit_action = "        # กดปุ่ม Submit อัตโนมัติ\n        await page.locator('button[type=\"submit\"]').click()"

    cookies_list = session.get("cookies", [])
    cookies_code = ""
    if cookies_list:
        clean_cookies = []
        for c in cookies_list:
            if "name" in c and "value" in c:
                item = {"name": c["name"], "value": c["value"]}
                if "domain" in c and c["domain"]:
                    item["domain"] = c["domain"]
                if "path" in c and c["path"]:
                    item["path"] = c["path"]
                clean_cookies.append(item)
        if clean_cookies:
            cookies_code = f"        # 🍪 Inject Captured Cookies for instant authenticated session!\n        await context.add_cookies({json.dumps(clean_cookies, indent=8)})\n"

    code = f'''#!/usr/bin/env python3
# ==============================================================================
# 🎭 Playwright Browser Automation Script
# Fallback Route: สำหรับใช้กรณีที่ API ยิงตรงไม่ได้ (ติด Cloudflare / Captcha / Signatures)
# ==============================================================================

import asyncio
from playwright.async_api import async_playwright

async def run_form_automation():
    async with async_playwright() as p:
        # เปิดเบราว์เซอร์ Chromium จำลองสภาพแวดล้อมคนใช้จริง
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={{"width": 1280, "height": 800}},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
{cookies_code}        page = await context.new_page()

        print("🌐 กำลังเปิดหน้าเว็บ: {url}")
        await page.goto("{url}", wait_until="networkidle")

        print("📝 กำลังกรอกข้อมูลลงฟอร์มอัตโนมัติตามพฤติกรรมจริง...")
{fields_code}

        print("🔘 กำลังกดส่งข้อมูล (Submit)...")
{submit_action}

        # รอให้ระบบปลายทางประมวลผล
        await page.wait_for_timeout(3000)
        print("✅ ดำเนินการกรอกฟอร์มและส่งข้อมูลสำเร็จเรียบร้อยแล้ว!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_form_automation())
'''
    return code
