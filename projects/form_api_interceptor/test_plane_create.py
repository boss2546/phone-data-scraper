#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
🚀 Plane Auto-Issue Creator (ทดสอบยิงสร้าง Task อัตโนมัติ)
=============================================================================
สคริปต์นี้สร้างขึ้นจากข้อมูลที่ Extension ดักจับมาจาก devspace.mergesoft.cloud
โครงการ: Joint Digital Service Platform (JDSP)
"""

import sys
import json
import requests
from datetime import date

# ---------------------------------------------------------------------------
# กำหนดค่าพารามิเตอร์ของระบบ JDSP
# ---------------------------------------------------------------------------
BASE_URL = "https://devspace.mergesoft.cloud/api/workspaces/aiis/projects/8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe/issues/"
PROJECT_ID = "8fa8b7f5-902b-4ea4-ba03-a6858a9b15fe"

# แมป State ID จากระบบจริงที่ดักจับได้
STATES = {
    "backlog": "cb92c938-8c41-4d83-be57-e40cbd747fec",
    "pm_review": "18c704ce-24eb-4030-b528-3193ecbd3e46",
    "ready_for_dev": "a0ee8fec-8941-4a58-b436-6f17d1ccb362",
    "in_dev": "d80de3de-2a56-4233-943a-d0629823d56a",
    "done": "b0b74c6d-8ac7-4b0a-8b1b-28683e91c0b3"
}

# แมป Label ID
LABELS = {
    "requirement": "ef8ce9d0-7900-4e10-b306-ab560d4c58c9",
    "development": "10f931d9-567d-4737-a06b-0617fb7b7358",
    "backend": "d101c238-85f3-433f-b1c7-bbdc109e146f",
    "frontend": "1db48be4-d864-444c-b4ca-8775aba10a84",
    "bug": "e1e0b6f1-371d-4b89-ab5d-f75864a88d37"
}

def create_issue(title, description, priority="medium", state_key="pm_review", label_key=None, cookie_str=""):
    """
    ฟังก์ชันยิงสร้าง Task/Issue บน Plane
    """
    if not cookie_str:
        print("⚠️ ยังไม่ได้ใส่ Cookie หรือ Token ค่ะบอส!")
        print("💡 วิธีเอา Cookie: เปิด Chrome -> F12 -> Network -> คลิกขวาที่ call ไหนก็ได้ของ devspace -> Copy -> Copy as cURL (bash) -> นำ Cookie มาวาง")
        return None

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": cookie_str
    }

    state_id = STATES.get(state_key, STATES["pm_review"])
    label_ids = [LABELS[label_key]] if label_key and label_key in LABELS else []

    payload = {
        "project_id": PROJECT_ID,
        "name": title,
        "description_html": f"<p>{description}</p>",
        "state_id": state_id,
        "priority": priority,
        "start_date": str(date.today()),
        "target_date": None,
        "assignee_ids": [],
        "label_ids": label_ids,
        "module_ids": None,
        "cycle_id": None
    }

    print(f"🚀 กำลังยิงสร้าง Task: '{title}' ไปยัง {BASE_URL}...")
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers, timeout=10)
        print(f"📡 Response Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print("=========================================================")
            print("🎉 สร้างสำเร็จ 100%! ข้อมูลบัตรงานใหม่:")
            print(f"📌 Task Number : JDSP-{data.get('sequence_id')}")
            print(f"📝 Title       : {data.get('name')}")
            print(f"🆔 Task ID     : {data.get('id')}")
            print(f"🚦 State ID    : {data.get('state_id')}")
            print(f"⏰ Created At  : {data.get('created_at')}")
            print("=========================================================")
            return data
        elif response.status_code == 401:
            print("❌ ผิดพลาด: 401 Unauthorized (Cookie หมดอายุ หรือไม่ได้ใส่ Cookie ค่ะ)")
            return None
        else:
            print(f"❌ เซิร์ฟเวอร์ตอบกลับรหัส {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"💥 เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
        return None

if __name__ == "__main__":
    # บอสสามารถวาง Cookie ที่ก็อปปี้มาจาก Chrome ใส่ตรงนี้ได้เลยค่ะ:
    MY_COOKIE = "" 
    
    # ถ้าส่งมาผ่าน argument เช่น: python3 test_plane_create.py "cookie_string"
    if len(sys.argv) > 1:
        MY_COOKIE = sys.argv[1]

    # ทดสอบยิงสร้างงาน
    create_issue(
        title="🤖 งานทดสอบระบบอัตโนมัติจาก Terminal (By Maymint)",
        description="ทดสอบยิงผ่าน Python Requests API ตรงสำเร็จเสร็จสิ้นใน 0.1 วินาที!",
        priority="high",
        state_key="pm_review",
        label_key="development",
        cookie_str=MY_COOKIE
    )
