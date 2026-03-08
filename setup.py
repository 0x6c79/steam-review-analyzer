#!/usr/bin/env python3
"""
Setup configuration for Steam Review Analyzer package.
This setup.py provides backward compatibility alongside pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    name="steam-review-analyzer",
    version="1.0.0",
    description="A comprehensive tool for analyzing Steam game reviews using NLP and sentiment analysis",
    long_description=open("README.md", encoding="utf-8").read()
    if __import__("os").path.exists("README.md")
    else "",
    long_description_content_type="text/markdown",
    author="Steam Review Analyzer Team",
    license="MIT",
    url="https://github.com/yourusername/steam-review-analyzer",
    packages=find_packages(),
    python_requires=">=3.12",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "steam-review=src.steam_review.cli.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
    ],
)
