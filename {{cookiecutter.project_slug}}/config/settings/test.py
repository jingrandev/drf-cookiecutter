# ruff: noqa: PGH004, F405, F403
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Use a faster password hasher during tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Use in-memory database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Your stuff...
# ------------------------------------------------------------------------------
INSTALLED_APPS = [*INSTALLED_APPS, "core.tests"]  # noqa: F405

SHOW_API_DOCS = True
