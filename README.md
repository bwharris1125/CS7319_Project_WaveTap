# WaveTap SDR Utilities (CS7319 - Software Architecture)

Repository for SMU Software Architecture (Course CS7319) Class Project
<p align="center">
   <img src="documentation/wavetap_icon.png" 
   alt="WaveTap Logo" width="200"/>
</p>
<div style="text-align: center;">
    ADS-B and SDR Utilities
</div>

## Project Structure
```
CS7319_SW_Arch/
├── src/              # Main source code for reusable modules
│   ├── sdr/          # Software Defined Radio modules
│   ├── main.py       # Main application entry point
│   └── README.md     # Source code documentation
├── tests/            # Unit and integration tests (pytest)
├── documentation/    # Documentation, diagrams and project instructions
│   ├── diagrams/     # Mermaid source (.mmd)
│   └── diagrams_output/ # Generated PNGs
├── tools/            # Utility scripts and tools
│   └── adsb_rtlsdr_pymodes.py # ADS-B decoding utility
├── dev-env/          # Development environment configuration
│   └── init_env.sh   # Environment setup script
├── pyproject.toml    # Project configuration
├── README.md         # Project documentation
└── LICENSE           # Project license (MIT)
```

## Getting Started

- Use the provided setup script (`dev-env/init_env.sh`) to initialize your Python environment and install dependencies.
- All code is primarily written in Python, with open source libraries as needed.

## Installation

To set up the Python virtual environment and install required libraries:

### Linux/WSL
1. Open a terminal and navigate to the project directory.
2. Run:
   ```bash
   bash dev-env/init_env.sh
   ```

### Installed Libraries
The setup script will install the following Python libraries in the virtual environment:
- `mypy` (static type checking)
- `isort` (import sorting)
- `ruff` (linting and code quality)
- `pytest` (testing framework)
- `pytest-cov` (test coverage)
- `fastapi` (web application framework)
- `httpx` (HTTP client for external API communication)
- `pyrtlsdr` (RTL-SDR library for software defined radio)
- `setuptools` (package development and distribution tools)

## RTL-SDR Setup

This project includes Software Defined Radio (SDR) functionality using RTL-SDR dongles. The setup script automatically installs the required system libraries.

### WSL2 USB Device Setup
If you're using WSL2 on Windows, you'll need to share your RTL-SDR USB device:

1. **Install usbipd-win on Windows** (PowerShell as Administrator):
   ```powershell
   winget install usbipd
   ```

2. **Find your RTL-SDR device**:
   ```powershell
   usbipd list
   ```

3. **Share and attach the device** (replace X-X with your device's bus ID):
   ```powershell
   usbipd bind --busid X-X
   usbipd attach --wsl --busid X-X
   ```

4. **Verify in WSL**:
   ```bash
   lsusb | grep -i rtl
   rtl_test -t
   ```

## Usage

### Running the SDR Application
To run the main SDR application:
```bash
source .venv/bin/activate
python src/main.py
```

### SDR Module
The RTL-SDR functionality is located in `src/sdr/radio.py`. This module provides basic RTL-SDR configuration and testing capabilities.

### Diagrams
System architecture sources are located in `documentation/diagrams/` and generated images are stored in `documentation/diagrams_output/`.
The repository includes a small helper script to render PNGs from the Mermaid sources:

```bash
bash documentation/generate_diagrams.sh
```

This script uses `mmdc` (mermaid-cli / puppeteer). If you see errors about missing Chrome/Chromium, install a system browser or set `PUPPETEER_EXECUTABLE_PATH` to the browser executable before running the script.

_Additional usage examples and instructions will be added as the project develops._

## Contributing

_Outline guidelines for contributing to this project (coding standards, pull requests, etc.)._

## Testing

All tests should be placed in the `tests/` folder and written using `pytest`.
To run tests:
```bash
pytest
```
_Explain how to run tests and ensure code quality (e.g., using pytest, ruff, mypy)._ 

## References

_List any references, resources, or documentation relevant to the project._

## Linux/WSL Setup Guide

This project is intended to be run exclusively on Linux or Windows Subsystem for Linux (WSL):

### 1. Install WSL (if on Windows)
- Open PowerShell as Administrator and run:
  ```powershell
  wsl --install
  ```
- Restart your computer if prompted.
- Choose and set up your preferred Linux distribution (e.g., Ubuntu) from the Microsoft Store.

### 2. Install the VS Code WSL Extension
- Open VS Code.
- Go to Extensions (`Ctrl+Shift+X`).
- Search for "Remote - WSL" and install the extension by Microsoft.

### 3. Open Your Project in WSL
- Open the Command Palette (`Ctrl+Shift+P`).
- Type and select: `Remote-WSL: Open Folder in WSL`.
- Choose your project folder (`CS7319_SW_Arch`).

### 4. Set Up Your Python Environment in WSL
- Open a terminal in VS Code (it will use WSL).
- Run:
  ```bash
  bash dev-env/init_env.sh
  ```
- This will create the virtual environment and install dependencies in WSL.

### 5. Update VS Code Settings (Optional)
- For Linux/WSL compatibility, set the Python interpreter path in `.vscode/settings.json`:
  ```json
  {
    "python.defaultInterpreterPath": ".venv/bin/python"
  }
  ```

You can now develop and run your project in a Linux environment using WSL, with all VS Code features.

---

### Disclaimer

AI assistance (GitHub Copilot) was used to help with documentation and environment setup for this project. Project code is to be primarily human-authored. Any use of AI assistants for code generation or other tasks will be clearly disclosed in relevant files or documentation sections.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---
