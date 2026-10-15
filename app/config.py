import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class Config:
    """Professional Configuration for Student Portal"""
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "dev-fallback-key-replace-in-production")
    DEFAULT_SEMESTER: str = os.environ.get("DEFAULT_SEMESTER", "Fall 2026")
    DEFAULT_CREDITS: int = int(os.environ.get("DEFAULT_CREDITS", 3))
    DB_PATH: str = os.environ.get("DB_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "database", "portal.db"))
    SESSION_TYPE: str = os.environ.get("SESSION_TYPE", "filesystem")

    # Production Hardening Settings
    SESSION_COOKIE_SECURE: bool = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() == "true"
    SESSION_COOKIE_HTTPONLY: bool = True
    PERMANENT_SESSION_LIFETIME: int = int(os.environ.get("SESSION_LIFETIME", 3600)) # 1 hour
    SESSION_PERMANENT: bool = True
    WTF_CSRF_ENABLED: bool = True
    SESSION_COOKIE_SAMESITE: str = 'Lax'
