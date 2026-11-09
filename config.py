
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is missing. Please configure it in your .env file."
        )

    # Production: PostgreSQL
    # Local development: SQLite
    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://", "postgresql+psycopg://", 1
            )
        elif DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = (
            f"sqlite:///{(BASE_DIR / 'database' / 'edusmart.db').as_posix()}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = MAIL_USERNAME
