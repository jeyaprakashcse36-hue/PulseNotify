from pathlib import Path
from dotenv import load_dotenv

# Load environment variables before importing base settings.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

from .base import *

SECRET_KEY = os.getenv("SECRET_KEY", SECRET_KEY)
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

DATABASES["default"]["PASSWORD"] = os.getenv(
    "POSTGRES_PASSWORD", ""
)