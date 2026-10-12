from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
COMPASIA_DIR = DATA_DIR / "compasia"
IMAGES_DIR = DATA_DIR / "images"
EXPORTS_DIR = DATA_DIR / "exports"
LINKS_DIR = DATA_DIR / "links"

# Create directories
for d in [DATA_DIR, COMPASIA_DIR, IMAGES_DIR, EXPORTS_DIR, LINKS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html",
    "Accept-Language": "th,en;q=0.9"
}

BASE_API_URL = "https://compasia.co.th/collections/all-smartphones/products.json"
