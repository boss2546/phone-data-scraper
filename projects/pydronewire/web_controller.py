#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pyDroneWire Web Controller
==========================
หน้าเว็บควบคุมโดรน KY UFO / FLOW-UFO / GT50 ผ่านมือถือหรือคอมพิวเตอร์
  - วิดีโอสด (MJPEG) + จอยสติ๊กสัมผัส 2 ข้าง + ปุ่มคำสั่งมาตรฐาน
  - ช่องกรอก URL เพื่อส่งภาพต่อไปสตรีมที่อื่น (RTMP / RTMPS / SRT) ผ่าน ffmpeg

เริ่มต้นแบบปลอดภัย (DRY RUN = ไม่ส่งคำสั่งใดๆ ไปที่โดรน):
    python3 web_controller.py
ส่งคำสั่งจริง (ถอดใบพัดก่อนทดสอบครั้งแรกเสมอ):
    python3 web_controller.py --live
ทดสอบหน้าเว็บโดยไม่มีโดรน:
    python3 web_controller.py --demo

โปรโตคอลอ้างอิงจาก drone_controller.py (ต้นฉบับ) ทุกประการ
"""
import argparse
import json
import logging
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from urllib.parse import urlparse

# ปิดข้อความรกจาก ffmpeg/OpenCV (เช่น "Missing packets; dropping frame") — ต้องตั้งก่อน import cv2
# ใส่ --verbose ถ้าต้องการดูข้อความเหล่านี้เพื่อแก้ปัญหาวิดีโอ
if "--verbose" not in sys.argv:
    os.environ.setdefault("OPENCV_FFMPEG_LOGLEVEL", "-8")   # AV_LOG_QUIET
    os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

import cv2  # noqa: E402
import numpy as np  # noqa: E402
from flask import Flask, Response, jsonify, request, send_file  # noqa: E402

__version__ = "1.2.0"
log = logging.getLogger("pydronewire")

HERE = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(HERE, "web")
OUTPUT_DIR = os.path.expanduser("~/DroneCaptures")

CTRL_HZ = 20
HEARTBEAT_HZ = 1
DEADMAN_S = 0.4            # ไม่ได้รับค่าก้านเกินนี้ -> คืนก้านกลาง (ลอยนิ่ง)
SPEED_SCALES = [0.30, 0.60, 1.00]

# ค่า cmd byte ตามโค้ดต้นฉบับ (drone_controller.py) — ไม่ใช่ตารางใน README
CMD_TAKEOFF_LAND = 0x01    # สลับขึ้นบิน/ลงจอด (toggle)
CMD_ESTOP = 0x02
CMD_FLIP = 0x08
CMD_HEADLESS = 0x10
CMD_GYRO = 0x80


# ───────────────────────── Protocol ─────────────────────────
def build_ctrl(roll, pitch, throttle, yaw, cmd, speed=0x02):
    pkt = [0x03, 0x66, 0x14, roll, pitch, throttle, yaw, cmd, speed]
    pkt += [0x00] * 10
    chk = 0
    for b in pkt[3:19]:
        chk ^= b
    pkt.append(chk)
    pkt.append(0x99)
    return bytes(pkt)


def stick_byte(v, scale):
    """ค่าก้าน -1..1 -> byte 0..255 (กลาง 0x80) คูณสัดส่วนความเร็ว"""
    try:
        v = float(v)
    except (TypeError, ValueError):
        v = 0.0
    if v != v:  # NaN
        v = 0.0
    v = max(-1.0, min(1.0, v))
    return int(max(0, min(255, 0x80 + round(v * 127 * scale))))


# ───────────────────────── Drone ─────────────────────────
class Drone:
    def __init__(self, ip, port, live, failsafe_land=0.0, video=None):
        self.ip, self.port, self.live = ip, port, live
        self.failsafe_land = failsafe_land
        self.video = video
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.lock = threading.RLock()
        self.running = True
        self.sticks = (0.0, 0.0, 0.0, 0.0)   # roll, pitch, throttle, yaw (-1..1)
        self.last_input = 0.0
        self.armed = False
        self.flying = False
        self.flight_start = 0.0
        self.speed_mode = 0                  # เริ่มที่ 30% เพื่อความปลอดภัย
        self.camera = 1
        self.cmd = 0
        self.cmd_until = 0.0
        self.status = "พร้อม"
        self.tx = self.hb = self.rx = 0
        self.no_client_since = time.monotonic()
        self._failsafe_fired = False
        self.last_tx = (128, 128, 128, 128, 0)
        self.last_pkt = ""
        self.send_errors = 0

    # ---- low level ----
    def _send(self, data):
        if not self.live:
            return False
        try:
            self.sock.sendto(data, (self.ip, self.port))
            return True
        except OSError:
            self.send_errors += 1
            return False

    def _timed(self, cmd, dur):
        self.cmd = cmd
        self.cmd_until = time.monotonic() + dur

    def start(self):
        for fn, name in ((self._ctrl_loop, "ctrl"), (self._hb_loop, "hb"), (self._rx_loop, "rx")):
            threading.Thread(target=fn, daemon=True, name=name).start()

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass

    # ---- threads ----
    def _ctrl_loop(self):
        interval = 1.0 / CTRL_HZ
        nxt = time.monotonic()
        while self.running:
            now = time.monotonic()
            with self.lock:
                if self.cmd and now >= self.cmd_until:
                    self.cmd = 0
                active = self.armed or self.cmd == CMD_ESTOP
                if now - self.last_input <= DEADMAN_S:
                    r, p, t, y = self.sticks
                else:
                    r = p = t = y = 0.0
                sc = SPEED_SCALES[self.speed_mode]
                rb, pb, tb, yb = (stick_byte(r, sc), stick_byte(p, sc),
                                  stick_byte(t, sc), stick_byte(y, sc))
                cmd = self.cmd
                # failsafe (เปิดใช้เฉพาะเมื่อกำหนด --failsafe-land)
                if (self.failsafe_land > 0 and self.flying and not self._failsafe_fired
                        and self.no_client_since is not None
                        and now - self.no_client_since > self.failsafe_land
                        and self.cmd == 0):
                    self._failsafe_fired = True
                    self.status = "สูญเสียการเชื่อมต่อ — สั่งลงจอดอัตโนมัติ"
                    self._timed(CMD_TAKEOFF_LAND, 1.0)
                    self.flying = False
                    cmd = self.cmd
            if active:
                pkt = build_ctrl(rb, pb, tb, yb, cmd)
                self._send(pkt)
                self.tx += 1
                self.last_tx = (rb, pb, tb, yb, cmd)
                self.last_pkt = pkt.hex()
            nxt += interval
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)
            else:
                nxt = time.monotonic()

    def _hb_loop(self):
        while self.running:
            if self._send(bytes([0x01, 0x01])):
                self.hb += 1
            time.sleep(1.0 / HEARTBEAT_HZ)

    def _rx_loop(self):
        self.sock.settimeout(1.0)
        while self.running:
            if not self.live:
                time.sleep(0.5)
                continue
            try:
                self.sock.recvfrom(256)
                self.rx += 1
            except (socket.timeout, OSError):
                time.sleep(0.05)

    # ---- API ----
    def set_sticks(self, r, p, t, y):
        def c(v):
            try:
                v = float(v)
            except (TypeError, ValueError):
                return 0.0
            if v != v:
                return 0.0
            return max(-1.0, min(1.0, v))
        with self.lock:
            self.sticks = (c(r), c(p), c(t), c(y))
            self.last_input = time.monotonic()

    def zero_sticks(self):
        with self.lock:
            self.sticks = (0.0, 0.0, 0.0, 0.0)
            self.last_input = 0.0

    def command(self, name, value=None):
        """คืน (ok, ข้อความ) — มีการตรวจสถานะก่อนส่งคำสั่งแบบ toggle เพื่อไม่ให้สลับผิดทาง"""
        now = time.monotonic()
        with self.lock:
            if name == "arm":
                if self.armed:
                    return False, "ARM อยู่แล้ว"
                self.armed = True
                return self._ok("ARM — เริ่มส่งคำสั่งควบคุม")
            if name == "disarm":
                if self.flying:
                    return False, "กำลังบินอยู่ — ลงจอดก่อน หรือกด STOP"
                self.armed = False
                self.cmd = 0
                self.zero_sticks()
                return self._ok("DISARM")
            if name == "takeoff":
                if self.flying:
                    return False, "บินอยู่แล้ว (ปฏิเสธเพื่อไม่ให้คำสั่งสลับเป็นลงจอด)"
                self.armed = True
                self.zero_sticks()
                self._timed(CMD_TAKEOFF_LAND, 1.0)
                self.flying = True
                self.flight_start = now
                self._failsafe_fired = False
                return self._ok("ขึ้นบิน")
            if name == "land":
                if not self.flying:
                    return False, "ยังไม่ได้บิน (ปฏิเสธเพื่อไม่ให้คำสั่งสลับเป็นขึ้นบิน)"
                self.zero_sticks()
                self._timed(CMD_TAKEOFF_LAND, 1.0)
                self.flying = False
                return self._ok("ลงจอด")
            if name == "estop":
                self.zero_sticks()
                self._timed(CMD_ESTOP, 1.0)
                self.flying = False
                self.status = "!! EMERGENCY STOP !!"
                return True, self.status
            if name == "flip":
                if not self.flying:
                    return False, "ตีลังกาได้เฉพาะตอนบิน"
                self._timed(CMD_FLIP, 0.5)
                return self._ok("ตีลังกา")
            if name == "headless":
                if not self.armed:
                    return False, "ต้อง ARM ก่อน"
                self._timed(CMD_HEADLESS, 0.5)
                return self._ok("สลับโหมด Headless")
            if name == "calibrate":
                if self.flying:
                    return False, "คาลิเบรตไจโรได้เฉพาะตอนอยู่บนพื้น"
                if not self.armed:
                    return False, "ต้อง ARM ก่อน (วางโดรนบนพื้นราบ)"
                self._timed(CMD_GYRO, 1.0)
                return self._ok("กำลังคาลิเบรตไจโร...")
            if name == "hover":
                self.zero_sticks()
                return self._ok("ลอยนิ่ง")
            if name == "speed":
                try:
                    v = int(value)
                except (TypeError, ValueError):
                    return False, "ค่าไม่ถูกต้อง"
                if v not in (0, 1, 2):
                    return False, "ค่าไม่ถูกต้อง"
                self.speed_mode = v
                return self._ok("ความแรงก้าน %d%%" % int(SPEED_SCALES[v] * 100))
            if name == "camera":
                try:
                    n = int(value)
                except (TypeError, ValueError):
                    return False, "ค่าไม่ถูกต้อง"
                if n not in (1, 2):
                    return False, "ค่าไม่ถูกต้อง"
                self._send(bytes([0x06, n]))
                self.camera = n
                if self.video:
                    self.video.request_reconnect(1.5)
                return self._ok("สลับกล้อง %d — กำลังเชื่อมต่อวิดีโอใหม่" % n)
        return False, "ไม่รู้จักคำสั่ง"

    def _ok(self, msg):
        self.status = msg
        return True, msg

    def snapshot(self):
        now = time.monotonic()
        with self.lock:
            elapsed = (now - self.flight_start) if self.flying else 0.0
            sc = SPEED_SCALES[self.speed_mode]
            fresh = now - self.last_input <= DEADMAN_S
            # ค่าที่ส่งออกจริง (หลังคูณความแรงและ deadman) เป็น % ของก้านเต็ม: roll, pitch, throttle, yaw
            out = [int(round(v * sc * 100)) if fresh else 0 for v in self.sticks]
            return {
                "scale": sc,
                "out": out,
                "live": self.live,
                "armed": self.armed,
                "flying": self.flying,
                "flight_s": int(elapsed),
                "speed": self.speed_mode,
                "camera": self.camera,
                "status": self.status,
                "tx": self.tx,
                "rx": self.rx,
                "hb": self.hb,
                "errs": self.send_errors,
                "pkt": self.last_pkt,
                "target": "%s:%d" % (self.ip, self.port),
                "sticks": [round(v, 2) for v in self.sticks],
            }


# ───────────────────────── Video ─────────────────────────
class VideoSource(threading.Thread):
    def __init__(self, url, demo=False):
        super().__init__(daemon=True, name="video")
        self.url, self.demo = url, demo
        self.lock = threading.Lock()
        self.frame = None
        self.jpeg = None
        self.fid = 0
        self.last_t = 0.0
        self.running = True
        self.reconnect_at = 0.0
        self._reconnect = False
        self._times = []

    def request_reconnect(self, delay=1.0):
        self.reconnect_at = time.monotonic() + delay
        self._reconnect = True

    def _publish(self, frame):
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not ok:
            return
        now = time.monotonic()
        with self.lock:
            self.frame = frame
            self.jpeg = buf.tobytes()
            self.fid += 1
            self.last_t = now
            self._times.append(now)
            self._times = [t for t in self._times if now - t < 5.0]

    def get_jpeg(self):
        with self.lock:
            return self.jpeg, self.fid

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def info(self):
        now = time.monotonic()
        with self.lock:
            live = self.last_t > 0 and (now - self.last_t) < 5.0
            fps = len([t for t in self._times if now - t < 2.0]) / 2.0
            size = None if self.frame is None else [int(self.frame.shape[1]), int(self.frame.shape[0])]
            ever = self.last_t > 0
        state = "live" if live else ("lost" if ever else "connecting")
        return {"live": live, "state": state, "fps": round(fps, 1), "size": size}

    def run(self):
        if self.demo:
            self._run_demo()
        else:
            self._run_rtsp()

    def _run_rtsp(self):
        os.environ.setdefault(
            "OPENCV_FFMPEG_CAPTURE_OPTIONS",
            "rtsp_transport;udp|max_delay;500000|reorder_queue_size;0")
        while self.running:
            self._reconnect = False
            cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
            fails = 0
            while self.running and not self._reconnect:
                ok, f = cap.read()
                if ok and f is not None:
                    self._publish(f)
                    fails = 0
                else:
                    fails += 1
                    if fails > 30:
                        break
                    time.sleep(0.03)
            cap.release()
            wait = max(1.0, self.reconnect_at - time.monotonic()) if self._reconnect else 1.5
            end = time.monotonic() + wait
            while self.running and time.monotonic() < end:
                time.sleep(0.1)

    def _run_demo(self):
        w, h = 640, 352
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        base = np.zeros((h, w, 3), np.uint8)
        base[:, :, 0] = (60 + 60 * (1 - yy)).astype(np.uint8)
        base[:, :, 1] = (40 + 50 * (1 - yy)).astype(np.uint8)
        base[:, :, 2] = (30 + 30 * (1 - yy)).astype(np.uint8)
        t0 = time.monotonic()
        while self.running:
            t = time.monotonic() - t0
            f = base.copy()
            for x in range(0, w, 64):
                cv2.line(f, (x, 0), (x, h), (80, 80, 80), 1)
            for y in range(0, h, 64):
                cv2.line(f, (0, y), (w, y), (80, 80, 80), 1)
            cx = int(w / 2 + 200 * np.sin(t))
            cy = int(h / 2 + 90 * np.cos(t * 1.3))
            cv2.circle(f, (cx, cy), 28, (80, 200, 120), -1)
            cv2.putText(f, "DEMO VIDEO " + datetime.now().strftime("%H:%M:%S"), (16, 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
            self._publish(f)
            time.sleep(1 / 15)


# ───────────────────────── Restream (ffmpeg) ─────────────────────────
ALLOWED_SCHEMES = ("rtmp", "rtmps", "srt")


class Restreamer:
    """ส่งภาพที่ได้จากโดรนต่อไปยัง RTMP/RTMPS/SRT ด้วย ffmpeg (เข้ารหัส H.264 + เสียงเงียบ)"""

    def __init__(self, video, fps=15):
        self.video, self.fps = video, fps
        self.proc = None
        self.stop_evt = threading.Event()
        self.lock = threading.Lock()
        self.error = ""
        self.sent = 0
        self.started = 0.0
        self.target = ""
        self._url = ""

    @staticmethod
    def validate(url):
        url = (url or "").strip()
        if not url or any(ch in url for ch in " \t\r\n\0"):
            raise ValueError("URL ไม่ถูกต้อง")
        u = urlparse(url)
        if u.scheme.lower() not in ALLOWED_SCHEMES or not u.hostname:
            raise ValueError("รองรับเฉพาะ rtmp:// rtmps:// srt://")
        return url

    @staticmethod
    def mask(url):
        u = urlparse(url)
        port = ":%d" % u.port if u.port else ""
        return "%s://%s%s/••••" % (u.scheme.lower(), u.hostname, port)

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self, url):
        url = self.validate(url)
        with self.lock:
            if self.running:
                raise RuntimeError("กำลังสตรีมอยู่แล้ว")
            ff = shutil.which("ffmpeg")
            if not ff:
                raise RuntimeError("ไม่พบ ffmpeg — ติดตั้งด้วย: brew install ffmpeg")
            frame = self.video.get_frame()
            if frame is None:
                raise RuntimeError("ยังไม่มีภาพจากโดรนให้ส่งต่อ")
            h, w = frame.shape[:2]
            w -= w % 2
            h -= h % 2
            fmt = "mpegts" if url.lower().startswith("srt") else "flv"
            cmd = [ff, "-hide_banner", "-loglevel", "warning",
                   "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "%dx%d" % (w, h),
                   "-framerate", str(self.fps), "-i", "pipe:0",
                   "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                   "-c:v", "libx264", "-preset", "veryfast", "-tune", "zerolatency",
                   "-pix_fmt", "yuv420p", "-g", str(self.fps * 2),
                   "-b:v", "1200k", "-maxrate", "1200k", "-bufsize", "2400k",
                   "-c:a", "aac", "-b:a", "64k", "-shortest",
                   "-f", fmt, url]
            self.stop_evt.clear()
            self.error = ""
            self.sent = 0
            self._url = url
            self.target = self.mask(url)
            self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
                                         stdout=subprocess.DEVNULL, bufsize=0)
            self.started = time.monotonic()
            threading.Thread(target=self._feed, args=(self.proc, w, h), daemon=True).start()
            threading.Thread(target=self._read_err, args=(self.proc,), daemon=True).start()

    def _feed(self, proc, w, h):
        interval = 1.0 / self.fps
        nxt = time.monotonic()
        while not self.stop_evt.is_set() and proc.poll() is None:
            f = self.video.get_frame()
            if f is not None:
                if f.shape[1] != w or f.shape[0] != h:
                    f = cv2.resize(f, (w, h))
                try:
                    proc.stdin.write(f.tobytes())
                    self.sent += 1
                except (BrokenPipeError, OSError, ValueError):
                    break
            nxt += interval
            d = nxt - time.monotonic()
            if d > 0:
                time.sleep(d)
            else:
                nxt = time.monotonic()
        if not self.stop_evt.is_set() and not self.error:
            self.error = "การสตรีมหยุดเอง (ตรวจ URL / เครือข่าย / stream key)"

    def _read_err(self, proc):
        try:
            for line in iter(proc.stderr.readline, b""):
                txt = line.decode("utf-8", "replace").strip()
                if not txt:
                    continue
                txt = txt.replace(self._url, self.target)
                if not self.stop_evt.is_set():
                    self.error = txt[-160:]
        except Exception:
            pass

    def stop(self):
        self.stop_evt.set()
        p = self.proc
        if p is None:
            return
        try:
            p.stdin.close()
        except Exception:
            pass
        try:
            p.terminate()
            p.wait(timeout=3)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
        self.proc = None

    def status(self):
        run = self.running
        return {"running": run,
                "target": self.target if (run or self.error) else "",
                "sent": self.sent,
                "seconds": int(time.monotonic() - self.started) if run else 0,
                "error": self.error}


# ───────────────────────── Web app (Flask) ─────────────────────────
CONTROLLER_TIMEOUT = 1.5   # วินาทีที่ไม่ได้ยินจากเครื่องที่ควบคุม -> ถือว่าหลุด


def local_ips():
    ips = []
    try:
        out = subprocess.run(["ifconfig"], capture_output=True, text=True, timeout=3).stdout
        ips = re.findall(r"inet (\d+\.\d+\.\d+\.\d+)", out)
    except Exception:
        pass
    if not ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.255.255.255", 1))
            ips = [s.getsockname()[0]]
            s.close()
        except Exception:
            pass
    return [i for i in dict.fromkeys(ips) if not i.startswith("127.")]


def create_app(drone, video, restream, token):
    app = Flask(__name__)
    ctl = {"cid": None, "seen": 0.0}
    ctl_lock = threading.Lock()

    def watch():
        while drone.running:
            now = time.monotonic()
            with ctl_lock:
                if ctl["cid"] is not None and now - ctl["seen"] > CONTROLLER_TIMEOUT:
                    ctl["cid"] = None
                    drone.zero_sticks()
                    drone.no_client_since = now
            time.sleep(0.2)
    threading.Thread(target=watch, daemon=True, name="watch").start()

    def claim(cid, force=False):
        """คืน True ถ้า cid นี้เป็นเครื่องที่ควบคุมอยู่"""
        now = time.monotonic()
        with ctl_lock:
            if ctl["cid"] == cid:
                ctl["seen"] = now
                return True
            if force or ctl["cid"] is None:
                ctl["cid"], ctl["seen"] = cid, now
                drone.no_client_since = None
                return True
            return False

    def status(is_ctrl):
        d = drone.snapshot()
        d["video"] = video.info()
        d["stream"] = restream.status()
        d["role"] = "controller" if is_ctrl else "viewer"
        return d

    rate_buckets = {}

    @app.before_request
    def auth():
        p = request.path
        if p in ("/video", "/snapshot.jpg") or p.startswith("/api/"):
            ip = request.remote_addr or "127.0.0.1"
            now = time.time()
            # Rate-limit guard for unauthorized brute-force attempts (HTTP 429 + Retry-After: 60)
            fails = [ts for ts in rate_buckets.get(ip, []) if now - ts < 60.0]
            if len(fails) >= 30:
                resp = jsonify({
                    "success": False,
                    "error": {"code": "RATE_LIMIT_EXCEEDED", "message": "คำขอถี่เกินกำหนด กรุณารอสักครู่"},
                })
                resp.status_code = 429
                resp.headers["Retry-After"] = "60"
                return resp

            t = request.args.get("t", "")
            if not secrets.compare_digest(t.encode(), token.encode()):
                fails.append(now)
                rate_buckets[ip] = fails
                return Response("unauthorized", status=401)

    @app.after_request
    def headers(resp):
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["Referrer-Policy"] = "no-referrer"
        resp.headers["X-Content-Type-Options"] = "nosniff"
        return resp

    @app.route("/")
    def index():
        return send_file(os.path.join(WEB_DIR, "index.html"))

    @app.route("/video")
    def video_stream():
        def gen():
            last = -1
            while True:
                jpg, fid = video.get_jpeg()
                if jpg and fid != last:
                    last = fid
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                           + str(len(jpg)).encode() + b"\r\n\r\n" + jpg + b"\r\n")
                time.sleep(0.03)
        return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/snapshot.jpg")
    def snapshot():
        jpg, _ = video.get_jpeg()
        if not jpg:
            return Response("no frame", status=503)
        name = "shot_%s.jpg" % datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(os.path.join(OUTPUT_DIR, name), "wb") as f:
                f.write(jpg)
        except OSError:
            pass
        resp = Response(jpg, mimetype="image/jpeg")
        if request.args.get("dl"):
            resp.headers["Content-Disposition"] = 'attachment; filename="%s"' % name
        return resp

    @app.route("/api/control", methods=["POST"])
    def api_control():
        d = request.get_json(silent=True) or {}
        is_ctrl = claim(str(d.get("cid", "")))
        if is_ctrl:
            drone.set_sticks(d.get("r"), d.get("p"), d.get("th"), d.get("y"))
        return jsonify(status(is_ctrl))

    @app.route("/api/cmd", methods=["POST"])
    def api_cmd():
        d = request.get_json(silent=True) or {}
        name = str(d.get("name", ""))
        cid = str(d.get("cid", ""))
        if name == "estop":                       # หยุดฉุกเฉินสั่งได้จากทุกเครื่อง
            ok, msg = drone.command("estop")
        elif claim(cid):
            ok, msg = drone.command(name, d.get("v"))
        else:
            ok, msg = False, "เครื่องอื่นกำลังควบคุมอยู่"
        return jsonify({"ok": ok, "msg": msg})

    @app.route("/api/take", methods=["POST"])
    def api_take():
        d = request.get_json(silent=True) or {}
        claim(str(d.get("cid", "")), force=True)
        return jsonify({"ok": True, "msg": "ได้รับสิทธิ์ควบคุมแล้ว"})

    @app.route("/api/stream", methods=["POST"])
    def api_stream():
        d = request.get_json(silent=True) or {}
        if not claim(str(d.get("cid", ""))):
            return jsonify({"ok": False, "msg": "เครื่องอื่นกำลังควบคุมอยู่"})
        try:
            if d.get("action") == "start":
                restream.start(str(d.get("url", "")))
                return jsonify({"ok": True, "msg": "เริ่มสตรีมต่อแล้ว"})
            restream.stop()
            return jsonify({"ok": True, "msg": "หยุดสตรีมต่อแล้ว"})
        except (ValueError, RuntimeError) as e:
            return jsonify({"ok": False, "msg": str(e)})

    @app.route("/api/estop", methods=["POST"])
    def api_estop():
        ok, msg = drone.command("estop")
        return jsonify({"ok": ok, "msg": msg})

    return app


def find_free_port(host, start, tries=30):
    """คืนพอร์ตแรกที่ว่างตั้งแต่ start ขึ้นไป (ข้ามพอร์ตที่มีโปรแกรมอื่นใช้อยู่)"""
    for port in range(start, start + tries):
        busy = False
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.settimeout(0.3)
            busy = probe.connect_ex(("127.0.0.1", port)) == 0
        finally:
            probe.close()
        if not busy:
            b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                b.bind((host, port))
                return port
            except OSError:
                pass
            finally:
                b.close()
    return start


def main():
    ap = argparse.ArgumentParser(description="pyDroneWire web controller")
    ap.add_argument("--live", action="store_true", help="ส่งคำสั่งไปที่โดรนจริง (ค่าเริ่มต้น: DRY RUN)")
    ap.add_argument("--demo", action="store_true", help="ใช้วิดีโอจำลอง (ไม่ต้องมีโดรน)")
    ap.add_argument("--drone-ip", default="192.168.1.1")
    ap.add_argument("--ctrl-port", type=int, default=7099)
    ap.add_argument("--stream-url", default=None, help="ค่าเริ่มต้น rtsp://<drone-ip>:7070/webcam")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--no-browser", action="store_true", help="ไม่เปิดเบราว์เซอร์ให้อัตโนมัติ")
    ap.add_argument("--rtsp-tcp", action="store_true",
                    help="ดึงวิดีโอผ่าน TCP (ภาพหน่วงขึ้นเล็กน้อยแต่แพ็กเก็ตไม่หลุด ลองใช้ถ้าขึ้น Missing packets)")
    ap.add_argument("--verbose", action="store_true", help="แสดงข้อความจาก ffmpeg/OpenCV (ใช้แก้ปัญหาวิดีโอ)")
    ap.add_argument("--version", action="version", version="%(prog)s " + __version__)
    ap.add_argument("--token", default=None, help="รหัสเข้าใช้งาน (ค่าเริ่มต้น: สุ่มใหม่ทุกครั้ง)")
    ap.add_argument("--failsafe-land", type=float, default=0.0, metavar="SEC",
                    help="สั่งลงจอดเมื่อไม่มีเครื่องควบคุมเกิน SEC วินาที (ปิดไว้เป็นค่าเริ่มต้น)")
    a = ap.parse_args()

    url = a.stream_url or "rtsp://%s:7070/webcam" % a.drone_ip
    if a.rtsp_tcp:
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|max_delay;500000"
    video = VideoSource(url, demo=a.demo)
    drone = Drone(a.drone_ip, a.ctrl_port, a.live, a.failsafe_land, video)
    restream = Restreamer(video)
    token = a.token or secrets.token_urlsafe(6)
    app = create_app(drone, video, restream, token)
    port = find_free_port(a.host, a.port)

    video.start()
    drone.start()

    tty = sys.stdout.isatty()
    G, Y, R, D, B, X = (("\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[1m", "\033[0m")
                        if tty else ("",) * 6)
    local_url = "http://127.0.0.1:%d/?t=%s" % (port, token)
    print()
    print(" %spyDroneWire Web Controller%s %sv%s%s" % (B, X, D, __version__, X))
    if a.live:
        print(" โหมด    %sLIVE%s  ส่งคำสั่งไปที่โดรนจริง" % (R + B, X))
        print("         %sทดสอบครั้งแรกให้ถอดใบพัดออกก่อน%s" % (Y, X))
    else:
        print(" โหมด    %sDRY RUN%s  ไม่ส่งคำสั่งไปที่โดรน (เพิ่ม --live เพื่อส่งจริง)" % (Y + B, X))
    print(" วิดีโอ   %s%s" % ("วิดีโอจำลอง" if a.demo else url,
                            "  (TCP)" if a.rtsp_tcp and not a.demo else ""))
    if port != a.port:
        print(" พอร์ต    %d ไม่ว่าง ใช้ %d แทน" % (a.port, port))
    print(" เปิดบน Mac  %s%s%s" % (G, local_url, X))
    for ip in local_ips():
        print(" เปิดจากมือถือ  http://%s:%d/?t=%s" % (ip, port, token))
    if not a.no_browser:
        threading.Timer(1.5, lambda: webbrowser.open(local_url)).start()
    print(" %sกด Ctrl+C เพื่อปิด%s\n" % (D, X))

    logging.basicConfig(level=logging.INFO, format=" %(message)s")
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    try:
        app.run(host=a.host, port=port, threaded=True, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        pass
    finally:
        was_flying = drone.flying
        restream.stop()
        drone.stop()
        video.running = False
        print()
        if was_flying and a.live:
            print(" %sปิดโปรแกรมขณะโดรนยังบิน: หยุดส่งคำสั่งแล้ว โดรนจะทำตามระบบป้องกันของตัวเอง%s"
                  % (Y, X))
        print(" ปิดแล้ว ส่งคำสั่งไปทั้งหมด %d ครั้ง" % drone.tx)


if __name__ == "__main__":
    main()
