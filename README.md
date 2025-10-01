# Django Multi-Manifest Loader

**A simple, standalone template tag for loading webpack manifest files from multiple Django packages/apps. Zero dependencies on unmaintained packages.**

## Problem

When using webpack with multiple Django packages (like `righttowork-check`, `criminalrecords-check`, etc.), each package generates its own `manifest.json` file with hashed asset filenames for cache busting. However, most manifest loaders only read a single manifest file, making it impossible to reference assets from installed packages.

## Solution

`django-multi-manifest-loader` provides a standalone template tag that:
1. Loads the main webpack manifest (from your dashboard/main app)
2. Automatically discovers and loads manifest files from all installed Django packages
3. Merges them into a single manifest dictionary
4. Makes all assets available via the `{% manifest %}` template tag
5. **Zero dependencies** - doesn't rely on unmaintained packages like `django-manifest-loader`

## Installation

```bash
pip install django-multi-manifest-loader
```

Or install from source:

```bash
cd django-multi-manifest-loader
pip install -e .
```

## Usage

### 1. Add to INSTALLED_APPS

In your `settings.py`:

```python
INSTALLED_APPS = [
    # ...
    'django_multi_manifest_loader',
    # ...
]
```

### 2. Use in Templates

Now you can use the `{% manifest %}` tag for assets from any installed package:

```django
{% load manifest %}

{# Main app assets #}
<script src="{% manifest 'js/scripts.bundle.js' %}"></script>

{# Package assets with hashed filenames #}
<script src="{% manifest 'custom/candidate/wizard/multiple-upload.js' %}"></script>
```

## How It Works

The loader searches for manifest files in all installed Django apps using Django's staticfiles finders:

- Main manifest: `manifest.json` (from your webpack build)
- Package manifests: `*/manifest.json` (e.g., `righttoworkcheck/manifest.json`)

All manifest entries are merged, so you can reference any asset by its original key, and the loader returns the hashed filename.

## Package Manifest Example

In your Django package (e.g., `righttowork-check`), generate a manifest using webpack:

**webpack.config.js:**
```javascript
const { WebpackManifestPlugin } = require('webpack-manifest-plugin');

module.exports = {
    output: {
        path: path.resolve(__dirname, 'static/righttoworkcheck/js/'),
        filename: '[name].[contenthash:8].js',
        publicPath: 'righttoworkcheck/js/'
    },
    plugins: [
        new WebpackManifestPlugin({
            fileName: '../manifest.json',
            publicPath: 'righttoworkcheck/js/',
        }),
    ],
};
```

This generates `static/righttoworkcheck/manifest.json`:
```json
{
  "custom/candidate/wizard/multiple-upload.js": "righttoworkcheck/js/custom/candidate/wizard/multiple-upload.dd215078.js"
}
```

## Configuration

All configuration is optional. Add to your `settings.py`:

```python
DJANGO_MULTI_MANIFEST_LOADER = {
    # Enable/disable manifest caching
    # Default: True in production (not DEBUG), False in DEBUG mode
    'cache': True,

    # Enable debug logging to see which manifests are loaded
    # Default: False
    'debug': False,
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `cache` | `bool` | `not DEBUG` | Cache merged manifests in memory. Disable in development for hot reloading. |
| `debug` | `bool` | `False` | Enable detailed logging of manifest loading process. |

## Development

### Setup Development Environment

```bash
# Clone the repository
cd django-multi-manifest-loader

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install package with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=django_multi_manifest_loader --cov-report=term-missing

# Run specific test file
pytest tests/test_manifest_loader.py -v
```

### Code Quality

```bash
# Run all quality checks
flake8 django_multi_manifest_loader/ tests/
black --check django_multi_manifest_loader/ tests/
isort --check-only django_multi_manifest_loader/ tests/
ruff check django_multi_manifest_loader/ tests/

# Auto-format code
black django_multi_manifest_loader/ tests/
isort django_multi_manifest_loader/ tests/
ruff check --fix django_multi_manifest_loader/ tests/
```

### Clear Cache Programmatically

During development, you can clear the manifest cache:

```python
from django_multi_manifest_loader import ManifestLoader
ManifestLoader.clear_cache()
```

### Debug Mode

Enable debug mode to see detailed logging:

```python
# settings.py
DJANGO_MULTI_MANIFEST_LOADER = {
    'debug': True,
}
```

This will log:
- Number of manifest files found
- Path to each manifest being loaded
- Number of entries in each manifest
- Total merged entries

### Hot Reloading in Development

By default, caching is disabled in DEBUG mode (`cache=not DEBUG`). This means:
- **Production**: Manifests are cached for performance
- **Development**: Manifests are reloaded on each request for hot reloading

## Requirements

- Python >= 3.10
- Django >= 4.0

**No other dependencies!** This package is completely standalone.

## How It Works

The loader uses Django's `staticfiles` finders to discover manifest files:

1. **Main manifest**: Searches for `manifest.json` in static directories
2. **Package manifests**: Iterates through all `INSTALLED_APPS` and checks each for `<app_name>/manifest.json`
3. **Merging**: All found manifests are merged into a single dictionary (later entries override earlier ones)
4. **Caching**: Merged manifest is cached in memory (unless disabled)

## Publishing

### Automated Publishing to PyPI

The package automatically publishes to PyPI when you push a version tag:

```bash
# Update version in __init__.py
# Commit changes
git add django_multi_manifest_loader/__init__.py
git commit -m "Bump version to 0.2.0"

# Create and push tag
git tag v0.2.0
git push origin main --tags
```

This triggers the GitHub Actions workflow which:
1. Runs all tests across Python 3.10-3.12 and Django 4.2-5.1
2. Runs all linters (flake8, black, isort, ruff)
3. Builds the package
4. Publishes to PyPI using trusted publishing (no API tokens needed)

### Manual Publishing

```bash
# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI (requires PyPI credentials)
twine upload dist/*
```

## License

MIT
