"""Tests for ManifestLoader class."""

from unittest.mock import MagicMock, mock_open, patch

import pytest
from django.test import override_settings

from django_multi_manifest_loader.templatetags.manifest import ManifestLoader


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear manifest cache before each test."""
    ManifestLoader.clear_cache()
    yield
    ManifestLoader.clear_cache()


class TestManifestLoader:
    """Test suite for ManifestLoader."""

    def test_get_config_default(self):
        """Test default configuration."""
        config = ManifestLoader._get_config()
        assert isinstance(config, dict)
        assert config == {}

    @override_settings(DJANGO_MULTI_MANIFEST_LOADER={"cache": True, "debug": True})
    def test_get_config_custom(self):
        """Test custom configuration."""
        config = ManifestLoader._get_config()
        assert config == {"cache": True, "debug": True}

    def test_clear_cache(self):
        """Test cache clearing."""
        # Set cache
        ManifestLoader._cache = {"test": "value"}
        assert ManifestLoader._cache is not None

        # Clear cache
        ManifestLoader.clear_cache()
        assert ManifestLoader._cache is None

    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    def test_get_manifest_no_files(self, mock_find):
        """Test get_manifest when no manifest files are found."""
        mock_find.return_value = []

        manifest = ManifestLoader.get_manifest()
        assert manifest == {}

    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data='{"main.js": "main.abc123.js"}')
    def test_get_manifest_single_file(self, mock_file, mock_find, mock_apps):
        """Test get_manifest with a single manifest file."""
        # Mock apps to return empty list
        mock_apps.get_app_configs.return_value = []

        mock_find.side_effect = [
            ["/path/to/manifest.json"],  # Main manifest
        ]

        manifest = ManifestLoader.get_manifest()

        config = ManifestLoader._get_config()
        main_app_name = config.get("main_app_name", "main")

        assert main_app_name in manifest
        assert "main.js" in manifest[main_app_name]
        assert manifest[main_app_name]["main.js"] == "main.abc123.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open")
    def test_get_manifest_multiple_files(self, mock_file_open, mock_find, mock_apps):
        """Test get_manifest with multiple manifest files."""
        # Mock app configs
        mock_app1 = MagicMock()
        mock_app1.name = "testapp1"
        mock_app2 = MagicMock()
        mock_app2.name = "testapp2"
        mock_apps.get_app_configs.return_value = [mock_app1, mock_app2]

        # Mock finders.find
        def find_side_effect(path, all=False):
            if path == "manifest.json":
                return ["/path/to/main/manifest.json"]
            elif path == "testapp1/manifest.json":
                return ["/path/to/testapp1/manifest.json"]
            elif path == "testapp2/manifest.json":
                return None
            return None

        mock_find.side_effect = find_side_effect

        # Mock file contents
        manifest_contents = {
            "/path/to/main/manifest.json": '{"main.js": "main.abc123.js"}',
            "/path/to/testapp1/manifest.json": '{"app1.js": "app1.def456.js"}',
        }

        def open_side_effect(path, *args, **kwargs):
            content = manifest_contents.get(path, "{}")
            return mock_open(read_data=content)()

        mock_file_open.side_effect = open_side_effect

        manifest = ManifestLoader.get_manifest()

        config = ManifestLoader._get_config()
        main_app_name = config.get("main_app_name", "main")

        assert main_app_name in manifest
        assert "testapp1" in manifest
        assert "main.js" in manifest[main_app_name]
        assert "app1.js" in manifest["testapp1"]
        assert manifest[main_app_name]["main.js"] == "main.abc123.js"
        assert manifest["testapp1"]["app1.js"] == "app1.def456.js"

    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", side_effect=OSError("File not found"))
    def test_get_manifest_file_error(self, mock_file, mock_find, mock_apps):
        """Test get_manifest handles file errors gracefully."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
        ]

        # Should not raise, should log warning and return empty dict
        manifest = ManifestLoader.get_manifest()
        assert manifest == {}

    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data="invalid json")
    def test_get_manifest_invalid_json(self, mock_file, mock_find, mock_apps):
        """Test get_manifest handles invalid JSON gracefully."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
        ]

        # Should not raise, should log warning and return empty dict
        manifest = ManifestLoader.get_manifest()
        assert manifest == {}

    @override_settings(DEBUG=False)
    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data='{"main.js": "main.abc123.js"}')
    def test_caching_enabled_production(self, mock_file, mock_find, mock_apps):
        """Test caching is enabled in production (DEBUG=False)."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
        ]

        config = ManifestLoader._get_config()
        main_app_name = config.get("main_app_name", "main")

        # First call should load manifest
        manifest1 = ManifestLoader.get_manifest()
        assert manifest1 == {main_app_name: {"main.js": "main.abc123.js"}}

        # Second call should use cache (file shouldn't be read again)
        mock_file.reset_mock()
        manifest2 = ManifestLoader.get_manifest()
        assert manifest2 == {main_app_name: {"main.js": "main.abc123.js"}}
        mock_file.assert_not_called()

    @override_settings(DEBUG=True)
    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data='{"main.js": "main.abc123.js"}')
    def test_caching_disabled_debug(self, mock_file, mock_find, mock_apps):
        """Test caching is disabled in DEBUG mode by default."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
            ["/path/to/manifest.json"],
        ]

        config = ManifestLoader._get_config()
        main_app_name = config.get("main_app_name", "main")

        # First call
        manifest1 = ManifestLoader.get_manifest()
        assert manifest1 == {main_app_name: {"main.js": "main.abc123.js"}}
        call_count_1 = mock_file.call_count

        # Second call should reload (caching disabled in DEBUG)
        manifest2 = ManifestLoader.get_manifest()
        assert manifest2 == {main_app_name: {"main.js": "main.abc123.js"}}
        assert mock_file.call_count > call_count_1

    @override_settings(DJANGO_MULTI_MANIFEST_LOADER={"cache": True})
    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data='{"main.js": "main.abc123.js"}')
    def test_caching_forced_enabled(self, mock_file, mock_find, mock_apps):
        """Test caching can be explicitly enabled via config."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
        ]

        config = ManifestLoader._get_config()
        main_app_name = config.get("main_app_name", "main")

        # First call
        manifest1 = ManifestLoader.get_manifest()
        assert manifest1 == {main_app_name: {"main.js": "main.abc123.js"}}

        # Second call should use cache
        mock_file.reset_mock()
        manifest2 = ManifestLoader.get_manifest()
        assert manifest2 == {main_app_name: {"main.js": "main.abc123.js"}}
        mock_file.assert_not_called()

    @override_settings(DJANGO_MULTI_MANIFEST_LOADER={"cache": False})
    @patch("django_multi_manifest_loader.templatetags.manifest.apps")
    @patch("django_multi_manifest_loader.templatetags.manifest.finders.find")
    @patch("builtins.open", new_callable=mock_open, read_data='{"main.js": "main.abc123.js"}')
    def test_caching_forced_disabled(self, mock_file, mock_find, mock_apps):
        """Test caching can be explicitly disabled via config."""
        mock_apps.get_app_configs.return_value = []
        mock_find.side_effect = [
            ["/path/to/manifest.json"],
            ["/path/to/manifest.json"],
        ]

        # First call
        ManifestLoader.get_manifest()
        call_count_1 = mock_file.call_count

        # Second call should reload
        ManifestLoader.get_manifest()
        assert mock_file.call_count > call_count_1
