import sys
import json
import csv
import time
import re
import urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Set project base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR, DEFAULT_HEADERS

INSTAGRAM_DATA_DIR = DATA_DIR / "instagram"
INSTAGRAM_IMAGES_DIR = DATA_DIR / "images" / "instagram"

INSTAGRAM_DATA_DIR.mkdir(parents=True, exist_ok=True)
INSTAGRAM_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

def fetch_single_post(index: int, post_url: str):
    """ดึงข้อความแคปชั่นและรูปรวมของแต่ละโพสต์"""
    clean_url = post_url.split("?")[0].rstrip("/")
    shortcode = clean_url.split("/")[-1]
    
    # 1. ดึงข้อความแคปชั่นและรูปปกผ่าน oEmbed
    oembed_url = f"https://www.instagram.com/api/v1/oembed/?url={clean_url}"
    caption = ""
    images = []
    
    try:
        req = urllib.request.Request(oembed_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=8) as res:
            data = json.loads(res.read().decode("utf-8"))
            caption = data.get("title", "")
            thumb = data.get("thumbnail_url")
            if thumb:
                images.append(thumb)
    except Exception as e:
        pass

    # 2. พยายามดึงรูปเพิ่มเติมจาก Embed page
    try:
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
        req2 = urllib.request.Request(embed_url, headers=DEFAULT_HEADERS)
        with urllib.request.urlopen(req2, timeout=8) as res2:
            html = res2.read().decode("utf-8")
            found_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
            for img in found_imgs:
                img_clean = img.replace("&amp;", "&")
                if "scontent" in img_clean or "fbcdn" in img_clean:
                    if "s100x100" not in img_clean and "s150x150" not in img_clean and "p50x50" not in img_clean:
                        if img_clean not in images:
                            images.append(img_clean)
    except Exception:
        pass

    # 3. ดาวน์โหลดรูปภาพทั้งหมดลงโฟลเดอร์ในเครื่อง
    post_folder = INSTAGRAM_IMAGES_DIR / f"post_{index:03d}"
    post_folder.mkdir(parents=True, exist_ok=True)
    
    local_image_paths = []
    for img_idx, img_url in enumerate(images, start=1):
        img_filename = f"img_{img_idx}.jpg"
        img_dest = post_folder / img_filename
        
        try:
            img_req = urllib.request.Request(img_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(img_req, timeout=10) as img_res:
                with open(img_dest, "wb") as f:
                    f.write(img_res.read())
            local_image_paths.append(str(img_dest.relative_to(BASE_DIR)))
        except Exception as e:
            pass

    return {
        "index": index,
        "shortcode": shortcode,
        "post_url": clean_url,
        "caption": caption,
        "images_count": len(local_image_paths),
        "local_images": local_image_paths,
        "image_urls": images
    }

def process_all_posts(max_workers: int = 6):
    links_file = BASE_DIR / "instagram_all_links.txt"
    if not links_file.exists():
        print(f"❌ ไม่พบไฟล์ {links_file}")
        return

    with open(links_file, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    total = len(urls)
    print("=" * 65)
    print(f"🚀 กำลังเริ่มดึงข้อมูลและดาวน์โหลดรูปภาพทั้งหมด {total} โพสต์...")
    print(f"📁 โฟลเดอร์เก็บข้อมูล: {INSTAGRAM_DATA_DIR}")
    print(f"🖼️  โฟลเดอร์เก็บรูปภาพ: {INSTAGRAM_IMAGES_DIR}")
    print("=" * 65)

    results = []
    completed_count = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_single_post, i, url): i for i, url in enumerate(urls, start=1)}
        
        for future in as_completed(futures):
            item = future.result()
            results.append(item)
            completed_count += 1
            
            if completed_count % 15 == 0 or completed_count == total:
                print(f"⏳ คืบหน้า: [{completed_count}/{total}] โพสต์เสร็จสิ้น ({(completed_count/total)*100:.1f}%)")

    # เรียงลำดับตาม Index
    results.sort(key=lambda x: x["index"])

    # 1. บันทึก JSON รวมทั้งหมด
    json_path = INSTAGRAM_DATA_DIR / "all_posts_data.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 2. บันทึก CSV สรุป
    csv_path = INSTAGRAM_DATA_DIR / "posts_summary.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "shortcode", "post_url", "images_count", "caption_preview"])
        for r in results:
            preview = r["caption"].replace("\n", " ")[:120]
            writer.writerow([r["index"], r["shortcode"], r["post_url"], r["images_count"], preview])

    total_downloaded_images = sum(r["images_count"] for r in results)
    print("\n" + "=" * 65)
    print("🎉 ดึงข้อมูลและดาวน์โหลดรูปภาพเสร็จสมบูรณ์ 100%!")
    print(f"📝 โพสต์ทั้งหมด: {len(results)} โพสต์")
    print(f"📸 รูปภาพที่ดาวน์โหลดลงเครื่องทั้งหมด: {total_downloaded_images} รูป")
    print(f"📄 บันทึกไฟล์ JSON รวม: {json_path}")
    print(f"📊 บันทึกไฟล์ CSV สรุป:  {csv_path}")
    print(f"📂 โฟลเดอร์รูปภาพ:        {INSTAGRAM_IMAGES_DIR}")
    print("=" * 65)

if __name__ == "__main__":
    process_all_posts(max_workers=8)
