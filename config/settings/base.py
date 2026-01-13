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

# Supabase Configuration (PostgreSQL Database)
SUPABASE_URL = os.getenv('SUPABASE_URL', '')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY', '')
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL', '')  # Direct PostgreSQL connection string

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
    "apps.mentorship",
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

# Database Configuration - Use Supabase PostgreSQL exclusively
# Priority: SUPABASE_DB_URL > DATABASE_URL (for backward compatibility)
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
DATABASE_URL = SUPABASE_DB_URL or os.getenv("DATABASE_URL")

RUNNING_TESTS = (
    "PYTEST_CURRENT_TEST" in os.environ
    or any("pytest" in arg or "py.test" in arg for arg in sys.argv)
    or any(arg.startswith("test") for arg in sys.argv)
)

if DATABASE_URL and not RUNNING_TESTS:
    # Parse database URL and configure connection
    db_config = dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    
    # Force SSL for Supabase connections
    if 'supabase' in DATABASE_URL.lower():
        db_config['OPTIONS'] = db_config.get('OPTIONS', {})
        db_config['OPTIONS']['sslmode'] = 'require'
    
    DATABASES = {"default": db_config}
else:
    # Use SQLite only for tests (faster, no network)
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

# Supabase Storage Configuration
# All media files are stored in Supabase Storage buckets
MEDIA_URL = f"{os.getenv('SUPABASE_URL', 'https://adnteftmqytcnieqmlma.supabase.co')}/storage/v1/object/public/"
MEDIA_ROOT = BASE_DIR / "media"  # Fallback for local development only

# Supabase Storage Buckets
SUPABASE_STORAGE_BUCKETS = {
    'event_flyers': 'event-flyers',  # Event flyers
    'event_photos': 'event-photos',  # Event photos/images
    'project_images': 'project-images',  # Project images
    'profiles': 'profiles',  # User profile pictures
    'events': 'events',  # General events bucket
    'projects': 'projects',  # General projects bucket
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CORS configuration - Allow both local development and production origins
CORS_ALLOWED_ORIGINS_ENV = os.getenv("CORS_ALLOWED_ORIGINS", "")
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:4000",  # admin dashboard
    "http://127.0.0.1:4000",  # admin dashboard
    "https://mansa-dashboard.vercel.app",  # production dashboard
    "https://mansa-dashboard-a20uzzd3j-wuniabdulai19-4405s-projects.vercel.app",  # dashboard preview
    "https://mansa-to-mansa.vercel.app",  # production website
    "https://mansatomansa.vercel.app",  # alternative production website
    "https://mansa-website-dusky.vercel.app",  # current production deployment
    "https://www.mansa-to-mansa.org",  # production domain
    "https://mansa-to-mansa.org",  # production domain (without www)
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

# Celery Configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True

# Celery Beat Schedule for periodic tasks
CELERY_BEAT_SCHEDULE = {
    'send-session-reminders-24h': {
        'task': 'apps.mentorship.tasks.send_session_reminder_24h',
        'schedule': 86400.0,  # Run daily (24 hours in seconds)
    },
}

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
