from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
WEATHER_DIR = DATA_DIR / "weather"
EXPORTS_DIR = DATA_DIR / "exports"

for d in [DATA_DIR, WEATHER_DIR, EXPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "th,en;q=0.9"
}

BMA_NONGKHAM_URL = "https://weather.bangkok.go.th/Radar/RadarAnimationNk.aspx"
BMA_NONGCHOK_URL = "https://weather.bangkok.go.th/Radar/RadarAnimationNc.aspx"
