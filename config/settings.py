"""
Django settings for config project.

Firestore stores application data; Django SQLite is only retained for
framework-managed tables during local development.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env.local")
load_dotenv(BASE_DIR / ".env")

def _get_debug():
    if os.environ.get("VERCEL") == "1":
        return False
    return os.environ.get("DJANGO_DEBUG", "true").lower() in {
        "1",
        "true",
        "yes",
    }


def _vercel_hostnames():
    return [
        hostname
        for name in (
            "VERCEL_URL",
            "VERCEL_BRANCH_URL",
            "VERCEL_PROJECT_PRODUCTION_URL",
        )
        if (hostname := os.environ.get(name, "").strip())
    ]


def _get_allowed_hosts(debug):
    default_hosts = "localhost,127.0.0.1,[::1]" if debug else ""
    hosts = [
        host.strip()
        for host in os.environ.get(
            "DJANGO_ALLOWED_HOSTS",
            default_hosts,
        ).split(",")
        if host.strip()
    ]
    return list(dict.fromkeys([*hosts, *_vercel_hostnames()]))


def _get_csrf_trusted_origins():
    origins = [
        origin.strip()
        for origin in os.environ.get(
            "DJANGO_CSRF_TRUSTED_ORIGINS",
            "",
        ).split(",")
        if origin.strip()
    ]
    vercel_origins = [f"https://{hostname}" for hostname in _vercel_hostnames()]
    return list(dict.fromkeys([*origins, *vercel_origins]))


DEBUG = _get_debug()

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-only",
)
ALLOWED_HOSTS = _get_allowed_hosts(DEBUG)

if not DEBUG and not os.environ.get("DJANGO_SECRET_KEY"):
    raise ImproperlyConfigured(
        "DJANGO_SECRET_KEY must be set when DEBUG is disabled."
    )
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS must be set when DEBUG is disabled."
    )
if not DEBUG and not os.environ.get("FIREBASE_PROJECT_ID"):
    raise ImproperlyConfigured(
        "FIREBASE_PROJECT_ID must be set when DEBUG is disabled."
    )
if not DEBUG and not os.environ.get("FIREBASE_API_KEY"):
    raise ImproperlyConfigured(
        "FIREBASE_API_KEY must be set when DEBUG is disabled."
    )
if not DEBUG and not os.environ.get("FIREBASE_SERVICE_ACCOUNT_BASE64"):
    raise ImproperlyConfigured(
        "FIREBASE_SERVICE_ACCOUNT_BASE64 must be set when DEBUG is disabled."
    )

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "users",
    "courses",
    "monitoring",
    "tickets",
    "web",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "firebase_backend.middleware.FirebaseSessionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.environ.get("DJANGO_SQLITE_PATH", BASE_DIR / "db.sqlite3"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

CSRF_TRUSTED_ORIGINS = _get_csrf_trusted_origins()

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = int(
    os.environ.get("DJANGO_HSTS_SECONDS", "0" if DEBUG else "31536000")
)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
