from .base import *

DEBUG = False
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")

if not os.getenv("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY must be configured in production.")

if not os.getenv("POSTGRES_PASSWORD"):
    raise RuntimeError("POSTGRES_PASSWORD must be configured in production.")

if not os.getenv("DJANGO_ALLOWED_HOSTS"):
    raise RuntimeError("DJANGO_ALLOWED_HOSTS must be configured in production.")

if not os.getenv("DB_HOST"):
    raise RuntimeError("DB_HOST must be configured in production.")

if not os.getenv("DB_PORT"):
    raise RuntimeError("DB_PORT must be configured in production.")

if not os.getenv("CELERY_BROKER_URL"):
    raise RuntimeError("CELERY_BROKER_URL must be configured in production.")

if not os.getenv("CELERY_RESULT_BACKEND"):
    raise RuntimeError("CELERY_RESULT_BACKEND must be configured in production.")

if not os.getenv("POSTGRES_DB") or not os.getenv("POSTGRES_USER"):
    raise RuntimeError("Database name and user must be configured in production.")

if not os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS"):
    raise RuntimeError("DJANGO_CSRF_TRUSTED_ORIGINS must be configured in production.")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", ""
).split(",")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True