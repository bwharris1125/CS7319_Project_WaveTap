#!/bin/bash
# Linux shell script to set up Python virtual environment and install packages
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install mypy isort ruff pytest pre-commit flask
