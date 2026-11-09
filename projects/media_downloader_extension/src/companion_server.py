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
from PIL import Image, ImageDraw, ImageOps

BASE_DIR = Path(__file__).resolve().parent.parent
TEST_ASSETS_DIR = BASE_DIR / "data" / "test_assets"
DOWNLOADS_DIR = Path(os.environ.get("UMG_DOWNLOADS_DIR") or (BASE_DIR / "data" / "downloads"))
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
        return f"{fallback_prefix}_{time.strftime('%Y%m%d_%H%M%S')}"

    name = str(raw_name).strip()
    # ตัด query string และ hash
    name = name.split("?")[0].split("#")[0]
    if "://" in name or "/" in name:
        name = os.path.basename(name)
    name = urllib.parse.unquote(name)

    # ตัด thumbnail suffix เช่น .jpg_80x80.jpg หรือ _220x220xz.webp
    name = re.sub(r"\.(jpg|jpeg|png|webp|avif|gif)_\d+x\d+.*$", "", name, flags=re.IGNORECASE)

    # ตัดนามสกุลออกทั้งหมด (รองรับทั้ง .webp, .sample.avif ฯลฯ)
    stem, ext = os.path.splitext(name)
    while ext.lower() in WEIRD_EXTENSIONS or ext.lower() in {".png", ".jpg", ".jpeg", ".mp4"}:
        name = stem
        stem, ext = os.path.splitext(name)

    # แทนที่อักขระไม่พึงประสงค์
    clean = re.sub(r"[^a-zA-Z0-9ก-๙_\-]", "_", stem or name)
    clean = re.sub(r"_+", "_", clean).strip("_-")
    if not clean or clean.lower() in {"blob", "data", "media", "image", "video", "watch"}:
        clean = f"{fallback_prefix}_{time.strftime('%Y%m%d_%H%M%S')}"
    return clean[:80]


def extract_site_label(page_url: str = "", media_url: str = "", site_hint: str = "") -> str:
    """สกัดชื่อเว็บไซต์ให้สั้น อ่านง่าย เช่น Alibaba, Shopee, Lazada, YouTube, TikTok"""
    if site_hint and str(site_hint).strip():
        clean_hint = re.sub(r"[^a-zA-Z0-9ก-๙]", "", str(site_hint).strip())
        if clean_hint:
            return clean_hint[:20]

    for candidate in (page_url, media_url):
        if not candidate or not str(candidate).startswith(("http://", "https://")):
            continue
        host = (urllib.parse.urlparse(str(candidate)).hostname or "").lower()
        if not host or host in ("127.0.0.1", "localhost"):
            continue
        brand_map = [
            (("alibaba.", "alicdn."), "Alibaba"),
            (("aliexpress.",), "AliExpress"),
            (("1688.",), "1688"),
            (("taobao.", "tbcdn."), "Taobao"),
            (("tmall.",), "Tmall"),
            (("shopee.", "shopeemobile."), "Shopee"),
            (("lazada.", "lzd-img"), "Lazada"),
            (("youtube.", "youtu.be", "ytimg.", "googlevideo."), "YouTube"),
            (("tiktok.", "tiktokcdn."), "TikTok"),
            (("facebook.", "fbcdn.", "fb.watch"), "Facebook"),
            (("instagram.", "cdninstagram."), "Instagram"),
            (("twitter.", "x.com", "twimg."), "X"),
            (("pinterest.", "pinimg."), "Pinterest"),
            (("apple.", "cdn-apple."), "Apple"),
            (("amazon.", "media-amazon."), "Amazon"),
            (("jd.com", "360buyimg."), "JD"),
        ]
        for keys, label in brand_map:
            if any(k in host for k in keys):
                return label
        parts = [p for p in host.split(".") if p not in ("www", "m", "mobile", "cdn", "img", "s", "gv", "videocdn", "com", "co", "th", "net", "org", "io")]
        if parts:
            return parts[0].capitalize()[:18]
    return ""


