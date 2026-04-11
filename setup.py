# Setup.py for GestureHUB
# For packaging and distribution
# Run: python setup.py develop (for development)

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, "r", encoding="utf-8") as f:
        long_description = f.read()

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, "r", encoding="utf-8") as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="gesturehub",
    version="1.0.0",
    author="GestureHUB Team",
    author_email="team@gesturehub.in",
    description="Gesture Recognition & Game Suite",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/harshhpatil/gesturehub",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Games/Entertainment",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gesturehub=app.gui_launcher:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.py",
            "assets/*",
            "assets/music/*",
            "assets/pictures/*",
            "config/*.py",
        ]
    },
)
