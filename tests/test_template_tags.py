"""Tests for manifest template tags."""

from unittest.mock import patch

import pytest
from django.template import Context, Template
from django.test import override_settings

from django_multi_manifest_loader.templatetags.manifest import (
    ManifestLoader,
    manifest,
    manifest_raw,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear manifest cache before each test."""
    ManifestLoader.clear_cache()
    yield
    ManifestLoader.clear_cache()


class TestManifestTag:
    """Test suite for {% manifest %} template tag."""

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    @override_settings(STATIC_URL="/static/")
    def test_manifest_tag_found(self, mock_get_manifest):
        """Test manifest tag returns hashed filename when found."""
        mock_get_manifest.return_value = {"main.js": "js/main.abc123.js"}

        result = manifest("main.js")
        assert "main.abc123.js" in result
        assert result.startswith("/static/")

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    @override_settings(STATIC_URL="/static/")
    def test_manifest_tag_not_found(self, mock_get_manifest):
        """Test manifest tag falls back to original key when not found."""
        mock_get_manifest.return_value = {}

        result = manifest("missing.js")
        assert "missing.js" in result

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    @override_settings(STATIC_URL="/static/")
    def test_manifest_tag_absolute_url(self, mock_get_manifest):
        """Test manifest tag handles absolute URLs."""
        mock_get_manifest.return_value = {"main.js": "https://cdn.example.com/main.abc123.js"}

        result = manifest("main.js")
        assert result == "https://cdn.example.com/main.abc123.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    @override_settings(STATIC_URL="/static/")
    def test_manifest_tag_absolute_path(self, mock_get_manifest):
        """Test manifest tag handles absolute paths."""
        mock_get_manifest.return_value = {"main.js": "/absolute/path/main.abc123.js"}

        result = manifest("main.js")
        assert result == "/absolute/path/main.abc123.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    def test_manifest_tag_in_template(self, mock_get_manifest):
        """Test manifest tag works in Django template."""
        mock_get_manifest.return_value = {"main.js": "js/main.abc123.js"}

        template = Template('{% load manifest %}{% manifest "main.js" %}')
        result = template.render(Context({}))
        assert "main.abc123.js" in result


class TestManifestRawTag:
    """Test suite for {% manifest_raw %} template tag."""

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    def test_manifest_raw_tag_found(self, mock_get_manifest):
        """Test manifest_raw tag returns raw value when found."""
        mock_get_manifest.return_value = {"main.js": "js/main.abc123.js"}

        result = manifest_raw("main.js")
        assert result == "js/main.abc123.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    def test_manifest_raw_tag_not_found(self, mock_get_manifest):
        """Test manifest_raw tag falls back to original key when not found."""
        mock_get_manifest.return_value = {}

        result = manifest_raw("missing.js")
        assert result == "missing.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.ManifestLoader.get_manifest")
    def test_manifest_raw_tag_in_template(self, mock_get_manifest):
        """Test manifest_raw tag works in Django template."""
        mock_get_manifest.return_value = {"main.js": "js/main.abc123.js"}

        template = Template('{% load manifest %}{% manifest_raw "main.js" %}')
        result = template.render(Context({}))
        assert result == "js/main.abc123.js"


class TestManifestIntegration:
    """Integration tests with real manifest files."""

    @pytest.fixture
    def temp_manifest(self, tmp_path):
        """Create temporary manifest file."""
        manifest_dir = tmp_path / "static"
        manifest_dir.mkdir()
        manifest_file = manifest_dir / "manifest.json"
        manifest_file.write_text('{"test.js": "test.abc123.js"}')
        return manifest_dir

    @override_settings(STATICFILES_DIRS=[])
    @patch("django.apps.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    def test_manifest_real_file(self, mock_find, mock_apps, temp_manifest):
        """Test manifest loading with real file."""
        mock_apps.get_app_configs.return_value = []
        manifest_file = temp_manifest / "manifest.json"
        mock_find.side_effect = [
            [str(manifest_file)],
        ]

        ManifestLoader.clear_cache()
        result = manifest("test.js")
        assert "test.abc123.js" in result
