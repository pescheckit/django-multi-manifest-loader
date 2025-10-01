"""Pytest configuration and fixtures for django-multi-manifest-loader tests."""

from pathlib import Path

import django


def pytest_configure():
    """Configure Django settings for tests."""
    from django.conf import settings

    # Minimal Django settings for testing
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-secret-key-for-django-multi-manifest-loader",
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "django.contrib.staticfiles",
            "django_multi_manifest_loader",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        STATIC_URL="/static/",
        STATICFILES_DIRS=[
            Path(__file__).parent / "static",
        ],
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [],
                "APP_DIRS": True,
                "OPTIONS": {
                    "context_processors": [
                        "django.template.context_processors.debug",
                        "django.template.context_processors.request",
                    ],
                },
            }
        ],
    )
    django.setup()
