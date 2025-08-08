# CS7319 - Software Architecture  

Repository for storing projects and homework assignments from SMU course CS7319 - Software Architecture.

## Disclaimer

AI assistance (GitHub Copilot) was used to help with documentation and environment setup for this project. Project code is to be primarily human-authored. Any use of AI assistants for code generation or other tasks will be clearly disclosed in relevant files or documentation sections.

## Project Structure

```
VS_Workspace/
├── src/              # Main source code for reusable modules
├── examples/         # In-class examples and sample code
├── experiments/      # Experimentation and prototype code
├── course_project/   # Main course project
├── tests/            # Unit and integration tests (pytest)
├── pyproject.toml    # Project configuration
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── README.md         # Project documentation
├── LICENSE           # Project license (MIT)
```

## Getting Started

- Use the provided setup script (`init_env.sh`) to initialize your Python environment and install dependencies.
- All code is primarily written in Python, with open source libraries as needed.

## Installation

To set up the Python virtual environment and install required libraries:

### Linux/WSL
1. Open a terminal and navigate to the project directory.
2. Run:
   ```bash
   bash init_env.sh
   ```

### Installed Libraries
The setup script will install the following Python libraries in the virtual environment:
- `mypy` (static type checking)
- `isort` (import sorting)
- `ruff` (linting and code quality)
- `pytest` (testing framework)
- `pre-commit` (automated code quality checks)
- `flask` (web application framework)

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automate code quality checks. To enable pre-commit hooks:

1. Install pre-commit (already included in setup script).
2. Run the following command in your terminal:
   ```bash
   pre-commit install
   ```
3. Hooks for `black`, `isort`, `ruff`, and `mypy` will run automatically on each commit.

## Usage

_Provide examples and instructions for running code, scripts, or modules. If you use Flask, add instructions for running your Flask app here._

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
- Choose your project folder (`VS_Workspace`).

### 4. Set Up Your Python Environment in WSL
- Open a terminal in VS Code (it will use WSL).
- Run:
  ```bash
  bash init_env.sh
  ```
- This will create the virtual environment and install dependencies in WSL.

### 5. Update VS Code Settings (Optional)
- For Linux/WSL compatibility, set the Python interpreter path in `.vscode/settings.json`:
  ```json
  "python.defaultInterpreterPath": ".venv/bin/python"
  "python.analysis.extraPaths": [
    ".venv/lib/python3.10/site-packages"
  ]
  ```

You can now develop and run your project in a Linux environment using WSL, with all VS Code features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---
