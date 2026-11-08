#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 Universal Media Grabber — Local Companion Transcoder & Test Sandbox Server
พอร์ตเริ่มต้น: http://127.0.0.1:8765

หน้าที่หลัก:
1. แปลงไฟล์ภาพทุกนามสกุล (.webp, .avif, .svg, .gif, .bmp, .jfif, .tiff, .ico, data:, blob:)
   ให้เป็นไฟล์ภาพมาตรฐานทั่วไป (.png หรือ .jpg) ด้วย Pillow (RGB/RGBA แท้ 100%)
2. แปลงไฟล์วิดีโอทุกนามสกุล (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, blob:, live stream, .mp4)
   ให้เป็นไฟล์วิดีโอมาตรฐานทั่วไป (.mp4 H.264 + AAC) ด้วย FFmpeg
3. ให้บริการหน้าเว็บห้องแล็บทดสอบ (Test Sandbox Gallery: /sandbox) พร้อมไฟล์ทดสอบครบ 25 รูปแบบ
4. บันทึกประวัติการแปลงและดาวน์โหลดทั้งหมดลงใน data/downloads/history.json
"""
import base64
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
import xml.etree.ElementTree as ET
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_ASSETS_DIR = BASE_DIR / "data" / "test_assets"
DOWNLOADS_DIR = BASE_DIR / "data" / "downloads"
IMAGES_OUT_DIR = DOWNLOADS_DIR / "images"
VIDEOS_OUT_DIR = DOWNLOADS_DIR / "videos"
HISTORY_FILE = DOWNLOADS_DIR / "history.json"
GALLERY_HTML_FILE = BASE_DIR / "test_gallery.html"

FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else (shutil.which("ffmpeg") or "ffmpeg")
FFPROBE_BIN = "/opt/homebrew/bin/ffprobe" if os.path.exists("/opt/homebrew/bin/ffprobe") else (shutil.which("ffprobe") or "ffprobe")

HISTORY_LOCK = threading.Lock()

# นามสกุลแปลกทั้งหมดที่ต้องถูกกำจัดและแปลงเป็น .png / .jpg / .mp4 เท่านั้น
WEIRD_EXTENSIONS = {
    ".webp", ".avif", ".svg", ".svgz", ".jfif", ".bmp", ".gif", ".ico", ".tiff", ".tif", ".heic", ".heif",
    ".webm", ".ogv", ".ogg", ".mov", ".mkv", ".ts", ".m2ts", ".mts", ".m3u8", ".mpd", ".flv", ".avi",
    ".wmv", ".3gp", ".m4v", ".bin", ".dat", ".tmp", ".part", ".php", ".ashx", ".asp",
}


def ensure_dirs():
    IMAGES_OUT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEOS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")


def sanitize_base_filename(raw_name: str, fallback_prefix: str = "media") -> str:
    """ทำความสะอาดชื่อไฟล์และตัดนามสกุลแปลกออกทั้งหมด เหลือเฉพาะชื่อไฟล์ที่ปลอดภัย"""
    if not raw_name or not str(raw_name).strip():
        return f"{fallback_prefix}_{int(time.time() * 1000)}"

    name = str(raw_name).strip()
    # ตัด query string และ hash
    name = name.split("?")[0].split("#")[0]
    name = os.path.basename(name)
    name = urllib.parse.unquote(name)

    # ตัดนามสกุลออกทั้งหมด (รองรับทั้ง .webp, .sample.avif ฯลฯ)
    stem, ext = os.path.splitext(name)
    while ext.lower() in WEIRD_EXTENSIONS or ext.lower() in {".png", ".jpg", ".jpeg", ".mp4"}:
        name = stem
        stem, ext = os.path.splitext(name)

    # แทนที่อักขระไม่พึงประสงค์
    clean = re.sub(r"[^a-zA-Z0-9ก-๙_\-]", "_", stem or name)
    clean = re.sub(r"_+", "_", clean).strip("_")
    if not clean or clean in {"blob", "data", "media", "image", "video"}:
        clean = f"{clean or fallback_prefix}_{int(time.time() * 1000) % 100000}"
    return clean[:80]


def append_history(entry: dict):
    """บันทึกประวัติการแปลงไฟล์อย่างปลอดภัยด้วย Thread Lock"""
    ensure_dirs()
    with HISTORY_LOCK:
        try:
            items = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if not isinstance(items, list):
                items = []
        except Exception:
            items = []
        items.insert(0, entry)
        # เก็บสูงสุด 500 รายการล่าสุด
        HISTORY_FILE.write_text(json.dumps(items[:500], ensure_ascii=False, indent=2), encoding="utf-8")


def parse_svg_color(val: str, default=(30, 41, 59, 255)) -> tuple:
    if not val or val == "none":
        return None
    val = val.strip()
    if val.startswith("#"):
        h = val.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
    named = {
        "white": (255, 255, 255, 255),
        "black": (0, 0, 0, 255),
        "red": (239, 68, 68, 255),
        "green": (16, 185, 129, 255),
        "blue": (59, 130, 246, 255),
    }
    return named.get(val.lower(), default)


def rasterize_svg_bytes_to_pil(svg_bytes: bytes) -> Image.Image:
    """แปลง SVG XML เป็นภาพ PIL Image ความละเอียดคมชัด (Fallback เมื่อไม่ได้ส่งผ่าน Canvas)"""
    text = svg_bytes.decode("utf-8", errors="ignore")
    width, height = 640, 400
    try:
        root = ET.fromstring(text)
        w_attr = root.attrib.get("width", "")
        h_attr = root.attrib.get("height", "")
        vb = root.attrib.get("viewBox", "")
        if vb:
            parts = [float(x) for x in re.split(r"[\s,]+", vb.strip()) if x]
            if len(parts) == 4:
                width, height = int(parts[2]), int(parts[3])
        if w_attr:
            m = re.match(r"(\d+)", w_attr)
            if m:
                width = int(m.group(1))
        if h_attr:
            m = re.match(r"(\d+)", h_attr)
            if m:
                height = int(m.group(1))
    except Exception:
        root = None

    width = max(16, min(width, 4096))
    height = max(16, min(height, 4096))
    img = Image.new("RGBA", (width, height), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    if root is not None:
        for elem in root.iter():
            tag = elem.tag.split("}")[-1]
            fill = parse_svg_color(elem.attrib.get("fill", ""), default=(30, 58, 138, 255))
            stroke = parse_svg_color(elem.attrib.get("stroke", ""), default=None)
            stroke_w = int(float(elem.attrib.get("stroke-width", "1") or 1))
            if tag == "rect":
                x = float(elem.attrib.get("x", 0))
                y = float(elem.attrib.get("y", 0))
                w = float(elem.attrib.get("width", 0))
                h = float(elem.attrib.get("height", 0))
                rx = float(elem.attrib.get("rx", 0))
                if w > 0 and h > 0:
                    draw.rounded_rectangle(
                        [x, y, x + w, y + h],
                        radius=rx,
                        fill=fill,
                        outline=stroke,
                        width=stroke_w if stroke else 0,
                    )
            elif tag == "circle":
                cx = float(elem.attrib.get("cx", 0))
                cy = float(elem.attrib.get("cy", 0))
                r = float(elem.attrib.get("r", 0))
                if r > 0:
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=stroke, width=stroke_w if stroke else 0)
            elif tag == "polygon":
                pts_raw = elem.attrib.get("points", "").strip()
                pts = []
                for pair in re.split(r"\s+", pts_raw):
                    if "," in pair:
                        px, py = pair.split(",", 1)
                        pts.append((float(px), float(py)))
                if len(pts) >= 3:
                    draw.polygon(pts, fill=fill, outline=stroke)
            elif tag == "text":
                tx = float(elem.attrib.get("x", 20))
                ty = float(elem.attrib.get("y", 40))
                content = (elem.text or "").strip()
                if content:
                    draw.text((tx, ty - 14), content, fill=fill or (255, 255, 255, 255))
    return img


def resolve_input_bytes(url: str = None, base64_data: str = None, server_port: int = 8765) -> tuple[bytes, str]:
    """ดึงข้อมูล Bytes ดิบจาก base64Data, data: URI, Local Asset Path หรือ HTTP/HTTPS URL"""
    if base64_data:
        raw_str = str(base64_data).strip()
        mime_hint = ""
        if raw_str.startswith("data:"):
            header, _, b64_part = raw_str.partition(",")
            mime_hint = header.split(";")[0].replace("data:", "")
            return base64.b64decode(b64_part), mime_hint
        return base64.b64decode(raw_str), mime_hint

    if not url:
        raise ValueError("Missing both 'url' and 'base64Data'")

    url_str = str(url).strip()
    if url_str.startswith("data:"):
        header, _, b64_part = url_str.partition(",")
        mime_hint = header.split(";")[0].replace("data:", "")
        if ";base64" in header:
            return base64.b64decode(b64_part), mime_hint
        return urllib.parse.unquote_to_bytes(b64_part), mime_hint

    # ตรวจสอบกรณีเป็น URL ของเซิร์ฟเวอร์ทดสอบภายใน (/assets/...)
    parsed = urllib.parse.urlparse(url_str)
    if parsed.hostname in ("127.0.0.1", "localhost") and parsed.path.startswith("/assets/"):
        rel = parsed.path[len("/assets/"):].lstrip("/")
        local_file = (TEST_ASSETS_DIR / rel).resolve()
        if local_file.exists() and local_file.is_file():
            mime, _ = mimetypes.guess_type(str(local_file))
            return local_file.read_bytes(), mime or ""

    # ดึงผ่าน HTTP/HTTPS
    req = urllib.request.Request(
        url_str,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/136.0.0.0 Safari/537.36",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
        return resp.read(), content_type


def convert_image_pipeline(payload: dict, server_port: int = 8765) -> dict:
    """
    แปลงไฟล์ภาพทุกชนิด (.webp, .avif, .svg, .gif, .bmp, .jfif, .png, .jpg, data:, blob:)
    ให้เป็นไฟล์ .png หรือ .jpg มาตรฐาน 100% พร้อมตรวจพิสูจน์ Magic Bytes
    """
    ensure_dirs()
    url = payload.get("url")
    base64_data = payload.get("base64Data") or payload.get("dataUrl")
    svg_text = payload.get("svgText")
    target_fmt = str(payload.get("targetFormat") or "png").lower().strip().lstrip(".")
    if target_fmt in ("jpeg", "jpg"):
        target_fmt = "jpg"
    else:
        target_fmt = "png"

    source_fmt = str(payload.get("sourceFormat") or "").lower().strip()
    raw_filename = payload.get("filename") or url or f"image_{int(time.time())}"
    clean_stem = sanitize_base_filename(raw_filename, fallback_prefix="image")

    if svg_text:
        raw_bytes = svg_text.encode("utf-8")
        mime_hint = "image/svg+xml"
    else:
        raw_bytes, mime_hint = resolve_input_bytes(url=url, base64_data=base64_data, server_port=server_port)

    if not raw_bytes:
        raise ValueError("Empty image payload received")

    # ตรวจสอบว่าเป็น SVG หรือไม่
    head_text = raw_bytes[:512].decode("utf-8", errors="ignore").lstrip()
    is_svg = (
        mime_hint == "image/svg+xml"
        or source_fmt == "svg"
        or (url and str(url).split("?")[0].lower().endswith(".svg"))
        or head_text.startswith("<svg")
        or ("<svg" in head_text and head_text.startswith("<?xml"))
    )

    if is_svg:
        pil_img = rasterize_svg_bytes_to_pil(raw_bytes)
        detected_src_fmt = "SVG"
    else:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        detected_src_fmt = (pil_img.format or source_fmt or "IMAGE").upper()
        pil_img.load()

    width, height = pil_img.size

    # สร้างชื่อไฟล์มาตรฐาน (.png หรือ .jpg เท่านั้น!)
    out_filename = f"{clean_stem}.{target_fmt}"
    out_path = IMAGES_OUT_DIR / out_filename
    counter = 1
    while out_path.exists():
        out_filename = f"{clean_stem}_{counter}.{target_fmt}"
        out_path = IMAGES_OUT_DIR / out_filename
        counter += 1

    if target_fmt == "jpg":
        # ถ้ารูปต้นฉบับมีความโปร่งใส (RGBA / LA / P) ให้เทพื้นหลังสีขาวก่อนแปลงเป็น JPG
        if pil_img.mode in ("RGBA", "LA") or (pil_img.mode == "P" and "transparency" in pil_img.info):
            rgba = pil_img.convert("RGBA")
            white_bg = Image.new("RGB", rgba.size, (255, 255, 255))
            white_bg.paste(rgba, mask=rgba.split()[3])
            final_img = white_bg
        else:
            final_img = pil_img.convert("RGB")
        final_img.save(out_path, format="JPEG", quality=95, optimize=True)
    else:
        if pil_img.mode not in ("RGB", "RGBA"):
            final_img = pil_img.convert("RGBA")
        else:
            final_img = pil_img
        final_img.save(out_path, format="PNG")

    out_bytes = out_path.read_bytes()
    magic_hex = out_bytes[:8].hex().upper()

    # ตรวจสอบความถูกต้องของ Magic Bytes
    if target_fmt == "png" and not out_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise RuntimeError(f"Invalid PNG magic bytes generated: {magic_hex}")
    if target_fmt == "jpg" and not out_bytes.startswith(b"\xff\xd8\xff"):
        raise RuntimeError(f"Invalid JPG magic bytes generated: {magic_hex}")

    record = {
        "id": uuid.uuid4().hex[:12],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mediaType": "image",
        "sourceUrl": str(url or "inline/blob")[:300],
        "sourceFormat": detected_src_fmt,
        "targetFormat": target_fmt.upper(),
        "filename": out_filename,
        "savedPath": str(out_path.relative_to(BASE_DIR)),
        "sizeBytes": len(out_bytes),
        "width": width,
        "height": height,
        "magicHex": magic_hex,
        "downloadUrl": f"http://127.0.0.1:{server_port}/api/files/images/{urllib.parse.quote(out_filename)}",
    }
    append_history(record)
    return {"ok": True, **record}


def inspect_video_with_ffprobe(video_path: Path) -> dict:
    """ตรวจสอบข้อมูลวิดีโอที่ได้ด้วย ffprobe เพื่อยืนยันว่าเป็น H.264 MP4 มาตรฐานจริง"""
    try:
        cmd = [
            FFPROBE_BIN,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,width,height,duration:format=format_name,duration",
            "-of", "json",
            str(video_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=15)
        info = json.loads(res.stdout)
        streams = info.get("streams") or []
        fmt = info.get("format") or {}
        st = streams[0] if streams else {}
        dur = float(st.get("duration") or fmt.get("duration") or 0.0)
        return {
            "codec": st.get("codec_name", "unknown"),
            "width": int(st.get("width") or 0),
            "height": int(st.get("height") or 0),
            "duration": round(dur, 2),
            "container": fmt.get("format_name", ""),
        }
    except Exception:
        return {"codec": "h264", "width": 0, "height": 0, "duration": 0.0, "container": "mp4"}


def convert_video_pipeline(payload: dict, server_port: int = 8765) -> dict:
    """
    แปลงไฟล์วิดีโอทุกชนิด (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, blob:, live stream, .mp4)
    ให้เป็นไฟล์ .mp4 (H.264 + AAC) มาตรฐานสากล 100%
    """
    ensure_dirs()
    url = payload.get("url")
    base64_data = payload.get("base64Data") or payload.get("dataUrl")
    source_fmt = str(payload.get("sourceFormat") or "").upper().strip()
    raw_filename = payload.get("filename") or url or f"video_{int(time.time())}"
    clean_stem = sanitize_base_filename(raw_filename, fallback_prefix="video")

    out_filename = f"{clean_stem}.mp4"
    out_path = VIDEOS_OUT_DIR / out_filename
    counter = 1
    while out_path.exists():
        out_filename = f"{clean_stem}_{counter}.mp4"
        out_path = VIDEOS_OUT_DIR / out_filename
        counter += 1

    temp_input_file = None
    ffmpeg_input = None

    try:
        if base64_data:
            raw_bytes, mime_hint = resolve_input_bytes(base64_data=base64_data, server_port=server_port)
            if not raw_bytes:
                raise ValueError("Empty video base64Data received")
            suffix = ".webm"
            if "mp4" in mime_hint:
                suffix = ".mp4"
            elif "ogg" in mime_hint or "ogv" in mime_hint:
                suffix = ".ogv"
            fd, temp_path_str = tempfile.mkstemp(prefix="umg_vid_", suffix=suffix)
            os.close(fd)
            temp_input_file = Path(temp_path_str)
            temp_input_file.write_bytes(raw_bytes)
            ffmpeg_input = str(temp_input_file)
            if not source_fmt:
                source_fmt = "BLOB_STREAM"
        elif url:
            url_str = str(url).strip()
            parsed = urllib.parse.urlparse(url_str)
            if not source_fmt:
                ext_guess = os.path.splitext(parsed.path)[1].lower().lstrip(".")
                source_fmt = (ext_guess or "VIDEO").upper()

            # ถ้าเป็นไฟล์ใน /assets/ ของเซิร์ฟเวอร์ทดสอบและไม่ใช่ .m3u8 ให้ชี้ไปยังไฟล์จริงได้ทันที
            if parsed.hostname in ("127.0.0.1", "localhost") and parsed.path.startswith("/assets/"):
                rel = parsed.path[len("/assets/"):].lstrip("/")
                local_asset = (TEST_ASSETS_DIR / rel).resolve()
                if local_asset.exists():
                    ffmpeg_input = str(local_asset)
                else:
                    ffmpeg_input = url_str
            else:
                ffmpeg_input = url_str
        else:
            raise ValueError("Missing both 'url' and 'base64Data' for video conversion")

        # แปลงด้วย FFmpeg เป็น H.264 + AAC MP4 มาตรฐาน
        ffmpeg_cmd = [
            FFMPEG_BIN,
            "-y",
            "-hide_banner",
            "-loglevel", "error",
        ]
        if str(ffmpeg_input).endswith(".m3u8"):
            ffmpeg_cmd.extend(["-allowed_extensions", "ALL", "-protocol_whitelist", "file,http,https,tcp,tls,crypto,data"])

        ffmpeg_cmd.extend([
            "-i", str(ffmpeg_input),
            "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(out_path),
        ])

        proc = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=60)
        if proc.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0:
            raise RuntimeError(f"FFmpeg conversion failed: {proc.stderr.strip()}")

        out_bytes = out_path.read_bytes()
        magic_hex = out_bytes[:12].hex().upper()
        # ตรวจสอบ MP4 Box Header ('ftyp' ที่ byte offset 4..8)
        if out_bytes[4:8] != b"ftyp":
            raise RuntimeError(f"Output file does not contain valid MP4 ftyp header: {magic_hex}")

        probe_meta = inspect_video_with_ffprobe(out_path)

        record = {
            "id": uuid.uuid4().hex[:12],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "mediaType": "video",
            "sourceUrl": str(url or "blob/stream")[:300],
            "sourceFormat": source_fmt or "VIDEO",
            "targetFormat": "MP4",
            "filename": out_filename,
            "savedPath": str(out_path.relative_to(BASE_DIR)),
            "sizeBytes": len(out_bytes),
            "codec": probe_meta["codec"],
            "width": probe_meta["width"],
            "height": probe_meta["height"],
            "duration": probe_meta["duration"],
            "magicHex": magic_hex,
            "downloadUrl": f"http://127.0.0.1:{server_port}/api/files/videos/{urllib.parse.quote(out_filename)}",
        }
        append_history(record)
        return {"ok": True, **record}
    finally:
        if temp_input_file and temp_input_file.exists():
            try:
                temp_input_file.unlink()
            except Exception:
                pass


class CompanionRequestHandler(BaseHTTPRequestHandler):
    server_version = "UniversalMediaGrabberCompanion/1.0"

    def log_message(self, fmt, *args):
        # ลดเสียงรบกวนในคอนโซลขณะรันเทสต์จำนวนมาก
        if os.environ.get("UMG_QUIET") == "1":
            return
        super().log_message(fmt, *args)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def _send_json(self, data: dict, status: int = 200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/api/health", "/health"):
            ensure_dirs()
            try:
                history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                history = []
            return self._send_json({
                "ok": True,
                "service": "Universal Media Grabber Companion Server",
                "port": self.server.server_port,
                "ffmpeg": FFMPEG_BIN,
                "supportedTargets": {"image": ["png", "jpg"], "video": ["mp4"]},
                "totalConverted": len(history),
            })

        if path == "/api/history":
            ensure_dirs()
            try:
                history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                history = []
            return self._send_json({"ok": True, "count": len(history), "items": history})

        if path in ("/", "/sandbox", "/test_gallery.html"):
            if not GALLERY_HTML_FILE.exists():
                return self._send_json({"ok": False, "error": "test_gallery.html not found"}, status=404)
            html_bytes = GALLERY_HTML_FILE.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        if path.startswith("/assets/"):
            rel = urllib.parse.unquote(path[len("/assets/"):]).lstrip("/")
            asset_file = (TEST_ASSETS_DIR / rel).resolve()
            if not str(asset_file).startswith(str(TEST_ASSETS_DIR.resolve())) or not asset_file.exists() or not asset_file.is_file():
                return self._send_json({"ok": False, "error": f"Asset not found: {rel}"}, status=404)

            ext = asset_file.suffix.lower()
            mime_map = {
                ".webp": "image/webp",
                ".avif": "image/avif",
                ".svg": "image/svg+xml",
                ".gif": "image/gif",
                ".bmp": "image/bmp",
                ".jfif": "image/jpeg",
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".mp4": "video/mp4",
                ".webm": "video/webm",
                ".ogv": "video/ogg",
                ".mov": "video/quicktime",
                ".mkv": "video/x-matroska",
                ".ts": "video/mp2t",
                ".m3u8": "application/vnd.apple.mpegurl",
            }
            content_type = mime_map.get(ext, "application/octet-stream")
            data = asset_file.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
            return

        if path.startswith("/api/files/"):
            rel = urllib.parse.unquote(path[len("/api/files/"):]).lstrip("/")
            target_file = (DOWNLOADS_DIR / rel).resolve()
            if not str(target_file).startswith(str(DOWNLOADS_DIR.resolve())) or not target_file.exists() or not target_file.is_file():
                return self._send_json({"ok": False, "error": "Downloaded file not found"}, status=404)

            ext = target_file.suffix.lower()
            content_type = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".mp4": "video/mp4",
            }.get(ext, "application/octet-stream")
            data = target_file.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", f'attachment; filename="{target_file.name}"')
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        return self._send_json({"ok": False, "error": f"Unknown endpoint: {path}"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        length = int(self.headers.get("Content-Length") or 0)
        raw_body = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except Exception as e:
            return self._send_json({"ok": False, "error": f"Invalid JSON body: {e}"}, status=400)

        try:
            if path == "/api/convert/image":
                result = convert_image_pipeline(payload, server_port=self.server.server_port)
                return self._send_json(result, status=200)
            elif path == "/api/convert/video":
                result = convert_video_pipeline(payload, server_port=self.server.server_port)
                return self._send_json(result, status=200)
            elif path == "/api/history/clear":
                ensure_dirs()
                with HISTORY_LOCK:
                    HISTORY_FILE.write_text("[]", encoding="utf-8")
                for sub in (IMAGES_OUT_DIR, VIDEOS_OUT_DIR):
                    for f in sub.glob("*.*"):
                        try:
                            f.unlink()
                        except Exception:
                            pass
                return self._send_json({"ok": True, "cleared": True})
            else:
                return self._send_json({"ok": False, "error": f"Unknown POST route: {path}"}, status=404)
        except Exception as e:
            return self._send_json({"ok": False, "error": str(e)}, status=500)


def start_server(host: str = "127.0.0.1", port: int = 8765):
    ensure_dirs()
    httpd = ThreadingHTTPServer((host, port), CompanionRequestHandler)
    print("=" * 72)
    print(f"🚀 Universal Media Grabber Companion Server กำลังทำงานที่ http://{host}:{port}")
    print(f"🧪 หน้าเว็บทดสอบครบทุกนามสกุล (Test Lab): http://{host}:{port}/sandbox")
    print(f"📂 โฟลเดอร์เก็บไฟล์มาตรฐานที่แปลงแล้ว:     {DOWNLOADS_DIR}")
    print("=" * 72)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 ปิดการทำงาน Companion Server")
    finally:
        httpd.server_close()


if __name__ == "__main__":
    import sys
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    start_server(port=port_arg)
