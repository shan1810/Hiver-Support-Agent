import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

RAW_CSV = Path(os.getenv("TWCS_CSV", ROOT / "data" / "raw" / "twcs.csv"))
PROCESSED = ROOT / "data" / "processed"
GOLDEN = ROOT / "data" / "golden"
RESULTS = ROOT / "results"
CACHE = ROOT / "cache"

BRAND = os.getenv("BRAND", "SpotifyCares")
AGENT_MODEL = os.getenv("AGENT_MODEL", "gemini-3.5-flash-lite")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-3.1-flash-lite")
SEED = 13
