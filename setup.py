from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="fake-news-detection-platform",
    version="1.2.0",
    author="Fake News Detection Team",
    author_email="support@fakenews-detection.com",
    description="A comprehensive fake news detection platform using machine learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/fake-news-detection-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "mypy>=1.7.1",
            "pre-commit>=3.6.0",
        ],
        "docs": [
            "mkdocs>=1.5.3",
            "mkdocs-material>=9.4.8",
        ],
        "monitoring": [
            "sentry-sdk>=1.38.0",
            "new-relic>=9.2.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "fake-news-api=backend.app:main",
            "fake-news-train=ml_core.training_pipeline.train_production_model:main",
        ],
    },
    include_package_data=True,
    package_data={
        "backend": ["models/*.pkl", "models/vectorizers/*.pkl"],
        "frontend": ["build/**/*"],
    },
    zip_safe=False,
)
