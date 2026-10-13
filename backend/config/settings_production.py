"""Production settings for the Hostinger VPS deployment."""

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403
from .settings import _INSECURE_KEY, env

DEBUG = False
ENVIRONMENT = "production"
if SECRET_KEY in {_INSECURE_KEY, "ganti-dengan-secret-acak-yang-panjang", "docker-dev-secret-change-me"} or len(SECRET_KEY) < 50:
    raise ImproperlyConfigured("Set a unique DJANGO_SECRET_KEY of at least 50 characters.")

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CORS_ALLOWED_ORIGINS = env.list("DJANGO_CORS_ORIGINS", default=[])
CORS_ALLOWED_ORIGIN_REGEXES = []
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
STATIC_URL = "/static/"
STATIC_ROOT = Path(env("DJANGO_STATIC_ROOT", default="/app/staticfiles"))
MEDIA_ROOT = Path(env("DJANGO_MEDIA_ROOT", default="/app/media"))

# Only Caddy can reach Gunicorn; Caddy sets this header from its HTTPS listener.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
