#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎨 Asset & Test Media Generator for Universal Media Grabber Extension
สร้างไอคอนจริงสำหรับ Chrome Extension (16x16, 48x48, 128x128)
และสร้างไฟล์ทดสอบจริงครบทุกนามสกุล:
- รูปภาพ: .webp, .avif, .svg, .gif, .bmp, .jfif, .png, .jpg
- วิดีโอ: .mp4, .webm, .ogv, .mov, .mkv, .ts, .m3u8 (HLS Stream)
"""
import os
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw

BASE_DIR = Path(__file__).resolve().parent.parent
EXT_ICONS_DIR = BASE_DIR / "extension" / "icons"
TEST_ASSETS_DIR = BASE_DIR / "data" / "test_assets"
DOWNLOADS_DIR = BASE_DIR / "data" / "downloads"
FFMPEG_BIN = "/opt/homebrew/bin/ffmpeg" if os.path.exists("/opt/homebrew/bin/ffmpeg") else "ffmpeg"


def generate_extension_icons():
    """สร้างไอคอน PNG จริงขนาด 16x16, 48x48, 128x128 ตามกฎเหล็ก Chrome Manifest V3"""
    EXT_ICONS_DIR.mkdir(parents=True, exist_ok=True)
    for size in [16, 48, 128]:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # พื้นหลังไล่สีทรงสี่เหลี่ยมขอบมนสีน้ำเงิน-เขียวมรกต
        margin = max(1, size // 16)
        radius = max(3, size // 4)
        draw.rounded_rectangle(
            [margin, margin, size - margin - 1, size - margin - 1],
            radius=radius,
            fill=(16, 185, 129, 255),  # Emerald #10B981
            outline=(5, 150, 105, 255),
            width=max(1, size // 32),
        )

        # วาดสัญลักษณ์ลูกศรดาวน์โหลดสีขาวตรงกลาง
        cx = size // 2
        top_y = int(size * 0.24)
        mid_y = int(size * 0.56)
        bot_y = int(size * 0.74)
        shaft_w = max(1, size // 10)
        wing_w = max(3, int(size * 0.24))

        # แกนลูกศร
        draw.rectangle(
            [cx - shaft_w, top_y, cx + shaft_w, mid_y],
            fill=(255, 255, 255, 255),
        )
        # หัวลูกศร
        draw.polygon(
            [(cx - wing_w, mid_y - 1), (cx + wing_w, mid_y - 1), (cx, bot_y - 2)],
            fill=(255, 255, 255, 255),
        )
        # ถาดรับด้านล่าง
        tray_y = int(size * 0.78)
        tray_h = max(1, size // 14)
        draw.rectangle(
            [cx - wing_w, tray_y, cx + wing_w, tray_y + tray_h],
            fill=(255, 255, 255, 255),
        )

        icon_path = EXT_ICONS_DIR / f"icon-{size}.png"
        img.save(icon_path, format="PNG")
        print(f"✅ สร้างไอคอน Extension: {icon_path.relative_to(BASE_DIR)} ({size}x{size} px)")


def create_sample_canvas(label: str, bg_color: tuple, accent_color: tuple, width: int = 640, height: int = 400) -> Image.Image:
    """สร้างภาพกราฟิกความละเอียดสูงพร้อมป้ายกำกับสำหรับทดสอบแต่ละนามสกุล"""
    img = Image.new("RGBA", (width, height), (*bg_color, 255))
    draw = ImageDraw.Draw(img)

    # กรอบและลวดลายเรขาคณิต
    draw.rounded_rectangle([16, 16, width - 16, height - 16], radius=24, outline=(*accent_color, 255), width=6)
    draw.ellipse([width - 220, 40, width - 40, 220], fill=(*accent_color, 180))
    draw.rounded_rectangle([40, 40, 380, 140], radius=16, fill=(15, 23, 42, 220))
    draw.text((64, 78), f"FORMAT: {label}", fill=(255, 255, 255, 255))
    draw.text((64, 105), f"Resolution: {width}x{height} -> Standard PNG/JPG", fill=(16, 185, 129, 255))

    # แถบสีทดสอบความแม่นยำของสี (Color Bars)
    bars = [
        (239, 68, 68),
        (245, 158, 11),
        (16, 185, 129),
        (59, 130, 246),
        (139, 92, 246),
        (236, 72, 153),
    ]
    bar_w = (width - 80) // len(bars)
    for i, c in enumerate(bars):
        x0 = 40 + i * bar_w
        draw.rectangle([x0, height - 120, x0 + bar_w - 6, height - 45], fill=(*c, 255))

    return img


def generate_test_images():
    """สร้างไฟล์ภาพทดสอบครบทุกนามสกุลแปลกและนามสกุลมาตรฐาน"""
    img_dir = TEST_ASSETS_DIR / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    # 1. WebP (.webp)
    im_webp = create_sample_canvas("WEBP (.webp)", (30, 41, 59), (56, 189, 248))
    im_webp.save(img_dir / "sample_webp.webp", format="WEBP", quality=92)

    # 2. AVIF (.avif)
    im_avif = create_sample_canvas("AVIF (.avif)", (49, 46, 129), (167, 139, 250))
    im_avif.save(img_dir / "sample_avif.avif", format="AVIF", quality=90)

    # 3. GIF (.gif) - 2 frames animated GIF
    im_gif1 = create_sample_canvas("GIF FRAME 1 (.gif)", (6, 78, 59), (52, 211, 153)).convert("RGB")
    im_gif2 = create_sample_canvas("GIF FRAME 2 (.gif)", (20, 83, 45), (16, 185, 129)).convert("RGB")
    im_gif1.save(img_dir / "sample_gif.gif", format="GIF", save_all=True, append_images=[im_gif2], duration=400, loop=0)

    # 4. BMP (.bmp)
    im_bmp = create_sample_canvas("BMP (.bmp)", (124, 45, 18), (251, 146, 60)).convert("RGB")
    im_bmp.save(img_dir / "sample_bmp.bmp", format="BMP")

    # 5. JFIF (.jfif)
    im_jfif = create_sample_canvas("JFIF (.jfif)", (112, 26, 117), (244, 114, 182)).convert("RGB")
    im_jfif.save(img_dir / "sample_jfif.jfif", format="JPEG", quality=92)

    # 6. PNG (.png)
    im_png = create_sample_canvas("PNG (.png)", (15, 23, 42), (34, 197, 94))
    im_png.save(img_dir / "sample_png.png", format="PNG")

    # 7. JPG (.jpg)
    im_jpg = create_sample_canvas("JPG (.jpg)", (39, 39, 42), (250, 204, 21)).convert("RGB")
    im_jpg.save(img_dir / "sample_jpg.jpg", format="JPEG", quality=92)

    # 8. SVG (.svg)
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400" viewBox="0 0 640 400">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e3a8a"/>
    </linearGradient>
  </defs>
  <rect width="640" height="400" rx="20" fill="url(#bg)"/>
  <rect x="20" y="20" width="600" height="360" rx="16" fill="none" stroke="#38bdf8" stroke-width="5"/>
  <circle cx="500" cy="140" r="80" fill="#10b981" opacity="0.85"/>
  <polygon points="500,90 475,145 525,145" fill="#ffffff"/>
  <rect x="465" y="155" width="70" height="14" rx="4" fill="#ffffff"/>
  <text x="50" y="95" fill="#ffffff" font-family="system-ui, sans-serif" font-size="32" font-weight="bold">SVG VECTOR (.svg)</text>
  <text x="50" y="140" fill="#38bdf8" font-family="system-ui, sans-serif" font-size="20">Auto-Rasterized to Crisp PNG / JPG</text>
  <rect x="50" y="260" width="90" height="65" rx="8" fill="#ef4444"/>
  <rect x="155" y="260" width="90" height="65" rx="8" fill="#f59e0b"/>
  <rect x="260" y="260" width="90" height="65" rx="8" fill="#10b981"/>
  <rect x="365" y="260" width="90" height="65" rx="8" fill="#3b82f6"/>
  <rect x="470" y="260" width="90" height="65" rx="8" fill="#8b5cf6"/>
</svg>"""
    (img_dir / "sample_svg.svg").write_text(svg_content, encoding="utf-8")

    print(f"✅ สร้างไฟล์รูปภาพทดสอบครบ 8 นามสกุล ใน {img_dir.relative_to(BASE_DIR)}/")


