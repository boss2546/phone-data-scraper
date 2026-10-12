import urllib.request
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config.settings import LINKS_DIR, DEFAULT_HEADERS, BASE_API_URL

def fetch_compasia_links(pages: List[int] = [1, 2, 3]) -> List[Dict[str, Any]]:
    """
    ดึงรายการสินค้าจาก CompAsia ผ่าน Shopify Products JSON API
    """
    all_products = []
    product_links = []

    print("=" * 64)
    print("🚀 กำลังดึงลิงก์สินค้าจาก CompAsia (Shopify API)...")
    print("=" * 64)

    for page in pages:
        api_url = f"{BASE_API_URL}?page={page}&limit=50"
        print(f"⏳ กำลังดึงหน้า {page}...")
        
        try:
            req = urllib.request.Request(api_url, headers=DEFAULT_HEADERS)
            with urllib.request.urlopen(req, timeout=12) as res:
                data = json.loads(res.read().decode("utf-8"))
            
            products = data.get("products", [])
            if not products:
                print(f"   ↳ หน้า {page} ไม่มีสินค้าแล้ว")
                break

            print(f"   ↳ หน้า {page} พบ {len(products)} สินค้า")
            for prod in products:
                handle = prod.get("handle")
                if handle:
                    link = f"https://compasia.co.th/products/{handle}"
                    product_links.append(link)
                    all_products.append(prod)

        except Exception as e:
            print(f"❌ หน้า {page} เกิดข้อผิดพลาด: {e}")

    # บันทึกเป็น TXT & JSON
    txt_path = LINKS_DIR / "compasia_product_links.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(product_links))

    json_path = LINKS_DIR / "compasia_products_links.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print("\n✅ ดึงลิงก์สำเร็จทั้งหมด:")
    print(f"📦 รวมสินค้า: {len(all_products)} รายการ")
    print(f"📄 บันทึกไฟล์ TXT:  {txt_path}")
    print(f"📄 บันทึกไฟล์ JSON: {json_path}")
    return all_products
