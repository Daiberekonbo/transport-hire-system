import os
import secrets
import sys
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()
BASE_DIR = Path(__file__).parent.parent

# Prefer an explicit SECRET_KEY, fall back to the platform-managed SESSION_SECRET,
# and only as a last resort generate a random key for the life of this process
# (this avoids a hardcoded, checked-in fallback that would compromise session
# security if the app were ever deployed without an env var configured).
_SECRET_KEY = os.getenv("SECRET_KEY") or os.getenv("SESSION_SECRET") or secrets.token_hex(32)


def _normalize_database_url(url: str) -> str:
    """Normalize DATABASE_URL for SQLAlchemy compatibility."""
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


def _compose_postgres_uri() -> str | None:
    host = os.getenv("POSTGRES_HOST") or os.getenv("DB_HOST")
    dbname = os.getenv("POSTGRES_DB") or os.getenv("DB_NAME")
    user = os.getenv("POSTGRES_USER") or os.getenv("DB_USER")
    password = os.getenv("POSTGRES_PASSWORD") or os.getenv("DB_PASSWORD")
    port = os.getenv("POSTGRES_PORT") or os.getenv("DB_PORT") or "5432"
    sslmode = os.getenv("POSTGRES_SSL_MODE") or os.getenv("DB_SSLMODE") or os.getenv("DB_SSL_MODE")

    if not (host and dbname and user and password):
        return None

    user = quote_plus(user)
    password = quote_plus(password)
    uri = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    if sslmode:
        uri += f"?sslmode={sslmode}"
    return uri


def _get_database_uri() -> str:
    env_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    if env_url:
        return _normalize_database_url(env_url)

    postgres_url = _compose_postgres_uri()
    if postgres_url:
        return postgres_url

    flask_env = os.getenv("FLASK_ENV", "").lower()
    if flask_env in ("production", "prod") or getattr(sys, "frozen", False):
        raise RuntimeError(
            "THMS production requires a PostgreSQL connection. "
            "Set DATABASE_URL or POSTGRES_HOST/POSTGRES_DB/POSTGRES_USER/POSTGRES_PASSWORD "
            "in the environment before launching the app."
        )

    sqlite_path = BASE_DIR / "thms.db"
    return f"sqlite:///{sqlite_path.as_posix()}"


class Config:
    SECRET_KEY = _SECRET_KEY
    SQLALCHEMY_DATABASE_URI = _get_database_uri()
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