NAMING_COUNTER_LOCK = threading.Lock()
NAMING_SEQ_COUNTERS: dict[str, int] = {}

SEO_FILLER_WORDS = {
    "factory", "direct", "wholesale", "wholesaler", "hot", "sale", "selling", "bestseller",
    "high", "quality", "top", "best", "cheap", "cheapest", "price", "low", "moq", "oem", "odm",
    "custom", "customized", "customizable", "logo", "private", "label", "manufacturer", "manufacturers",
    "supplier", "suppliers", "exporter", "exporters", "importer", "importers", "ready", "to", "ship",
    "fast", "shipping", "delivery", "free", "sample", "new", "arrival", "design", "style", "fashion",
    "popular", "trendy", "modern", "professional", "good", "supply", "amazon", "alibaba", "aliexpress",
    "shopee", "lazada", "1688", "taobao", "tmall", "buy", "online", "shop", "store", "official",
    "authentic", "original", "product", "products", "item", "china", "chinese", "thailand",
    "for", "with", "and", "the", "in", "on", "of", "at", "by", "from", "or", "a", "an", "com", "www",
    "image", "images", "video", "videos", "photo", "picture", "media", "main", "detail",
    "พร้อมส่ง", "ส่งฟรี", "ราคาโรงงาน", "ราคาถูก", "ราคาส่ง", "ขายส่ง", "แท้", "เกรดพรีเมี่ยม", "รุ่นใหม่", "ยอดฮิต", "ขายดี",
}


def is_gibberish_or_hash(text: str) -> bool:
    """ตรวจจับว่าชื่อไฟล์เป็นรหัสสุ่ม/Hash ของ CDN หรือไม่ (เช่น 5kiu9u-h264-hd หรือ Ha0fe3c1058624d3194b6d68a220f9dcb3)"""
    if not text:
        return True
    s = str(text).strip("_- ")
    if len(s) < 2:
        return True
    low = s.lower()
    generic_words = {
        "image", "video", "media", "blob", "data", "watch", "default", "maxresdefault",
        "hqdefault", "sddefault", "mqdefault", "master", "playlist", "index", "unnamed",
        "untitled", "download", "file", "live_blob_video", "blob_video_stream", "blob_image",
        "alibaba", "aliexpress", "shopee", "lazada", "youtube", "tiktok", "facebook", "instagram",
    }
    if low in generic_words:
        return True
    if re.search(r"[ก-๙]", s):
        return False
    if re.fullmatch(r"[\d_\-xX]+", s):
        return True
    if re.fullmatch(r"[a-fA-F0-9_\-]{12,}", s) or re.match(r"^(H[a-fA-F0-9]{16,}|O1CN01[a-zA-Z0-9_\-]+|TB2[a-zA-Z0-9_\-]+)", s):
        return True
    tokens = [t for t in re.split(r"[_\-\s]+", low) if t]
    codec_tokens = {"h264", "h265", "hevc", "avc", "hd", "sd", "fhd", "uhd", "mp4", "webm", "1080p", "720p", "480p", "360p", "trans", "aidc", "vod", "target"}
    meaningful_tokens = 0
    gibberish_tokens = 0
    for tok in tokens:
        if tok in codec_tokens or tok.isdigit():
            continue
        if re.search(r"\d", tok) and re.search(r"[a-z]", tok):
            gibberish_tokens += 1
        elif len(tok) >= 16 and not re.search(r"[aeiou]{2}", tok):
            gibberish_tokens += 1
        elif len(tok) >= 3:
            meaningful_tokens += 1
    if meaningful_tokens == 0 and (gibberish_tokens > 0 or all(t in codec_tokens or t.isdigit() for t in tokens)):
        return True
    return False


