import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "change-me-in-production")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "0.0.0.0,127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "scanner_api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}

ROOT_URLCONF = "django_admin.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

LOGIN_URL = "/login/"

WSGI_APPLICATION = "django_admin.wsgi.application"

# ── Database (Supabase PostgreSQL with SQLite fallback) ─────────────────
def _use_supabase():
    url = os.getenv("SUPABASE_DATABASE_URL", "")
    host = os.getenv("SUPABASE_DB_HOST", "")
    pwd = os.getenv("SUPABASE_DB_PASSWORD", "")
    key = os.getenv("SUPABASE_SERVICE_KEY", "")
    if url and "user:password@host" not in url and "xxxxx" not in url:
        return True
    if host and "xxxxx" not in host and pwd and "your-" not in pwd:
        return True
    if key and "service_role_key" not in key:
        return True
    return False

if _use_supabase():
    DATABASE_URL = os.getenv("SUPABASE_DATABASE_URL")
    if DATABASE_URL:
        import re
        match = re.match(r"postgres(?:ql)?://(.+):(.+)@(.+):(\d+)/(.+)", DATABASE_URL)
        if match:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": match.group(5),
                    "USER": match.group(1),
                    "PASSWORD": match.group(2),
                    "HOST": match.group(3),
                    "PORT": match.group(4),
                    "OPTIONS": {"sslmode": "require"},
                }
            }
        else:
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": os.getenv("SUPABASE_DB_NAME", "postgres"),
                    "USER": os.getenv("SUPABASE_DB_USER", "postgres"),
                    "PASSWORD": os.getenv("SUPABASE_DB_PASSWORD", ""),
                    "HOST": os.getenv("SUPABASE_DB_HOST", ""),
                    "PORT": os.getenv("SUPABASE_DB_PORT", "5432"),
                    "OPTIONS": {"sslmode": "require"},
                }
            }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.getenv("SUPABASE_DB_NAME", "postgres"),
                "USER": os.getenv("SUPABASE_DB_USER", "postgres"),
                "PASSWORD": os.getenv("SUPABASE_DB_PASSWORD", ""),
                "HOST": os.getenv("SUPABASE_DB_HOST", ""),
                "PORT": os.getenv("SUPABASE_DB_PORT", "5432"),
                "OPTIONS": {"sslmode": "require"},
            }
        }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "data" / "scanner.db",
        }
    }

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Logging ─────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "[{levelname}] {message}", "style": "{"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

# ── Supabase Client Settings ───────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")
