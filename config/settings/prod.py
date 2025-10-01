import os  # noqa: E402

from .base import *  # noqa

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Sentry integration
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    import logging

    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    def _level(val: str, default: str) -> int | None:  # helper to coerce string level names
        v = os.getenv(val, default)
        if v.isdigit():
            return int(v)
        return getattr(logging, v.upper(), logging.INFO)

    sentry_logging = LoggingIntegration(
        level=_level("SENTRY_LOG_LEVEL", "INFO"),  # Capture breadcrumbs
        event_level=_level("SENTRY_EVENT_LEVEL", "ERROR"),  # Events
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), sentry_logging],
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0")),
        send_default_pii=True,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        release=os.getenv("GIT_COMMIT", ""),
    )
