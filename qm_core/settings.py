import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [x.strip() for x in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if x.strip()]
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if x.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "oauth2_provider",
    "rest_framework",
    "users",
    "organizations",
    "entitlements",
    "audit",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "users.middleware.ActiveQMAccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "qm_core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

WSGI_APPLICATION = "qm_core.wsgi.application"

if os.getenv("QM_DATABASE_ENGINE") == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "qm_core"),
            "USER": os.getenv("POSTGRES_USER", "qm_core"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", ""),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"
AUTHENTICATION_BACKENDS = ["users.auth.QMModelBackend"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/api/v1/auth/me/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
PASSWORD_RESET_TIMEOUT = int(os.getenv("PASSWORD_RESET_TIMEOUT", "86400"))
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "QM Identity <noreply@qmanufacture.com>")
QM_ACCOUNT_PUBLIC_ORIGIN = os.getenv("QM_ACCOUNT_PUBLIC_ORIGIN", "http://localhost:8000").rstrip("/")
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
EMAIL_FILE_PATH = os.getenv("EMAIL_FILE_PATH", str(BASE_DIR / "mail"))


def _env_bool(name, default=False):
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


SESSION_COOKIE_NAME = "qm_identity_session"
CSRF_COOKIE_NAME = "qm_identity_csrf"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = _env_bool("QM_SECURE_COOKIES", False)
CSRF_COOKIE_SECURE = _env_bool("QM_SECURE_COOKIES", False)
SECURE_SSL_REDIRECT = _env_bool("QM_SECURE_SSL_REDIRECT", False)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"


def _multiline_env(name):
    value = os.getenv(name, "")
    return value.replace("\\n", "\n").strip()


def _oidc_private_key():
    key_file = os.getenv("QM_OIDC_RSA_PRIVATE_KEY_FILE", "").strip()
    if key_file:
        return Path(key_file).read_text(encoding="utf-8").strip()
    return _multiline_env("QM_OIDC_RSA_PRIVATE_KEY")


def _oidc_inactive_private_keys():
    files = [
        value.strip()
        for value in os.getenv("QM_OIDC_RSA_PRIVATE_KEYS_INACTIVE_FILES", "").split(",")
        if value.strip()
    ]
    return [
        Path(key_file).read_text(encoding="utf-8").strip()
        for key_file in files
    ]


OIDC_RSA_PRIVATE_KEY = _oidc_private_key()
OIDC_RSA_PRIVATE_KEYS_INACTIVE = _oidc_inactive_private_keys()
OIDC_ISSUER = os.getenv("QM_OIDC_ISSUER", "").rstrip("/")

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": bool(OIDC_RSA_PRIVATE_KEY),
    "OIDC_RSA_PRIVATE_KEY": OIDC_RSA_PRIVATE_KEY,
    "OIDC_RSA_PRIVATE_KEYS_INACTIVE": OIDC_RSA_PRIVATE_KEYS_INACTIVE,
    "OIDC_ISS_ENDPOINT": OIDC_ISSUER,
    "OIDC_RP_INITIATED_LOGOUT_ENABLED": True,
    "OAUTH2_VALIDATOR_CLASS": "users.oauth_validators.QMOAuth2Validator",
    "SCOPES": {
        "openid": "OpenID Connect identity",
        "profile": "Basic user profile",
        "email": "User email address",
        "qm.access": "Read current QM organization and product access context",
        "qm.provision": "Create or resend central QM account invitations",
    },
    "DEFAULT_SCOPES": ["openid", "profile", "email"],
    "PKCE_REQUIRED": True,
    "COMPLIANT_BCP_RFC9700_PKCE_METHOD": True,
    "COMPLIANT_BCP_RFC9700_ACCESS_TOKEN_TRANSPORT": True,
    "COMPLIANT_BCP_RFC9700_AUTHZ_RESPONSE_ISS": True,
    "COMPLIANT_BCP_RFC9700_REDIRECT_URI_MATCHING": True,
    "COMPLIANT_BCP_RFC9700_PKCE_REQUIRED": True,
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "oauth2_provider.contrib.rest_framework.OAuth2Authentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "api.permissions.IsActiveQMUser",
    ],
}
