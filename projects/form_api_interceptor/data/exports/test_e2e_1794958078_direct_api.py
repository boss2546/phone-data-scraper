#!/usr/bin/env python3
# ==============================================================================
# 🚀 Python Direct API Automation Script (Ready-to-Run with Cookies 🍪 & Auth 🔑)
# Generated automatically from Form & API Interceptor capture
# Target URL: https://httpbin.org/post
# Method: POST
# ==============================================================================

import requests
import json
import sys

def execute_request():
    url = "https://httpbin.org/post"
    headers = {
    "Content-Type": "application/json"
}
    payload = {
    "first_name": "กฤษณะ",
    "email": "boss@meuu.club"
}

    print(f"📡 กำลังส่งคำขอ [POST] ไปยัง: {url} ...")
    try:
        response = requests.post(
            url,
            headers=headers, json=payload,
            timeout=15
        )
        print(f"📥 สถานะการตอบกลับ: {response.status_code} ({response.reason})")
        
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
        print(f"❌ เกิดข้อผิดพลาด: {e}", file=sys.stderr)
        return None

if __name__ == "__main__":
    execute_request()
