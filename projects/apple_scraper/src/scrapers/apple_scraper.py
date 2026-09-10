import urllib.request
import urllib.parse
import re
import json
from typing import Dict, Any, List, Optional
from config.settings import DEFAULT_HEADERS, BASE_APPLE_URL, DEFAULT_LOCALE
from src.services.formatter import AppleDataFormatter

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class AppleScraper:
    """Scraper สำหรับดึงข้อมูลภาพรวมสินค้า ราคาทางการ และตัวเลือกสี/ความจุจาก Apple.com"""

    def __init__(self, locale: str = DEFAULT_LOCALE, headers: Optional[Dict[str, str]] = None):
        self.locale = locale.strip("/")
        self.base_url = f"{BASE_APPLE_URL}/{self.locale}" if self.locale else BASE_APPLE_URL
        self.headers = headers or DEFAULT_HEADERS

    def normalize_url(self, target_url: str) -> str:
        """แปลง URL ให้อยู่ในโดเมนและ Locale ที่ถูกต้อง"""
        target = target_url.strip()
        if not target.startswith("http"):
            target = f"{self.base_url.rstrip('/')}/{target.lstrip('/')}"
        return target

    def fetch_page_html(self, url: str) -> Optional[str]:
        """ดาวน์โหลด HTML ของหน้าเว็บ Apple"""
        full_url = self.normalize_url(url)
        req = urllib.request.Request(full_url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                return res.read().decode("utf-8", errors="ignore")
        except Exception as e:
            print(f"❌ [AppleScraper] ไม่สามารถดาวน์โหลด {full_url}: {e}")
            return None

    def parse_product_overview(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """สกัดข้อมูลจากหน้าภาพรวมสินค้าหรือหน้า Buy Flow"""
        title = ""
        description = ""
        images = []
        json_ld_data = {}
        starting_price_thb = None
        price_text = ""
        specs_url = None
        buy_url = None

        if HAS_BS4:
            soup = BeautifulSoup(html_content, "html.parser")
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = og_title["content"].strip()
            elif soup.title:
                title = soup.title.text.strip()

            og_desc = soup.find("meta", property="og:description")
            if og_desc and og_desc.get("content"):
                description = og_desc["content"].strip()

            og_image = soup.find("meta", property="og:image")
            if og_image and og_image.get("content"):
                images.append(og_image["content"])

            for img in soup.find_all("img", src=True):
                src = img["src"]
                if ("product" in src or "overview" in src or "hero" in src) and not "icon" in src and not "svg" in src:
                    full_img = urllib.parse.urljoin(source_url, src)
                    if full_img not in images:
                        images.append(full_img)

            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    content = json.loads(script.string)
                    if isinstance(content, dict) and (content.get("@type") == "Product" or "offers" in content):
                        json_ld_data = content
                        break
                except Exception:
                    pass

            for a in soup.find_all("a", href=True):
                href = a["href"]
                clean_href = href.split("?")[0].rstrip("/")
                if clean_href.endswith("/specs") or "specs" in clean_href.split("/")[-1]:
                    specs_url = urllib.parse.urljoin(source_url, href)
                if "/shop/buy-" in href or "/buy" in href:
                    buy_url = urllib.parse.urljoin(source_url, href)

        else:
            # Fallback ใช้ Regex เมื่อไม่มี bs4
            title_m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.I)
            if not title_m:
                title_m = re.search(r'<title>(.*?)</title>', html_content, re.I | re.S)
            if title_m:
                title = title_m.group(1).strip()

            desc_m = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.I)
            if desc_m:
                description = desc_m.group(1).strip()

            img_m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html_content, re.I)
            if img_m:
                images.append(img_m.group(1).strip())

            raw_imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content, re.I)
            for src in raw_imgs:
                if ("product" in src or "overview" in src or "hero" in src) and not "icon" in src and not "svg" in src:
                    full_img = urllib.parse.urljoin(source_url, src)
                    if full_img not in images:
                        images.append(full_img)

            json_ld_blocks = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_content, re.DOTALL)
            for block in json_ld_blocks:
                try:
                    content = json.loads(block.strip())
                    if isinstance(content, dict) and (content.get("@type") == "Product" or "offers" in content):
                        json_ld_data = content
                        break
                except Exception:
                    pass

            links = re.findall(r'<a[^>]+href=["\']([^"\']+)["\']', html_content, re.I)
            for href in links:
                clean_href = href.split("?")[0].rstrip("/")
                if clean_href.endswith("/specs") or "specs" in clean_href.split("/")[-1]:
                    specs_url = urllib.parse.urljoin(source_url, href)
                if "/shop/buy-" in href or "/buy" in href:
                    buy_url = urllib.parse.urljoin(source_url, href)

        title = re.sub(r'\s*-\s*Apple\s*\([^\)]+\)', '', title).strip()

        # หาราคา
        price_patterns = [
            r'(?:เริ่มต้นที่|ราคาเริ่มต้น|เริ่มต้นเพียง|฿)\s*([\d,]{4,7})',
            r'฿\s*([\d,]{4,7})'
        ]
        for pat in price_patterns:
            matches = re.findall(pat, html_content)
            for m in matches:
                parsed = AppleDataFormatter.parse_price(m)
                if parsed and parsed > 5000:
                    starting_price_thb = parsed
                    price_text = f"฿{parsed:,}"
                    break
            if starting_price_thb:
                break

        if not starting_price_thb and json_ld_data:
            offers = json_ld_data.get("offers", {})
            if isinstance(offers, dict) and offers.get("price"):
                starting_price_thb = AppleDataFormatter.parse_price(str(offers.get("price")))
                if starting_price_thb:
                    price_text = f"฿{starting_price_thb:,}"

        slug = source_url.strip("/").split("/")[-1].split("?")[0]
        family_info = AppleDataFormatter.extract_model_and_family(title or slug)

        return {
            "status": "success",
            "title": title or slug,
            "slug": slug,
            "family": family_info["family"],
            "url": source_url,
            "specs_url": specs_url,
            "buy_url": buy_url,
            "starting_price_thb": starting_price_thb,
            "starting_price_text": price_text,
            "currency": "THB" if "th" in self.locale else "USD",
            "description": description,
            "images_count": len(images),
            "images": images[:10],
            "schema_ld": bool(json_ld_data)
        }

    def scrape_product(self, product_path_or_url: str) -> Dict[str, Any]:
        """เรียกทำงานดึงข้อมูลสินค้าจาก URL ที่ระบุ"""
        full_url = self.normalize_url(product_path_or_url)
        html = self.fetch_page_html(full_url)
        if not html:
            return {
                "status": "error",
                "message": f"ไม่สามารถเปิดอ่านข้อมูลจาก {full_url}",
                "url": full_url
            }

        data = self.parse_product_overview(html, full_url)
        return data
