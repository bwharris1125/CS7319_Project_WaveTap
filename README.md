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

- Use the provided setup scripts (`init_env.bat` for Windows, `init_env.sh` for Linux) to initialize your Python environment and install dependencies.
- All code is primarily written in Python, with open source libraries as needed.

## Installation

To set up the Python virtual environment and install required libraries:

### Windows
1. Open Command Prompt and navigate to the project directory.
2. Run:
   ```cmd
   init_env.bat
   ```

### Linux
1. Open a terminal and navigate to the project directory.
2. Run:
   ```bash
   bash init_env.sh
   ```

### Installed Libraries
The setup scripts will install the following Python libraries in the virtual environment:
- `mypy` (static type checking)
- `isort` (import sorting)
- `ruff` (linting and code quality)
- `pytest` (testing framework)
- `pre-commit` (automated code quality checks)

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to automate code quality checks. To enable pre-commit hooks:

1. Install pre-commit (already included in setup scripts).
2. Run the following command in your terminal:
   ```bash
   pre-commit install
   ```
3. Hooks for `black`, `isort`, `ruff`, and `mypy` will run automatically on each commit.

## Usage

_Provide examples and instructions for running code, scripts, or modules._

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

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
