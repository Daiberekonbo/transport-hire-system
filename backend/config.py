import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "thms-dev-secret-change-in-production-2024")
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
