import sys
import re
import urllib.request
import urllib.parse
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.settings import DATA_DIR, DEFAULT_HEADERS

RAW_HTML_DIR = DATA_DIR / "raw_html"
RAW_HTML_DIR.mkdir(parents=True, exist_ok=True)

class RawHtmlScraper:
    """ดาวน์โหลดไฟล์ HTML ดิบทั้งหน้าเว็บลงเครื่อง และช่วยวิเคราะห์/ดึงข้อมูลตามจุดที่ต้องการ"""

    @staticmethod
    def save_raw_html(url: str, custom_filename: str = None) -> Path:
        """ดาวน์โหลด HTML ของ URL ใดๆ แล้วบันทึกเป็นไฟล์ .html"""
        headers = {
            **DEFAULT_HEADERS,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                html_content = res.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"❌ ไม่สามารถดาวน์โหลด HTML จาก {url}: {e}")
            return None

        # ตั้งชื่อไฟล์อัตโนมัติจาก URL
        if not custom_filename:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.replace("www.", "").split(".")[0]
            slug = re.sub(r'[^a-zA-Z0-9_-]', '_', parsed.path.strip("/").split("/")[-1])
            if not slug:
                slug = "index"
            custom_filename = f"{domain}_{slug}.html"
        
        if not custom_filename.endswith(".html"):
            custom_filename += ".html"

        out_path = RAW_HTML_DIR / custom_filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ บันทึก Raw HTML สำเร็จ: {out_path} (ขนาด: {len(html_content):,} ตัวอักษร)")
        return out_path

    @staticmethod
    def inspect_html(html_file_path: Path):
        """วิเคราะห์เบื้องต้นของไฟล์ HTML: หัวข้อ, แท็ก meta, รูปภาพ, ลิงก์, สคริปต์ JSON-LD"""
        if not html_file_path.exists():
            print(f"❌ ไม่พบไฟล์ {html_file_path}")
            return

        with open(html_file_path, "r", encoding="utf-8") as f:
            html = f.read()

        title_m = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_m.group(1).strip() if title_m else "ไม่มี title"

        images = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
        links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html, re.IGNORECASE)
        json_ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)

        print("=" * 60)
        print(f"📄 รายละเอียดไฟล์ HTML: {html_file_path.name}")
        print(f"🏷️  Page Title: {title}")
        print(f"🖼️  จำนวนแท็กรูปภาพ <img>: {len(images)} รูป")
        print(f"🔗 จำนวนลิงก์ <a>: {len(links)} ลิงก์")
        print(f"📦 จำนวน JSON-LD Schema: {len(json_ld)} บล็อก")
        print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        saved_file = RawHtmlScraper.save_raw_html(target_url)
        if saved_file:
            RawHtmlScraper.inspect_html(saved_file)
    else:
        print("💡 วิธีใช้: python3 src/scrapers/html_scraper.py <URL>")
