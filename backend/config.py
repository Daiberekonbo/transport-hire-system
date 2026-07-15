import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent.parent

# Prefer an explicit SECRET_KEY, fall back to the platform-managed SESSION_SECRET,
# and only as a last resort generate a random key for the life of this process
# (this avoids a hardcoded, checked-in fallback that would compromise session
# security if the app were ever deployed without an env var configured).
_SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET") or secrets.token_hex(32)


class Config:
    SECRET_KEY = _SECRET_KEY
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'thms.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    DEBUG = False
    TESTING = False

    WTF_CSRF_ENABLED = True
    PERMANENT_SESSION_LIFETIME = 3600 * 8  # 8 hours

    UPLOAD_FOLDER = BASE_DIR / "backend" / "static" / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    APP_NAME = "THMS"
    APP_FULL_NAME = "Transport Hire Management System"
    CURRENCY_SYMBOL = "₦"


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    WTF_CSRF_ENABLED = True


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
