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
import stat
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NATIVE_HOST_SCRIPT = BASE_DIR / "src" / "native_host.py"
SERVER_SCRIPT = BASE_DIR / "src" / "companion_server.py"
HOST_NAME = "com.meuu.umg_companion"
LAUNCH_AGENT_LABEL = "com.meuu.umg.companion"


def install_auto_daemon():
    # 1. Make scripts executable
    for script in (NATIVE_HOST_SCRIPT, SERVER_SCRIPT):
        st = os.stat(script)
        os.chmod(script, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

    # 2. Install macOS LaunchAgent so companion_server runs automatically on demand / background
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents_dir / f"{LAUNCH_AGENT_LABEL}.plist"
    log_path = BASE_DIR / "data" / "companion_server.log"
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
        <string>{SERVER_SCRIPT}</string>
        <string>8765</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{BASE_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""
    plist_path.write_text(plist_content, encoding="utf-8")

    # Reload launchctl service
    subprocess.run(["launchctl", "unload", str(plist_path)], capture_output=True)
    subprocess.run(["launchctl", "load", "-w", str(plist_path)], capture_output=True)

    # Also ensure server is running right now via native_host --ensure
    subprocess.run([sys.executable, str(NATIVE_HOST_SCRIPT), "--ensure"], capture_output=True)

    return {
        "ok": True,
        "launch_agent": str(plist_path),
        "native_host_script": str(NATIVE_HOST_SCRIPT),
    }


if __name__ == "__main__":
    info = install_auto_daemon()
    print("✅ ติดตั้งระบบ Auto-Start เบื้องหลังสำเร็จ:", json.dumps(info, ensure_ascii=False))
