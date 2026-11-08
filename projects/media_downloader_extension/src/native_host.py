#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔌 Chrome Native Messaging Host for Universal Media Grabber
ช่วยให้ตัว Chrome Extension สามารถสั่งปลุก (Auto-Start) Companion Server (127.0.0.1:8765)
ขึ้นมาทำงานเองโดยอัตโนมัติทันทีที่ต้องการแปลงไฟล์ โดยที่ผู้ใช้ไม่ต้องเปิด Terminal เอง
"""
import json
import os
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SERVER_SCRIPT = BASE_DIR / "src" / "companion_server.py"
SERVER_URL = "http://127.0.0.1:8765/api/health"


def is_server_alive() -> bool:
    try:
        with urllib.request.urlopen(SERVER_URL, timeout=0.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return bool(data.get("ok"))
    except Exception:
        return False


def ensure_companion_server_started() -> dict:
    if is_server_alive():
        return {"ok": True, "status": "already_running", "port": 8765}

    log_file = BASE_DIR / "data" / "companion_server.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    out = open(log_file, "a", encoding="utf-8")

    subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT), "8765"],
        cwd=str(BASE_DIR),
        stdout=out,
        stderr=out,
        start_new_session=True,
    )

    for _ in range(25):
        time.sleep(0.2)
        if is_server_alive():
            return {"ok": True, "status": "started_now", "port": 8765}

    return {"ok": False, "error": "Failed to start companion server within timeout"}


def read_native_message():
    raw_length = sys.stdin.buffer.read(4)
    if len(raw_length) == 0:
        return None
    message_length = struct.unpack("@I", raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)


def send_native_message(payload: dict):
    encoded = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(struct.pack("@I", len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--ensure":
        res = ensure_companion_server_started()
        print(json.dumps(res, ensure_ascii=False))
        sys.exit(0 if res.get("ok") else 1)

    try:
        msg = read_native_message()
        res = ensure_companion_server_started()
        send_native_message(res)
    except Exception as e:
        send_native_message({"ok": False, "error": str(e)})

