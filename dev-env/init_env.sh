#!/usr/bin/env bash
# Linux shell script to set up Python virtual environment and install packages

set -euo pipefail

# Determine project root (parent of this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project root: $PROJECT_ROOT"

# --- Install system dependencies required by pyrtlsdr (Debian/Ubuntu) ---
if command -v apt-get >/dev/null 2>&1; then
	echo "Checking system packages required for pyrtlsdr..."
	PKGS=(rtl-sdr librtlsdr-dev librtlsdr2 libusb-1.0-0-dev usbutils pkg-config build-essential)

	MISSING=()
	for pkg in "${PKGS[@]}"; do
		if ! dpkg -s "$pkg" >/dev/null 2>&1; then
			MISSING+=("$pkg")
		fi
	done

	if [ ${#MISSING[@]} -ne 0 ]; then
		echo "Missing system packages: ${MISSING[*]}"
		echo "Installing missing packages (requires sudo)..."
		sudo apt-get update -qq
		sudo apt-get install -y "${MISSING[@]}"
		echo "System packages installed."
	else
		echo "All required system packages are already installed."
	fi
else
	echo "apt-get not found. Please install these system packages manually:"
	echo "  rtl-sdr librtlsdr-dev librtlsdr2 libusb-1.0-0-dev usbutils pkg-config build-essential"
fi

# --- Install Node.js and Mermaid CLI (Linux) --- TODO TEST ME
if [[ "$(uname -s)" == "Linux" ]]; then
    if ! command -v npm >/dev/null 2>&1; then
        echo "Node.js and npm are not installed. Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "Node.js and npm are already installed."
    fi

    if ! command -v mmdc >/dev/null 2>&1; then
        echo "Mermaid CLI is not installed. Installing Mermaid CLI..."
        npm install -g @mermaid-js/mermaid-cli
    else
        echo "Mermaid CLI is already installed."
    fi
fi

# --- Create and activate Python virtual environment ---
cd "$PROJECT_ROOT"

if [ -d ".venv" ]; then
	echo "Existing virtual environment found at $PROJECT_ROOT/.venv - leaving in place"
else
	echo "Creating virtual environment at $PROJECT_ROOT/.venv"
	python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip and installing Python packages..."
pip install --upgrade pip
pip install mypy isort ruff pytest pytest-cov flask pyrtlsdr setuptools pyModeS

echo "Setup complete. RTL-SDR development environment is ready."
