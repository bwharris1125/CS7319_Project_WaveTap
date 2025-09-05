# Dev Environment Scripts

This folder contains helper scripts to set up and manage the development environment for the WaveTap project.

## Scripts

- **init_env.sh**: Bash script for Unix-like systems (Linux/WSL). Creates a virtual environment and installs Python tooling and dependencies used during development.
- **attach_rtlsdr_wsl.ps1**: PowerShell helper to bind and attach an RTL-SDR USB device into WSL using usbipd on Windows.

## Usage

### On Linux / WSL:
```bash
# from the project root
bash dev-env/init_env.sh
```

### On Windows (attach RTL-SDR to WSL):
**NOTE: This was generated with CoPilot and still requires additional testing**
1. Run the PowerShell helper on Windows (requires usbipd):
```powershell
pwsh ./dev-env/attach_rtlsdr_wsl.ps1
```
2. Follow prompts from the script to bind and attach the RTL-SDR device to your WSL distribution.

Review each script before running and ensure you have administrative privileges when required.