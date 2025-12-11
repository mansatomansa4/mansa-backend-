import os
import sys
from datetime import timedelta
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "false").lower() == "true"

ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "corsheaders",
    "apps.core",
    "apps.users",
    "apps.platform",
    "apps.projects",
    "apps.emails",
    "apps.events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL")
# Treat obvious placeholder values as unset so local dev doesn't try to resolve an invalid host
PLACEHOLDER_DB_HOST_TOKENS = {"HOST", "YOUR_HOST", "CHANGE_ME"}
VALID_DB_SCHEMES = {
    "postgres", "postgresql", "cockroach", "mysql", "sqlite",
    "oracle", "mssql", "redshift", "timescale"
}


def _is_placeholder_db(url: str | None) -> bool:
    if not url:
        return True

    # Check if URL starts with invalid scheme (like https://)
    try:
        scheme = url.split("://", 1)[0].lower() if "://" in url else ""
        if scheme and scheme not in VALID_DB_SCHEMES:
            import sys
            print(
                f"WARNING: DATABASE_URL has invalid scheme '{scheme}://'. "
                f"Expected one of: {', '.join(VALID_DB_SCHEMES)}. "
                f"Falling back to SQLite.",
                file=sys.stderr
            )
            return True
    except Exception:  # pragma: no cover - defensive
        pass

    # crude parse: look for '@HOST:' pattern or missing real host
    try:
        at_split = url.split("@", 1)
        if len(at_split) == 2:
            host_part = at_split[1]
            # host_part like HOST:5432/dbname
            host = host_part.split(":", 1)[0]
            if host in PLACEHOLDER_DB_HOST_TOKENS:
                return True
    except Exception:  # pragma: no cover - defensive
        return False
    return False


if _is_placeholder_db(DATABASE_URL):
    DATABASE_URL = None
RUNNING_TESTS = (
    "PYTEST_CURRENT_TEST" in os.environ
    or any("pytest" in arg or "py.test" in arg for arg in sys.argv)
    or any(arg.startswith("test") for arg in sys.argv)
)
FORCE_DB_URL_IN_TESTS = os.getenv("USE_DB_URL_IN_TESTS", "false").lower() in {"1", "true", "yes"}

if DATABASE_URL and (not RUNNING_TESTS or (RUNNING_TESTS and FORCE_DB_URL_IN_TESTS)):
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=False)
    }
else:
    # Always fallback to sqlite for tests (faster, no network) unless opt-in
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(BASE_DIR / "db.sqlite3"),
        }
    }

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("THROTTLE_RATE_ANON", "50/min"),
        "user": os.getenv("THROTTLE_RATE_USER", "200/min"),
    },
}

SIMPLE_JWT = {
    # Extended to match documentation (1 hour access) while keeping refresh window
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "7"))),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS configuration - Allow both local development and production origins
CORS_ALLOWED_ORIGINS_ENV = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4000",  # admin dashboard
    "http://127.0.0.1:4000",  # admin dashboard
    "https://mansa-dashboard.vercel.app",  # production dashboard
    "https://mansa-to-mansa.vercel.app",  # production website
    "https://mansatomansa.vercel.app",  # alternative production website
    "https://mansa-website-dusky.vercel.app",  # current production deployment
]

# Add production origins from environment variable (comma-separated)
if CORS_ALLOWED_ORIGINS_ENV:
    CORS_ALLOWED_ORIGINS.extend([origin.strip() for origin in CORS_ALLOWED_ORIGINS_ENV.split(",") if origin.strip()])

# Allow all Vercel preview deployments
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

CORS_ALLOW_CREDENTIALS = True

# Email defaults (override via environment in production)
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Mansa <noreply@example.com>")

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://adnteftmqytcnieqmlma.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Security related headers (activated more strictly in production settings)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # allow CSRF token read by client JS only if necessary
X_FRAME_OPTIONS = "DENY"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
        "json": {
            "format": (
                '{{"level": "{levelname}", "time": "{asctime}", "name": '
                '"{name}", "message": "{message}"}}'
            ),
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# drf-spectacular OpenAPI configuration
SPECTACULAR_SETTINGS = {
    "TITLE": "Mansa API",
    "DESCRIPTION": (
        "API for Mansa platform including user accounts, platform data "
        "(Supabase), and project applications."
    ),
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api",
    "CONTACT": {
        "name": "Mansa Support",
        "email": "support@example.com",
    },
    "LICENSE": {
        "name": "Proprietary",
    },
}