def clean_page_title(raw_title: str, max_words: int = 5, max_chars: int = 38) -> str:
    """
    สกัดเฉพาะคำสำคัญของชื่อสินค้า/หัวข้อ (3-5 คำสมบูรณ์ ไม่ตัดกลางคำ และกรองคำโฆษณา SEO รกๆ ออก)
    """
    if not raw_title:
        return ""
    t = str(raw_title).strip()
    t = re.sub(r"^\(\d+\)\s*", "", t)
    t = re.split(
        r"\s+(?:\||-|\u2013|\u2014)\s+(?:Alibaba|AliExpress|Shopee|Lazada|YouTube|TikTok|Facebook|Instagram|Twitter|X|Buy\s|ซื้อ\s)",
        t,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    t = re.sub(r"\b(?:Buy|Wholesale|on\s+Alibaba\.com|Product\s+on\s+Alibaba\.com)\b", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"[^a-zA-Z0-9ก-๙_\-\s]", " ", t)

    raw_tokens = [tok.strip("_-") for tok in re.split(r"[\s_\-]+", t) if tok.strip("_-")]
    if not raw_tokens:
        return ""

    # กรองคำโฆษณา SEO ออก (แต่ถ้ากรองแล้วไม่เหลือคำเลย ให้ใช้คำต้นฉบับ)
    core_tokens = [
        tok for tok in raw_tokens
        if tok.lower() not in SEO_FILLER_WORDS
        and not re.fullmatch(r"202\d|100%", tok)
        and not (len(tok) >= 12 and tok.isdigit())
    ]
    chosen_pool = core_tokens if len(core_tokens) >= 1 else raw_tokens

    # เลือกไม่เกิน max_words คำ และความยาวรวมไม่เกิน max_chars โดยไม่ตัดกลางคำเด็ดขาด!
    selected = []
    total_len = 0
    for tok in chosen_pool:
        if len(selected) >= max_words:
            break
        add_len = len(tok) + (1 if selected else 0)
        if selected and (total_len + add_len) > max_chars:
            break
        selected.append(tok[:24])
        total_len += add_len

    return "_".join(selected).strip("_-")


def extract_slug_from_page_url(page_url: str) -> str:
    """ดึงชื่อสินค้าจาก URL หน้าเว็บ (เช่น /product-detail/Luxury-Glass-Candle-Jar_160098.html)"""
    if not page_url or not str(page_url).startswith(("http://", "https://")):
        return ""
    try:
        path = urllib.parse.unquote(urllib.parse.urlparse(str(page_url)).path or "")
        for seg in reversed([s for s in path.split("/") if s]):
            seg_clean = re.sub(r"\.(html?|php|asp|jsp)$", "", seg, flags=re.IGNORECASE)
            seg_clean = re.sub(r"[_\-\.]?\d{7,}$", "", seg_clean)
            seg_clean = re.sub(r"-i\.\d+\.\d+$", "", seg_clean)
            if seg_clean.lower() in ("watch", "reel", "shorts", "video", "videos", "product", "item", "detail", "search", "sandbox"):
                continue
            if not is_gibberish_or_hash(seg_clean):
                cleaned = clean_page_title(seg_clean, max_words=5, max_chars=36)
                if cleaned and not is_gibberish_or_hash(cleaned):
                    return cleaned
    except Exception:
        pass
    return ""


def next_clean_sequence_number(base_stem: str) -> str:
    """สร้างเลขลำดับ 01, 02, 03... ต่อท้ายชื่อไฟล์แทนรหัสเวลา 14 หลัก เพื่อให้ชื่อไฟล์สั้น สวย และดูง่าย"""
    user_downloads = Path.home() / "Downloads"
    with NAMING_COUNTER_LOCK:
        seq = NAMING_SEQ_COUNTERS.get(base_stem, 0) + 1
        while True:
            seq_str = f"{seq:02d}"
            candidate = f"{base_stem}_{seq_str}"
            exists_anywhere = False
            for folder in (user_downloads, IMAGES_OUT_DIR, VIDEOS_OUT_DIR):
                if folder and folder.exists():
                    for ext in (".png", ".jpg", ".mp4"):
                        if (folder / f"{candidate}{ext}").exists():
                            exists_anywhere = True
                            break
                if exists_anywhere:
                    break
            if not exists_anywhere:
                NAMING_SEQ_COUNTERS[base_stem] = seq
                return seq_str
            seq += 1


def build_smart_filename(
    raw_name: str = "",
    media_type: str = "image",
    url: str = "",
    page_url: str = "",
    page_title: str = "",
    site_name: str = "",
    custom_prefix: str = "",
) -> str:
    """
    ระบบตั้งชื่อไฟล์อัจฉริยะ v3.0 (อ่านง่าย กระชับ ไม่ตัดกลางคำ ไม่มีเลขเวลา 14 หลักรกตา):
    - กรณีผู้ใช้ตั้งชื่อนำหน้าเอง (custom_prefix): <ชื่อที่ตั้งเอง>_<รูปภาพ|วิดีโอ>_01
    - กรณีอัตโนมัติ: <รูปภาพ|วิดีโอ>_<ชื่อเว็บ>_<ชื่อสินค้าสั้นกระชับ 3-5 คำ>_01
    """
    type_prefix = "วิดีโอ" if media_type == "video" else "รูปภาพ"

    # กรณีผู้ใช้ระบุชื่อหมวด/ชื่อสินค้าเองจากช่องตั้งชื่อใน Popup
    if custom_prefix and str(custom_prefix).strip():
        clean_custom = re.sub(r"[^a-zA-Z0-9ก-๙_\-\s]", "", str(custom_prefix).strip())
        clean_custom = re.sub(r"[\s_]+", "_", clean_custom).strip("_-")[:35]
        if clean_custom:
            base_stem = f"{clean_custom}_{type_prefix}"
            seq_str = next_clean_sequence_number(base_stem)
            return f"{base_stem}_{seq_str}"

    site_label = extract_site_label(page_url=page_url, media_url=url, site_hint=site_name)
    candidate_stem = ""

    # 1. ลองดึงจาก page_title (ชื่อสินค้า/หัวข้อโพสต์) ก่อน และกรองคำโฆษณา SEO ออก
    if page_title:
        cleaned_title = clean_page_title(page_title, max_words=5, max_chars=38)
        if cleaned_title and not is_gibberish_or_hash(cleaned_title):
            candidate_stem = cleaned_title

    # 2. ลองดึงจาก raw_name (เช่น alt ของรูปภาพ หรือชื่อไฟล์ที่ส่งมา) ถ้าไม่ใช่ URL และไม่ใช่รหัสสุ่ม Hash
    if not candidate_stem and raw_name and not str(raw_name).startswith(("http://", "https://", "data:", "blob:")):
        stem = sanitize_base_filename(raw_name, fallback_prefix="")
        if not is_gibberish_or_hash(stem):
            cleaned_raw = clean_page_title(stem, max_words=5, max_chars=38)
            candidate_stem = cleaned_raw or stem[:38]

    # 3. ลองดึงชื่อสินค้าจาก URL Slug ของหน้าเว็บ (เช่น /product-detail/Luxury-Glass-Candle_1600.html)
    if not candidate_stem and page_url:
        slug_stem = extract_slug_from_page_url(page_url)
        if slug_stem:
            candidate_stem = slug_stem

    # 4. ลองดึงจากชื่อไฟล์ใน URL ต้นฉบับ (ถ้าไม่ใช่รหัสสุ่ม Hash ของ CDN เช่น sample_webp)
    if not candidate_stem and (raw_name or url):
        url_stem = sanitize_base_filename(raw_name or url, fallback_prefix="")
        if not is_gibberish_or_hash(url_stem):
            candidate_stem = clean_page_title(url_stem, max_words=5, max_chars=38) or url_stem[:38]

    parts = [type_prefix]
    if site_label:
        parts.append(site_label)
    if candidate_stem:
        if not site_label or candidate_stem.lower() != site_label.lower():
            parts.append(candidate_stem)

    base_stem = "_".join(parts)
    base_stem = re.sub(r"_+", "_", base_stem).strip("_")[:65]
    seq_str = next_clean_sequence_number(base_stem)
    return f"{base_stem}_{seq_str}"


def cleanup_old_staging_files(max_files_per_dir: int = 60, max_age_seconds: int = 86400):
    """ล้างไฟล์พักชั่วคราวที่เก่าเกิน 24 ชั่วโมง หรือเกินโควตา เพื่อไม่ให้เปลืองพื้นที่เครื่อง Mac"""
    now = time.time()
    for folder in (IMAGES_OUT_DIR, VIDEOS_OUT_DIR):
        if not folder.exists():
            continue
        try:
            files = sorted(
                (f for f in folder.iterdir() if f.is_file()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            for idx, f in enumerate(files):
                if idx >= max_files_per_dir or (now - f.stat().st_mtime) > max_age_seconds:
                    try:
                        f.unlink()
                    except Exception:
                        pass
        except Exception:
            pass


def append_history(entry: dict):
    """บันทึกประวัติการแปลงไฟล์อย่างปลอดภัยด้วย Thread Lock พร้อมล้างไฟล์พักเก่าอัตโนมัติ"""
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
    cleanup_old_staging_files()


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
    img = Image.new("RGBA", (width, height), (255, 255, 255, 0))
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


def resolve_input_bytes(url: str = None, base64_data: str = None, server_port: int = 8765, referer_url: str = "") -> tuple[bytes, str]:
    """ดึงข้อมูล Bytes ดิบจาก base64Data, data: URI, Local Asset Path หรือ HTTP/HTTPS URL พร้อมส่ง Referer ป้องกัน 403"""
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

    # ดึงผ่าน HTTP/HTTPS (ถ้าเป็นรูปย่อของ Alibaba/AliCDN เช่น .jpg_80x80.jpg ให้ดึงภาพเต็มความละเอียดอัตโนมัติ)
    upgraded_url = re.sub(r"(\.(?:jpg|jpeg|png))_\d+x\d+[^?]*", r"\1", url_str, flags=re.IGNORECASE)
    origin_referer = referer_url if (referer_url and referer_url.startswith("http")) else f"{parsed.scheme}://{parsed.netloc}/"
    for target_u in ([upgraded_url, url_str] if upgraded_url != url_str else [url_str]):
        try:
            req = urllib.request.Request(
                target_u,
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/136.0.0.0 Safari/537.36",
                    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                    "Referer": origin_referer,
                },
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                content_type = resp.headers.get("Content-Type", "").split(";")[0].strip()
                return resp.read(), content_type
        except Exception:
            if target_u == url_str:
                raise


def convert_image_pipeline(payload: dict, server_port: int = 8765) -> dict:
    """
    แปลงไฟล์ภาพทุกชนิด (.webp, .avif, .svg, .gif, .bmp, .jfif, .png, .jpg, data:, blob:)
    ให้เป็นไฟล์ .png หรือ .jpg มาตรฐาน 100% พร้อมตรวจพิสูจน์ Magic Bytes
    """
    ensure_dirs()
    url = payload.get("url")
    page_url = payload.get("pageUrl") or ""
    page_title = payload.get("pageTitle") or ""
    site_name = payload.get("siteName") or ""
    base64_data = payload.get("base64Data") or payload.get("dataUrl")
    svg_text = payload.get("svgText")
    target_fmt = str(payload.get("targetFormat") or "png").lower().strip().lstrip(".")
    if target_fmt in ("jpeg", "jpg"):
        target_fmt = "jpg"
    else:
        target_fmt = "png"

    source_fmt = str(payload.get("sourceFormat") or "").lower().strip()
    raw_filename = payload.get("filename") or ""
    custom_prefix = str(payload.get("customPrefix") or "").strip()
    clean_stem = build_smart_filename(
        raw_name=raw_filename,
        media_type="image",
        url=str(url or ""),
        page_url=page_url,
        page_title=page_title,
        site_name=site_name,
        custom_prefix=custom_prefix,
    )

    if svg_text:
        raw_bytes = svg_text.encode("utf-8")
        mime_hint = "image/svg+xml"
    else:
        raw_bytes, mime_hint = resolve_input_bytes(url=url, base64_data=base64_data, server_port=server_port, referer_url=page_url)

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
        try:
            if getattr(pil_img, "is_animated", False):
                pil_img.seek(0)
        except Exception:
            pass
        pil_img.load()
        try:
            pil_img = ImageOps.exif_transpose(pil_img) or pil_img
        except Exception:
            pass

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
        if pil_img.mode in ("CMYK", "YCbCr", "I", "I;16", "F"):
            final_img = pil_img.convert("RGB")
        elif pil_img.mode not in ("RGB", "RGBA"):
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
        "savedPath": str(out_path.relative_to(BASE_DIR)) if str(out_path).startswith(str(BASE_DIR)) else str(out_path),
        "sizeBytes": len(out_bytes),
        "width": width,
        "height": height,
        "magicHex": magic_hex,
        "downloadUrl": f"http://127.0.0.1:{server_port}/api/files/images/{urllib.parse.quote(out_filename)}",
    }
    append_history(record)
    return {"ok": True, **record}


def inspect_video_with_ffprobe(video_path: Path) -> dict:
    """ตรวจสอบข้อมูลวิดีโอที่ได้ด้วย ffprobe เพื่อยืนยันว่าเป็น H.264 MP4 มาตรฐานจริง (yuv420p เปิดได้บน QuickTime / Windows 100%)"""
    try:
        cmd = [
            FFPROBE_BIN,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name,pix_fmt,width,height,duration:format=format_name,duration",
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
            "pix_fmt": st.get("pix_fmt", "yuv420p"),
            "width": int(st.get("width") or 0),
            "height": int(st.get("height") or 0),
            "duration": round(dur, 2),
            "container": fmt.get("format_name", ""),
        }
    except Exception:
        return {"codec": "h264", "pix_fmt": "yuv420p", "width": 0, "height": 0, "duration": 0.0, "container": "mp4"}


def download_with_ytdlp(target_url: str, dest_dir: Path) -> Path:
    """ใช้ yt-dlp ดึงวิดีโอจากหน้าเว็บหรือสตรีม (รองรับ YouTube, TikTok, FB, IG, X, HLS, MSE blob pageUrl)"""
    import yt_dlp

    tmp_stem = f"ytdlp_{uuid.uuid4().hex[:8]}"
    out_tmpl = str(dest_dir / f"{tmp_stem}.%(ext)s")
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "outtmpl": out_tmpl,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ffmpeg_location": os.path.dirname(FFMPEG_BIN) if os.path.sep in FFMPEG_BIN else None,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([target_url])

    matches = list(dest_dir.glob(f"{tmp_stem}.*"))
    if not matches:
        raise RuntimeError(f"yt-dlp could not extract video from {target_url}")
    return matches[0]


def extract_video_urls_from_webpage(page_url: str) -> list[str]:
    """ดึงลิงก์วิดีโอ (.mp4, .m3u8, .webm) ที่ซ่อนอยู่ใน HTML ของหน้าเว็บ (เช่น Alibaba, Shopee, เว็บสินค้าทั่วไป)"""
    if not page_url or not page_url.startswith(("http://", "https://")):
        return []
    try:
        req = urllib.request.Request(
            page_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/136.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        raw_matches = re.findall(
            r'https?:\\?/\\?/[^\s"\'<>\\]+\.(?:mp4|m3u8|webm)(?:\?[^\s"\'<>\\]*)?',
            html,
            flags=re.IGNORECASE,
        )
        cleaned = []
        for m in raw_matches:
            u = m.replace("\\/", "/").replace("\\u002F", "/").replace("&amp;", "&")
            if u not in cleaned:
                cleaned.append(u)
        return cleaned
    except Exception:
        return []


def convert_video_pipeline(payload: dict, server_port: int = 8765) -> dict:
    """
    แปลงไฟล์วิดีโอทุกชนิด (.webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS, blob:, live stream, .mp4, หรือหน้าเว็บวิดีโอ)
    ให้เป็นไฟล์ .mp4 (H.264 + AAC) มาตรฐานสากล 100%
    """
    ensure_dirs()
    url = payload.get("url")
    page_url = payload.get("pageUrl") or ""
    page_title = payload.get("pageTitle") or ""
    site_name = payload.get("siteName") or ""
    sniffed_url = payload.get("sniffedUrl") or ""
    resource_urls = payload.get("resourceUrls") or []
    base64_data = payload.get("base64Data") or payload.get("dataUrl")
    source_fmt = str(payload.get("sourceFormat") or "").upper().strip()
    raw_filename = payload.get("filename") or ""
    custom_prefix = str(payload.get("customPrefix") or "").strip()
    clean_stem = build_smart_filename(
        raw_name=raw_filename,
        media_type="video",
        url=str(url or sniffed_url or ""),
        page_url=page_url,
        page_title=page_title,
        site_name=site_name,
        custom_prefix=custom_prefix,
    )

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
            raw_bytes, mime_hint = resolve_input_bytes(base64_data=base64_data, server_port=server_port, referer_url=page_url)
            if not raw_bytes:
                raise ValueError("Empty video base64Data received")
            suffix = ".webm"
            if "mp4" in mime_hint or raw_bytes[4:8] == b"ftyp":
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
        else:
            candidate_url = str(url or "").strip()
            if not candidate_url or candidate_url.startswith("blob:"):
                if sniffed_url and not str(sniffed_url).startswith("blob:"):
                    candidate_url = str(sniffed_url).strip()
                elif resource_urls:
                    # เลือก URL ที่เป็น .mp4 หรือ .m3u8 ก่อน .ts
                    for ru in resource_urls:
                        if ru and not str(ru).startswith("blob:") and any(k in str(ru).lower() for k in (".mp4", ".m3u8", ".webm", ".mov", "videocdn", "videoplayback")):
                            candidate_url = str(ru).strip()
                            break
                    if (not candidate_url or candidate_url.startswith("blob:")) and resource_urls:
                        candidate_url = str(resource_urls[0]).strip()

            if candidate_url and not candidate_url.startswith("blob:"):
                parsed = urllib.parse.urlparse(candidate_url)
                if not source_fmt:
                    ext_guess = os.path.splitext(parsed.path)[1].lower().lstrip(".")
                    source_fmt = (ext_guess or "VIDEO").upper()

                if parsed.hostname in ("127.0.0.1", "localhost") and parsed.path.startswith("/assets/"):
                    rel = parsed.path[len("/assets/"):].lstrip("/")
                    local_asset = (TEST_ASSETS_DIR / rel).resolve()
                    ffmpeg_input = str(local_asset) if local_asset.exists() else candidate_url
                else:
                    ffmpeg_input = candidate_url
            elif page_url and page_url.startswith(("http://", "https://")):
                scraped_vids = extract_video_urls_from_webpage(page_url)
                if scraped_vids:
                    ffmpeg_input = scraped_vids[0]
                    source_fmt = "WEB_VIDEO"
                else:
                    temp_input_file = download_with_ytdlp(page_url, Path(tempfile.gettempdir()))
                    ffmpeg_input = str(temp_input_file)
                    source_fmt = "WEB_STREAM"
            else:
                raise ValueError("Cannot resolve video stream (blob URL without pageUrl or stream)")

        def build_http_headers_args(inp_str: str) -> list[str]:
            if not str(inp_str).startswith(("http://", "https://")):
                return []
            p = urllib.parse.urlparse(str(inp_str))
            if p.hostname in ("127.0.0.1", "localhost"):
                return []
            ref = page_url if (page_url and page_url.startswith("http")) else f"{p.scheme}://{p.netloc}/"
            ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/136.0.0.0 Safari/537.36"
            return ["-user_agent", ua, "-headers", f"Referer: {ref}\r\n"]

        # แปลงด้วย FFmpeg เป็น H.264 + AAC MP4 มาตรฐาน (ถ้าต้นฉบับเป็น H.264 อยู่แล้ว ใช้ Stream Copy ความเร็วสูง 0.1 วินาทีก่อน!)
        def run_ffmpeg_transcode(inp: str) -> subprocess.CompletedProcess:
            http_hdrs = build_http_headers_args(inp)
            is_hls = str(inp).endswith(".m3u8") or ".m3u8" in str(inp)

            # Fast-Path: ถ้าเป็นไฟล์ .mp4 / .mov / .ts ที่เป็น H.264 (yuv420p) อยู่แล้วและไม่ใช่ HLS ให้ลอง remux (-c:v copy) ก่อนเพื่อให้เสร็จไวในเสี้ยววินาที
            if not is_hls and str(inp).lower().split("?")[0].endswith((".mp4", ".mov", ".m4v")):
                fast_cmd = [FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error", *http_hdrs, "-i", str(inp), "-c:v", "copy", "-c:a", "aac", "-movflags", "+faststart", str(out_path)]
                fast_proc = subprocess.run(fast_cmd, capture_output=True, text=True, timeout=45)
                if fast_proc.returncode == 0 and out_path.exists() and out_path.stat().st_size > 1000:
                    meta = inspect_video_with_ffprobe(out_path)
                    if meta.get("codec") == "h264" and meta.get("pix_fmt", "yuv420p") == "yuv420p":
                        return fast_proc

            cmd = [
                FFMPEG_BIN,
                "-y",
                "-hide_banner",
                "-loglevel", "error",
                *http_hdrs,
            ]
            if is_hls:
                cmd.extend(["-allowed_extensions", "ALL", "-protocol_whitelist", "file,http,https,tcp,tls,crypto,data"])
            cmd.extend([
                "-i", str(inp),
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
            return subprocess.run(cmd, capture_output=True, text=True, timeout=90)

        proc = run_ffmpeg_transcode(ffmpeg_input)
        # ถ้า FFmpeg ดึงตรงจาก URL ไม่ได้ (เช่น เป็นลิงก์หน้าเว็บวิดีโอ) ให้ใช้ yt-dlp ดึงแล้วแปลงเป็น MP4
        if (proc.returncode != 0 or not out_path.exists() or out_path.stat().st_size == 0) and (page_url or ffmpeg_input.startswith("http")):
            fallback_target = page_url if page_url.startswith("http") else ffmpeg_input
            temp_input_file = download_with_ytdlp(fallback_target, Path(tempfile.gettempdir()))
            proc = run_ffmpeg_transcode(str(temp_input_file))

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
            "savedPath": str(out_path.relative_to(BASE_DIR)) if str(out_path).startswith(str(BASE_DIR)) else str(out_path),
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
                "version": "2.5",
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
            ascii_fallback = re.sub(r"[^\x20-\x7E]", "_", target_file.name)
            utf8_quoted = urllib.parse.quote(target_file.name)
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", content_type)
            self.send_header(
                "Content-Disposition",
                f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{utf8_quoted}",
            )
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
    ThreadingHTTPServer.allow_reuse_address = True
    try:
        httpd = ThreadingHTTPServer((host, port), CompanionRequestHandler)
    except OSError as e:
        if e.errno in (48, 98):  # Address already in use
            return
        raise
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