def run_ffmpeg(args: list, desc: str):
    cmd = [FFMPEG_BIN, "-y", "-hide_banner", "-loglevel", "error"] + args
    subprocess.run(cmd, check=True)
    print(f"✅ สร้างไฟล์วิดีโอทดสอบ: {desc}")


def generate_test_videos():
    """สร้างไฟล์วิดีโอทดสอบจริงครบทุกนามสกุล (.mp4, .webm, .ogv, .mov, .mkv, .ts, .m3u8 HLS)"""
    vid_dir = TEST_ASSETS_DIR / "videos"
    vid_dir.mkdir(parents=True, exist_ok=True)

    # 1. Base MP4 (H.264 + AAC, 2 วินาที, 480x270)
    mp4_path = vid_dir / "sample_mp4.mp4"
    run_ffmpeg(
        [
            "-f", "lavfi", "-i", "testsrc=duration=2:size=480x270:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=660:duration=2",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
            str(mp4_path),
        ],
        "sample_mp4.mp4 (H.264/AAC)",
    )

    # 2. WebM (.webm - VP8 + Vorbis/Opus)
    webm_path = vid_dir / "sample_webm.webm"
    run_ffmpeg(
        [
            "-f", "lavfi", "-i", "testsrc2=duration=2:size=480x270:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=520:duration=2",
            "-c:v", "libvpx", "-b:v", "400k", "-pix_fmt", "yuv420p",
            "-an",
            str(webm_path),
        ],
        "sample_webm.webm (VP8 WebM)",
    )

    # 3. OGV / Ogg Video (.ogv - VP8 in Ogg container)
    ogv_path = vid_dir / "sample_ogv.ogv"
    run_ffmpeg(
        [
            "-i", str(webm_path),
            "-c", "copy",
            "-f", "ogg",
            str(ogv_path),
        ],
        "sample_ogv.ogv (Ogg Video)",
    )

    # 4. QuickTime MOV (.mov)
    mov_path = vid_dir / "sample_mov.mov"
    run_ffmpeg(
        [
            "-i", str(mp4_path),
            "-c", "copy",
            "-f", "mov",
            str(mov_path),
        ],
        "sample_mov.mov (QuickTime MOV)",
    )

    # 5. Matroska MKV (.mkv)
    mkv_path = vid_dir / "sample_mkv.mkv"
    run_ffmpeg(
        [
            "-i", str(mp4_path),
            "-c", "copy",
            "-f", "matroska",
            str(mkv_path),
        ],
        "sample_mkv.mkv (Matroska MKV)",
    )

    # 6. MPEG-TS (.ts)
    ts_path = vid_dir / "sample_ts.ts"
    run_ffmpeg(
        [
            "-i", str(mp4_path),
            "-c", "copy",
            "-f", "mpegts",
            str(ts_path),
        ],
        "sample_ts.ts (MPEG Transport Stream)",
    )

    # 7. HLS Stream (.m3u8 + .ts segments)
    m3u8_path = vid_dir / "sample_hls.m3u8"
    run_ffmpeg(
        [
            "-i", str(mp4_path),
            "-c", "copy",
            "-start_number", "0",
            "-hls_time", "1",
            "-hls_list_size", "0",
            "-f", "hls",
            str(m3u8_path),
        ],
        "sample_hls.m3u8 (HLS Stream Playlist + Segments)",
    )


def main():
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    (DOWNLOADS_DIR / "images").mkdir(parents=True, exist_ok=True)
    (DOWNLOADS_DIR / "videos").mkdir(parents=True, exist_ok=True)
    generate_extension_icons()
    generate_test_images()
    generate_test_videos()
    print("\n🎉 สร้างไอคอนและไฟล์มีเดียทดสอบครบทุกนามสกุลเรียบร้อยแล้ว!")


if __name__ == "__main__":
    main()
