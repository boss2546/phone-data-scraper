import sys
import json
import csv
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR

LINKS_DIR = DATA_DIR / "links"
LINKS_DIR.mkdir(parents=True, exist_ok=True)

def extract_links():
    # 1. Extract Facebook Links
    fb_file = Path("facebook_group_user_posts_1786864985160.json")
    fb_links = []
    if fb_file.exists():
        with open(fb_file, "r", encoding="utf-8") as f:
            fb_posts = json.load(f)
        
        fb_txt = LINKS_DIR / "facebook_post_links.txt"
        with open(fb_txt, "w", encoding="utf-8") as f:
            for p in fb_posts:
                url = p.get("post_url")
                if url:
                    fb_links.append(url)
                    f.write(url + "\n")
        print(f"✅ บันทึกลิงก์ Facebook ทั้งหมด: {len(fb_links)} ลิงก์ -> {fb_txt}")

    # 2. Extract Instagram Links
    ig_file = DATA_DIR / "json" / "instagram_mynowphone.shop.json"
    ig_links = []
    if ig_file.exists():
        with open(ig_file, "r", encoding="utf-8") as f:
            ig_data = json.load(f)
        
        ig_posts = ig_data.get("posts", [])
        ig_txt = LINKS_DIR / "instagram_post_links.txt"
        with open(ig_txt, "w", encoding="utf-8") as f:
            for p in ig_posts:
                url = p.get("url")
                if url:
                    ig_links.append(url)
                    f.write(url + "\n")
        print(f"✅ บันทึกลิงก์ Instagram ทั้งหมด: {len(ig_links)} ลิงก์ -> {ig_txt}")

    # 3. Create Combined CSV Summary of all links
    combined_csv = LINKS_DIR / "all_extracted_links.csv"
    with open(combined_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["platform", "index", "post_url", "images_count", "caption_preview"])
        
        if fb_file.exists():
            for p in fb_posts:
                writer.writerow([
                    "facebook",
                    p.get("post_index"),
                    p.get("post_url"),
                    p.get("images_count"),
                    p.get("content", "").replace("\n", " ")[:100]
                ])

        if ig_file.exists():
            for i, p in enumerate(ig_posts, 1):
                writer.writerow([
                    "instagram",
                    i,
                    p.get("url"),
                    p.get("images_count"),
                    p.get("caption", "").replace("\n", " ")[:100]
                ])

    print(f"📊 สรุปรวมทุกลิงก์เป็นไฟล์ CSV -> {combined_csv}")

if __name__ == "__main__":
    extract_links()
