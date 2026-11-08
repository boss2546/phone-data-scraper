#!/usr/bin/env python3
"""
Read-only preflight check for a KY UFO-family drone (e.g. GT50).
Sends NOTHING that moves motors: only the 1 Hz heartbeat packet and an RTSP OPTIONS request.

Usage (after joining the drone's WiFi):
    python3 check_gt50.py              # auto-detect gateway
    python3 check_gt50.py 192.168.1.1  # force IP
"""
import socket, subprocess, sys, re, time

CTRL_PORT, RTSP_PORT = 7099, 7070
HEARTBEAT = bytes([0x01, 0x01])   # ตามโค้ด drone_controller.py (README ระบุค่าอื่น แต่โค้ดจริงใช้ค่านี้)

def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception as e:
        return f"(error: {e})"

def gateway():
    m = re.search(r"gateway:\s*(\S+)", sh("route -n get default"))
    return m.group(1) if m else "192.168.1.1"

def main():
    ip = sys.argv[1] if len(sys.argv) > 1 else gateway()
    print(f"[1] Target IP: {ip}")
    print("    WiFi:", sh("networksetup -getairportnetwork en0") or "(unknown)")
    print("    Ping:", "OK" if "1 packets received" in sh(f"ping -c1 -t2 {ip}") else "NO REPLY")

    print(f"[2] RTSP port {RTSP_PORT} (video)")
    try:
        s = socket.create_connection((ip, RTSP_PORT), timeout=3)
        s.sendall(f"OPTIONS rtsp://{ip}:{RTSP_PORT}/webcam RTSP/1.0\r\nCSeq: 1\r\n\r\n".encode())
        print("    ->", s.recv(512).decode(errors="replace").splitlines()[:1] or "connected, no reply")
        s.close()
    except Exception as e:
        print("    -> FAIL:", e)

    print(f"[3] UDP {CTRL_PORT} heartbeat (control), listening 3 s for any reply")
    u = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); u.settimeout(0.5)
    got = None
    t0 = time.time()
    while time.time() - t0 < 3:
        u.sendto(HEARTBEAT, (ip, CTRL_PORT))
        try:
            got = u.recvfrom(256); break
        except socket.timeout:
            pass
    print("    -> reply:", got[0].hex() if got else "none (normal for some drones; UDP is connectionless)")

    print("[4] Grab one video frame via OpenCV")
    try:
        import os, cv2
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp|max_delay;500000"
        import threading
        res = {}
        def grab():
            cap = cv2.VideoCapture(f"rtsp://{ip}:{RTSP_PORT}/webcam", cv2.CAP_FFMPEG)
            res["ok"], res["frame"] = cap.read(); cap.release()
        th = threading.Thread(target=grab, daemon=True); th.start(); th.join(10)
        if res.get("ok"):
            f = res["frame"]; print(f"    -> OK {f.shape[1]}x{f.shape[0]}")
            cv2.imwrite("gt50_frame.jpg", f); print("    saved gt50_frame.jpg")
        else:
            print("    -> no frame within 10 s")
    except ImportError:
        print("    -> opencv not installed (pip install -r requirements.txt)")

if __name__ == "__main__":
    main()
