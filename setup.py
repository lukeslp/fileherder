"""Setup script for fileherder package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="fileherder",
    version="1.0.1",
    author="Luke Steuber",
    author_email="luke@dr.eamer.dev",
    description="Lightweight file management utilities for deduplication and organization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lukeslp/fileherder",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No required dependencies (Rich is optional)
    ],
    extras_require={
        "cli": ["rich>=10.0.0"],
        "dev": ["pytest>=7.0.0", "pytest-cov>=3.0.0"],
    },
    entry_points={
        "console_scripts": [
            "fileherder=fileherder.cli:main",
        ],
    },
    keywords="files deduplication organization utilities",
    project_urls={
        "Bug Reports": "https://github.com/lukeslp/fileherder/issues",
        "Source": "https://github.com/lukeslp/fileherder",
    },
)
