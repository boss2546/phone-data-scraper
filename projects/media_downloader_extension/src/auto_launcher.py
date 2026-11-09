#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⚙️ Auto-Start & Native Messaging Installer for Universal Media Grabber
ติดตั้ง:
1. macOS LaunchAgent (com.meuu.umg.companion.plist) ให้เซิร์ฟเวอร์แปลงไฟล์พร้อมทำงานอัตโนมัติและฟื้นคืนชีพเองเสมอ
2. Chrome Native Messaging Host เพื่อให้ Chrome Extension สั่งปลุกเซิร์ฟเวอร์เองได้อัตโนมัติ
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NATIVE_HOST_SCRIPT = BASE_DIR / "src" / "native_host.py"
SERVER_SCRIPT = BASE_DIR / "src" / "companion_server.py"
GALLERY_HTML = BASE_DIR / "test_gallery.html"
HOST_NAME = "com.meuu.umg_companion"
LAUNCH_AGENT_LABEL = "com.meuu.umg.companion"

# คัดลอก Runtime ไปไว้ที่ ~/.umg_companion (นอก ~/Desktop) เพื่อไม่ให้ติดสิทธิ์ macOS TCC (Operation not permitted)
RUNTIME_DIR = Path.home() / ".umg_companion"
RUNTIME_SRC_DIR = RUNTIME_DIR / "src"
RUNTIME_SERVER_SCRIPT = RUNTIME_SRC_DIR / "companion_server.py"
RUNTIME_NATIVE_SCRIPT = RUNTIME_SRC_DIR / "native_host.py"


def sync_tcc_safe_runtime():
    RUNTIME_SRC_DIR.mkdir(parents=True, exist_ok=True)
    (RUNTIME_DIR / "data").mkdir(parents=True, exist_ok=True)
    shutil.copy2(SERVER_SCRIPT, RUNTIME_SERVER_SCRIPT)
    shutil.copy2(NATIVE_HOST_SCRIPT, RUNTIME_NATIVE_SCRIPT)
    if GALLERY_HTML.exists():
        shutil.copy2(GALLERY_HTML, RUNTIME_DIR / "test_gallery.html")
    test_assets_src = BASE_DIR / "data" / "test_assets"
    if test_assets_src.exists():
        shutil.copytree(test_assets_src, RUNTIME_DIR / "data" / "test_assets", dirs_exist_ok=True)

    for script in (NATIVE_HOST_SCRIPT, SERVER_SCRIPT, RUNTIME_NATIVE_SCRIPT, RUNTIME_SERVER_SCRIPT):
        if script.exists():
            st = os.stat(script)
            os.chmod(script, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def install_auto_daemon():
    sync_tcc_safe_runtime()

    # ติดตั้ง Chrome Native Messaging Host ชี้ไปยัง ~/.umg_companion/src/native_host.py
    nm_dirs = [
        Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts",
        Path.home() / "Library" / "Application Support" / "BraveSoftware" / "Brave-Browser" / "NativeMessagingHosts",
        Path.home() / "Library" / "Application Support" / "Chromium" / "NativeMessagingHosts",
    ]
    nm_manifest = {
        "name": HOST_NAME,
        "description": "Universal Media Grabber Auto-Start Companion Host",
        "path": str(RUNTIME_NATIVE_SCRIPT),
        "type": "stdio",
        "allowed_origins": [
            "chrome-extension://*/",
        ],
    }
    for d in nm_dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{HOST_NAME}.json").write_text(json.dumps(nm_manifest, indent=2), encoding="utf-8")
        except Exception:
            pass

    # ติดตั้ง macOS LaunchAgent ชี้ไปยัง ~/.umg_companion/src/companion_server.py (ไม่ติด TCC ~/Desktop)
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents_dir / f"{LAUNCH_AGENT_LABEL}.plist"
    log_path = RUNTIME_DIR / "data" / "companion_server.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCH_AGENT_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{RUNTIME_SERVER_SCRIPT}</string>
        <string>8765</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{RUNTIME_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""
    plist_path.write_text(plist_content, encoding="utf-8")

    # Reload launchctl service and restart running process so latest synced code is active
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    try:
        res = subprocess.run(["lsof", "-ti", ":8765"], capture_output=True, text=True, timeout=3)
        for pid_str in res.stdout.strip().splitlines():
            if pid_str.strip().isdigit():
                subprocess.run(["kill", "-9", pid_str.strip()], check=False)
    except Exception:
        pass
    subprocess.run(["launchctl", "load", "-w", str(plist_path)], capture_output=True)

    # Also ensure server is running right now via native_host --ensure
    subprocess.run([sys.executable, str(RUNTIME_NATIVE_SCRIPT), "--ensure"], capture_output=True)

    return {
        "ok": True,
        "runtime_dir": str(RUNTIME_DIR),
        "launch_agent": str(plist_path),
        "native_host_script": str(RUNTIME_NATIVE_SCRIPT),
    }


if __name__ == "__main__":
    info = install_auto_daemon()
    print("✅ ติดตั้งระบบ Auto-Start เบื้องหลังสำเร็จ:", json.dumps(info, ensure_ascii=False))

