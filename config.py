import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "secret_dev_key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))

# Database Configuration
DB_ENGINE = os.getenv("DB_ENGINE", "postgresql")
DB_NAME = os.getenv("DB_NAME", "refdata")
DB_SCHEMA = os.getenv("DB_SCHEMA", "fastapi_auth")
DB_USER = os.getenv("DB_USER", "chatpaat_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

# Construct DATABASE_URL from individual components with URL encoding for special characters
DATABASE_URL = f"{DB_ENGINE}://{quote(DB_USER, safe='')}:{quote(DB_PASSWORD, safe='')}@{DB_HOST}:{DB_PORT}/{DB_NAME}?options=-c%20search_path={DB_SCHEMA}"

EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_APP_PASS")
