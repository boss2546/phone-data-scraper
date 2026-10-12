from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
JSON_DIR = DATA_DIR / "json"

for d in [DATA_DIR, EXPORTS_DIR, JSON_DIR]:
    d.mkdir(parents=True, exist_ok=True)
