#!/bin/bash
# Linux shell script to set up Python virtual environment and install packages
python3 -m venv .venv
source .venv/bin/activate

echo "Upgrading pip and installing Python packages..."
pip install --upgrade pip
pip install mypy isort ruff pytest pytest-cov flask pyrtlsdr setuptools

echo "Setup complete! RTL-SDR development environment is ready."
