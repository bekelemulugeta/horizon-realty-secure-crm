import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER', 'root')}:"
        f"{os.getenv('DB_PASSWORD', '')}"
        f"@{os.getenv('DB_HOST', '127.0.0.1')}:{os.getenv('DB_PORT', 3306)}"
        f"/{os.getenv('DB_NAME', 'realestate_crm')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")

    # VULN-BASELINE: debug mode left on -> verbose stack traces to any visitor.
    # Fix in hardened branch: DEBUG = False, proper error pages.
    DEBUG = True
