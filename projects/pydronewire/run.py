#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛸 pyDroneWire Launcher CLI
ระบบควบคุมโดรน FLOW-UFO (KY UFO) ผ่านโปรโตคอล UDP/RTSP พร้อม Optical Flow HUD & Web Controller
"""
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_PYTHON = BASE_DIR / ".venv" / "bin" / "python"
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def print_banner():
    print("=" * 72)
    print("🛸 pyDroneWire — FLOW-UFO Reverse-Engineered Drone Controller")
    print("   ควบคุมการบิน UDP (7099) + สตรีมกล้อง RTSP (7070) + Optical Flow HUD")
    print("=" * 72)


def interactive_menu():
    while True:
        print_banner()
        print("เลือกโหมดการทำงาน:")
        print("  [1] 🌐 เปิด Web Controller (ควบคุมผ่านเบราว์เซอร์ / มือถือ)")
        print("  [2] 🎮 เปิด Desktop HUD Controller (OpenCV + DJI HUD + Optical Flow)")
        print("  [3] 🧪 รันชุดทดสอบ Unit Tests (pytest / unittest)")
        print("  [0] ออกจากโปรแกรม")
        print("-" * 72)

        choice = input("👉 เลือกเมนู (0-3): ").strip()
        if choice == "0":
            break
        elif choice == "1":
            subprocess.run([PYTHON_EXE, str(BASE_DIR / "web_controller.py")], cwd=str(BASE_DIR))
        elif choice == "2":
            subprocess.run([PYTHON_EXE, str(BASE_DIR / "drone_controller.py")], cwd=str(BASE_DIR))
        elif choice == "3":
            subprocess.run([PYTHON_EXE, "-m", "unittest", "discover", "-s", "tests"], cwd=str(BASE_DIR))
        else:
            print("❌ ตัวเลือกไม่ถูกต้อง\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ["web", "server"]:
            subprocess.run([PYTHON_EXE, str(BASE_DIR / "web_controller.py")] + sys.argv[2:], cwd=str(BASE_DIR))
        elif cmd in ["desktop", "hud", "fly"]:
            subprocess.run([PYTHON_EXE, str(BASE_DIR / "drone_controller.py")] + sys.argv[2:], cwd=str(BASE_DIR))
        elif cmd in ["test", "tests"]:
            subprocess.run([PYTHON_EXE, "-m", "unittest", "discover", "-s", "tests"], cwd=str(BASE_DIR))
        else:
            print("วิธีใช้: python3 run.py [web | desktop | test]")
    else:
        interactive_menu()
