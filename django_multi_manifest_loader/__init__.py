"""
Django Multi-Manifest Loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A standalone template tag for loading webpack manifest files from multiple
Django packages/apps. No dependencies on unmaintained packages.

Usage:
    In template:

    {% load manifest %}
    <script src="{% manifest 'main.js' %}"></script>

Configuration (optional):
    In settings.py:

    DJANGO_MULTI_MANIFEST_LOADER = {
        'cache': True,  # Cache manifests (default: not DEBUG)
        'debug': False,  # Enable debug logging (default: False)
    }

"""

__version__ = "0.1.0"

from django_multi_manifest_loader.templatetags.manifest import ManifestLoader

__all__ = ["ManifestLoader", "__version__"]
