import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

PUBLIC_IP_OF_WEB01 = os.environ.get("WEB01_PUBLIC_IP")
PUBLIC_IP_OF_WEB02 = os.environ.get("WEB02_PUBLIC_IP")
PRIVATE_IP_OF_WEB01 = os.environ.get("WEB01_PRIVATE_IP")
PRIVATE_IP_OF_WEB02 = os.environ.get("WEB02_PRIVATE_IP")
ALLOWED_HOSTS = [PRIVATE_IP_OF_WEB01, PUBLIC_IP_OF_WEB01, PRIVATE_IP_OF_WEB02, PUBLIC_IP_OF_WEB02, "localhost", "127.0.0.1"]

INSTALLED_APPS = [
    "daphne",
    "channels",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "storages",
    "accounts",
    "myapp",
    "vendor",
    "customer",
    "menu",
    "marketplace",
    "order",
    "admins",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mysite.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "vendor.context_processors.getGoogleApi",
                "vendor.context_processors.getVendor",
                "marketplace.context_processor.get_cart_counter",
                "marketplace.context_processor.cart_amount",
            ],
        },
    },
]
ASGI_APPLICATION = "mysite.asgi.application"
WSGI_APPLICATION = "mysite.wsgi.application"
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT"),
    }
}
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

GDAL_DATA = os.environ.get("GDAL_DATA")
STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles/"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 86400


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS") == "True"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                (
                    os.environ.get("REDIS_HOST", "redis"),
                    int(os.environ.get("REDIS_PORT", 6379)),
                )
            ],
        },
    },
}
INSTALLED_APPS += ["django_celery_results"]

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")

CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kathmandu"
CELERY_ENABLE_UTC = True

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
ESEWA_SUCCESS_URL = os.environ.get("ESEWA_SUCCESS_URL")
ESEWA_FAILURE_URL = os.environ.get("FAILURE_URL")

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_REGION_NAME = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
AWS_DEFAULT_ACL = None  # private by default
AWS_QUERYSTRING_AUTH = True  # signed URLs
AWS_S3_FILE_OVERWRITE = False

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "mysite.storage.NonStrictManifestStaticFilesStorage",
    },
}

