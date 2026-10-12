from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECTS_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
EXPORTS_DIR = DATA_DIR / "exports"
REPORTS_DIR = DATA_DIR / "reports"

for d in [DATA_DIR, EXPORTS_DIR, REPORTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)
