import json
import csv
import random
import string
import sys
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import EXPORTS_DIR, JSON_DIR

FIRST_NAMES = ["สมชาย", "กิตติพงษ์", "อัครเดช", "ณภัทร", "ธีรภัทร", "วรัญญา", "ชลธิชา", "กมลวรรณ", "ปิยะพร", "ศิริพร"]
LAST_NAMES = ["สุขสมบูรณ์", "เจริญกิจ", "รัตนเดชา", "วัฒนากูล", "ทองประเสริฐ", "รุ่งเรือง", "ประสิทธิ์โชค", "เกียรติสกุล"]
DOMAINS = ["gmail.com", "hotmail.com", "outlook.co.th", "icloud.com", "yahoo.com"]

class UserAccountGenerator:
    """ระบบสร้างข้อมูลบัญชีผู้ใช้จำลอง (Synthetic User Accounts) สำหรับทดสอบระบบ E-Commerce และ GraphQL"""

    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        chars = string.ascii_letters + string.digits + "!@#$%"
        return "".join(random.choice(chars) for _ in range(length))

    @staticmethod
    def generate_accounts(count: int = 10) -> List[Dict[str, Any]]:
        accounts = []
        for i in range(1, count + 1):
            fname = random.choice(FIRST_NAMES)
            lname = random.choice(LAST_NAMES)
            latin_user = f"user_{random.randint(1000, 9999)}_{i}"
            domain = random.choice(DOMAINS)
            email = f"{latin_user}@{domain}"
            phone = f"08{random.randint(10000000, 99999999)}"

            accounts.append({
                "id": i,
                "first_name": fname,
                "last_name": lname,
                "full_name": f"{fname} {lname}",
                "username": latin_user,
                "email": email,
                "password": UserAccountGenerator.generate_random_password(),
                "phone": phone,
                "role": "customer",
                "status": "active"
            })

        # Save to JSON
        json_path = JSON_DIR / "generated_users.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(accounts, f, ensure_ascii=False, indent=2)

        # Save to CSV
        csv_path = EXPORTS_DIR / "generated_users.csv"
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "full_name", "username", "email", "password", "phone", "role", "status"])
            writer.writeheader()
            for acc in accounts:
                row = {k: acc[k] for k in ["id", "full_name", "username", "email", "password", "phone", "role", "status"]}
                writer.writerow(row)

        return accounts
