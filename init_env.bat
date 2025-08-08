@echo off
REM Windows batch script to set up Python virtual environment and install packages
python -m venv .venv
call .venv\Scripts\activate
pip install --upgrade pip
pip install mypy isort ruff pytest pre-commit
