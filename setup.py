from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

# Read the version from __init__.py
version = {}
with open(this_directory / "django_multi_manifest_loader" / "__init__.py") as f:
    for line in f:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="django-multi-manifest-loader",
    version=version.get("__version__", "0.1.0"),
    author="Pescheck",
    author_email="devops@pescheck.nl",
    description="Standalone template tag for loading webpack manifest files from multiple Django packages/apps",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pescheck/django-multi-manifest-loader",
    project_urls={
        "Bug Reports": "https://github.com/pescheck/django-multi-manifest-loader/issues",
        "Source": "https://github.com/pescheck/django-multi-manifest-loader",
    },
    packages=find_packages(exclude=["tests*"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Framework :: Django :: 5.1",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="django webpack manifest cache-busting static-files",
    python_requires=">=3.10",
    install_requires=[
        "Django>=4.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-django>=4.5",
            "black>=23.0",
            "flake8>=6.0",
        ],
    },
)
