import urllib.request
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LINKS_DIR = BASE_DIR / "data" / "links"
LINKS_DIR.mkdir(parents=True, exist_ok=True)

def fetch_compasia_links(pages=[1, 2]):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    all_products = []
    product_links = []

    print("=" * 60)
    print("🚀 กำลังดึงลิงก์สินค้าจาก CompAsia (Shopify API)...")
    print("=" * 60)

    for page in pages:
        api_url = f"https://compasia.co.th/collections/all-smartphones/products.json?page={page}&limit=50"
        print(f"⏳ กำลังดึงหน้า {page}...")
        
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
            
            products = data.get("products", [])
            print(f"   ↳ หน้า {page} พบ {len(products)} สินค้า")

            for p in products:
                handle = p.get("handle")
                title = p.get("title")
                prod_url = f"https://compasia.co.th/collections/all-smartphones/products/{handle}"
                
                # ดึงราคาเริ่มต้น
                variants = p.get("variants", [])
                min_price = variants[0].get("price") if variants else None

                all_products.append({
                    "id": p.get("id"),
                    "title": title,
                    "handle": handle,
                    "url": prod_url,
                    "price": min_price,
                    "variants_count": len(variants),
                    "images_count": len(p.get("images", []))
                })
                product_links.append(prod_url)

        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดหน้า {page}: {e}")

    # 1. บันทึกเฉพาะลิงก์เป็นไฟล์ .txt
    txt_file = LINKS_DIR / "compasia_product_links.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        for link in product_links:
            f.write(link + "\n")

    # 2. บันทึก JSON รายละเอียด
    json_file = LINKS_DIR / "compasia_products_links.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"🎉 ดึงลิงก์สำเร็จทั้งหมด: {len(product_links)} ลิงก์!")
    print(f"📄 บันทึกไฟล์ข้อความ (.txt): {txt_file}")
    print(f"📄 บันทึกไฟล์ JSON:          {json_file}")
    print("=" * 60)

    return all_products

if __name__ == "__main__":
    fetch_compasia_links(pages=[1, 2])
