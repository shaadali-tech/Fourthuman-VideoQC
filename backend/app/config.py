from pathlib import Path
import os

BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = Path(os.getenv("VIDEOQC_DATA_DIR", BACKEND_DIR / "data"))
UPLOAD_DIR = Path(os.getenv("VIDEOQC_UPLOAD_DIR", DATA_DIR / "uploads"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(DATA_DIR / 'videoqc.db').as_posix()}")

MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "500"))
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}

# Initial demo thresholds. Tune these to the company's actual QC specification.
MIN_DURATION_SECONDS = float(os.getenv("MIN_DURATION_SECONDS", "1"))
MAX_DURATION_SECONDS = float(os.getenv("MAX_DURATION_SECONDS", "300"))
MIN_WIDTH = int(os.getenv("MIN_WIDTH", "640"))
MIN_HEIGHT = int(os.getenv("MIN_HEIGHT", "360"))
MIN_FPS = float(os.getenv("MIN_FPS", "15"))
MAX_FPS = float(os.getenv("MAX_FPS", "60"))
MIN_BLUR_SCORE = float(os.getenv("MIN_BLUR_SCORE", "50"))
BLACK_FRAME_THRESHOLD = int(os.getenv("BLACK_FRAME_THRESHOLD", "20"))
