from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "reviewer.db"))
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "200000"))
SUPPORTED_EXTENSIONS = {".py": "python", ".js": "javascript", ".ts": "typescript", ".java": "java"}
SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Informational"]
