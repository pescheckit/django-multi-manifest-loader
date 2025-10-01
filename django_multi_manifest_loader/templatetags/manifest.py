"""
Manifest template tag for loading webpack assets with cache busting.

Automatically discovers and merges manifest.json files from all Django apps.
"""

import json
import logging

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.templatetags.static import static

logger = logging.getLogger(__name__)
register = template.Library()


class ManifestLoader:
    """Loads and caches merged manifests from all Django apps."""

    _cache = None

    @classmethod
    def _get_config(cls):
        """Get configuration from Django settings."""
        return getattr(settings, "DJANGO_MULTI_MANIFEST_LOADER", {})

    @classmethod
    def get_manifest(cls):
        """Load and merge all manifest.json files."""
        config = cls._get_config()
        cache_enabled = config.get("cache", not settings.DEBUG)
        debug = config.get("debug", False)

        # Return cached manifest if available and caching is enabled
        if cache_enabled and cls._cache is not None:
            return cls._cache

        merged = {}
        all_manifests = []

        # Method 1: Find main manifest.json
        manifest_files = finders.find("manifest.json", all=True) or []
        if isinstance(manifest_files, str):
            all_manifests.append(manifest_files)
        else:
            all_manifests.extend(manifest_files)

        # Method 2: Search for package-specific manifests by checking each INSTALLED_APP
        # This is more reliable than using wildcards
        from django.apps import apps

        for app_config in apps.get_app_configs():
            # Try to find manifest.json in the app's static directory
            app_manifest_path = f"{app_config.name}/manifest.json"
            found = finders.find(app_manifest_path, all=True)
            if found:
                if isinstance(found, str):
                    all_manifests.append(found)
                else:
                    all_manifests.extend(found)

        # Load and merge all manifests
        if debug:
            logger.info(f"[django-multi-manifest-loader] Found {len(all_manifests)} manifest files")

        for manifest_path in all_manifests:
            try:
                if debug:
                    logger.info(
                        f"[django-multi-manifest-loader] Loading manifest from: {manifest_path}"
                    )
                with open(manifest_path) as f:
                    data = json.load(f)
                    if debug:
                        logger.info(
                            f"[django-multi-manifest-loader] Loaded {len(data)} entries from {manifest_path}"
                        )
                    merged.update(data)
            except Exception as e:
                logger.warning(
                    f"[django-multi-manifest-loader] Failed to load manifest from {manifest_path}: {e}"
                )

        if debug:
            logger.info(
                f"[django-multi-manifest-loader] Total merged manifest entries: {len(merged)}"
            )

        # Cache if enabled
        if cache_enabled:
            cls._cache = merged

        return merged

    @classmethod
    def clear_cache(cls):
        """Clear the manifest cache. Useful for development."""
        cls._cache = None


@register.simple_tag
def manifest(asset_key):
    """
    Template tag to get the hashed asset URL from the manifest.

    Usage:
        {% load manifest %}
        <script src="{% manifest 'main.js' %}"></script>

    Args:
        asset_key: The key in the manifest (e.g., 'main.js')

    Returns:
        The full static URL with hash (e.g., '/static/main.abc123.js')
        Falls back to static tag if key not found in manifest.
    """
    manifest_data = ManifestLoader.get_manifest()

    # Get the hashed filename from manifest
    hashed_filename = manifest_data.get(asset_key, asset_key)

    # If the hashed_filename already starts with http or /, return it as is
    if hashed_filename.startswith(("http://", "https://", "/")):
        return hashed_filename

    # Otherwise use Django's static helper
    return static(hashed_filename)


@register.simple_tag
def manifest_raw(asset_key):
    """
    Get the raw manifest value without the static URL processing.

    Usage:
        {% manifest_raw 'main.js' %}

    Returns:
        The manifest value (e.g., 'static/main.abc123.js')
    """
    manifest_data = ManifestLoader.get_manifest()
    return manifest_data.get(asset_key, asset_key)
