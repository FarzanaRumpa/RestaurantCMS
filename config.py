import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///restaurant_platform.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    WTF_CSRF_ENABLED = True

    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'SuperAdmin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '123456')
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@system.local')

    QR_CODE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'qrcodes')

    # Base URL for QR codes - update this for production
    BASE_URL = os.getenv('BASE_URL', 'http://127.0.0.1:8000')

    RATELIMIT_DEFAULT = "200 per day"
    RATELIMIT_STORAGE_URL = "memory://"

