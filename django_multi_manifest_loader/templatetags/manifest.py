"""
Manifest template tag for loading webpack assets with cache busting.

Automatically discovers and merges manifest.json files from all Django apps.
"""

import json
import logging

from django import template
from django.apps import apps
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
        """
        Load and namespace all manifest.json files by app.

        Returns a dict like:
        {
            'dashboard': {'main.js': 'js/main.xxx.js'},  # Main app
            'vogcheck': {'config.js': 'vogcheck/js/config.xxx.js'},
            'id2check': {'config.js': 'id2check/js/config.yyy.js'}
        }
        """
        config = cls._get_config()
        cache_enabled = config.get("cache", not settings.DEBUG)
        debug = config.get("debug", False)
        main_app_name = config.get("main_app_name", "main")  # Default to 'main'

        # Return cached manifest if available and caching is enabled
        if cache_enabled and cls._cache is not None:
            return cls._cache

        manifests = {}
        app_manifest_map = {}  # Maps manifest path -> app name

        # Method 1: Find main manifest.json (not tied to specific apps)
        manifest_files = finders.find("manifest.json", all=True) or []
        main_manifests = []
        if isinstance(manifest_files, str):
            main_manifests.append(manifest_files)
        else:
            main_manifests.extend(manifest_files)

        # Method 2: Search for package-specific manifests by checking each INSTALLED_APP

        for app_config in apps.get_app_configs():
            # Try to find manifest.json in the app's static directory
            app_manifest_path = f"{app_config.name}/manifest.json"
            found = finders.find(app_manifest_path, all=True)
            if found:
                if isinstance(found, str):
                    app_manifest_map[found] = app_config.name
                else:
                    # It's a list - map all paths to this app
                    for path in found:
                        app_manifest_map[path] = app_config.name

        # Combine all manifests
        all_manifests = list(set(main_manifests + list(app_manifest_map.keys())))

        # Load all manifests
        if debug:
            logger.info(f"[django-multi-manifest-loader] Found {len(all_manifests)} manifest files")

        for manifest_path in all_manifests:
            try:
                # Determine app name: from map or default to main_app_name
                app_name = app_manifest_map.get(manifest_path, main_app_name)

                if debug:
                    logger.info(
                        f"[django-multi-manifest-loader] Loading manifest from: {manifest_path} (app: {app_name})"
                    )

                with open(manifest_path) as f:
                    data = json.load(f)
                    if debug:
                        logger.info(f"[django-multi-manifest-loader] Loaded {len(data)} entries")

                    # Store/merge by app name
                    if app_name in manifests:
                        manifests[app_name].update(data)
                    else:
                        manifests[app_name] = data
            except Exception as e:
                logger.warning(
                    f"[django-multi-manifest-loader] Failed to load manifest from {manifest_path}: {e}"
                )

        if debug:
            logger.info(
                f"[django-multi-manifest-loader] Loaded manifests for {len(manifests)} apps: {list(manifests.keys())}"
            )

        # Cache if enabled
        if cache_enabled:
            cls._cache = manifests

        return manifests

    @classmethod
    def clear_cache(cls):
        """Clear the manifest cache. Useful for development."""
        cls._cache = None


def _detect_app_from_context(context):
    """
    Detect the current app from template context.

    Extracts app name from Django template name (e.g., 'vogcheck/form.html' -> 'vogcheck').
    Returns None if detection fails.
    """
    try:
        if hasattr(context, "template") and hasattr(context.template, "origin"):
            template_name = context.template.origin.template_name
            if template_name and "/" in template_name:
                # Django convention: "app_name/template.html"
                return template_name.split("/")[0]
    except Exception:
        pass
    return None


@register.simple_tag(takes_context=True)
def manifest(context, asset_key, app=None):
    """
    Template tag to get the hashed asset URL from the manifest.

    Usage:
        {% load manifest %}
        <script src="{% manifest 'main.js' %}"></script>
        <script src="{% manifest 'config.js' app='vogcheck' %}"></script>

    Args:
        context: Template context (automatically provided)
        asset_key: The key in the manifest (e.g., 'main.js')
        app: Optional app name to explicitly load from (e.g., 'vogcheck')

    Returns:
        The full static URL with hash (e.g., '/static/main.abc123.js')
        Falls back to static tag if key not found in manifest.
    """
    manifests = ManifestLoader.get_manifest()
    config = ManifestLoader._get_config()
    main_app_name = config.get("main_app_name", "main")

    # Handle explicit app parameter
    if app:
        # Warn if app doesn't exist in manifests
        if app not in manifests:
            logger.warning(
                f"[django-multi-manifest-loader] Asset '{asset_key}' references non-existent app '{app}'. "
                f"Available apps: {', '.join(sorted(manifests.keys()))}"
            )

        hashed_filename = manifests.get(app, {}).get(asset_key, asset_key)
    else:
        # Auto-detect current app from template
        current_app = _detect_app_from_context(context)
        hashed_filename = None

        # Try current app first
        if current_app and current_app in manifests:
            hashed_filename = manifests[current_app].get(asset_key)

        # Fall back to main app if not found
        if not hashed_filename and main_app_name in manifests:
            hashed_filename = manifests[main_app_name].get(asset_key)

        # If still not found, use asset_key as-is
        if not hashed_filename:
            hashed_filename = asset_key

    # If the hashed_filename already starts with http or /, return it as is
    if hashed_filename.startswith(("http://", "https://", "/")):
        return hashed_filename

    # Otherwise use Django's static helper
    return static(hashed_filename)


@register.simple_tag(takes_context=True)
def manifest_raw(context, asset_key, app=None):
    """
    Get the raw manifest value without the static URL processing.

    Usage:
        {% manifest_raw 'main.js' %}
        {% manifest_raw 'config.js' app='vogcheck' %}

    Args:
        context: Template context (automatically provided)
        asset_key: The key in the manifest (e.g., 'main.js')
        app: Optional app name to explicitly load from (e.g., 'vogcheck')

    Returns:
        The manifest value (e.g., 'static/main.abc123.js')
    """
    manifests = ManifestLoader.get_manifest()
    config = ManifestLoader._get_config()
    main_app_name = config.get("main_app_name", "main")

    # Handle explicit app parameter
    if app:
        # Warn if app doesn't exist in manifests
        if app not in manifests:
            logger.warning(
                f"[django-multi-manifest-loader] Asset '{asset_key}' references non-existent app '{app}'. "
                f"Available apps: {', '.join(sorted(manifests.keys()))}"
            )

        return manifests.get(app, {}).get(asset_key, asset_key)

    # Auto-detect current app from template
    current_app = _detect_app_from_context(context)
    result = None

    # Try current app first
    if current_app and current_app in manifests:
        result = manifests[current_app].get(asset_key)

    # Fall back to main app if not found
    if not result and main_app_name in manifests:
        result = manifests[main_app_name].get(asset_key)

    # If still not found, use asset_key as-is
    return result if result else asset_key
