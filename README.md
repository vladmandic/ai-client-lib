# Workspace instructions

Follow the instructions below to ensure consistency and maintainability.  
Each folder has its own `README.md` file, consider it as the first place to look for information.  

- `/cli` - contains the client code, this is the core library: [README](cli/README.md)
- `/srv` - contains the server code, used for testing of webhooks/callbacks: [README](srv/README.md)
- `/test` - contains the cli tests for the project: [README](test/README.md)
- `/docs` - contains the project documentation: [README](docs/README.md)
- `/samples` - contains sample media files used for testing: [README](samples/README.md)

## Guidelines

- Project is a Python project.  
- Preserve the existing Python project structure and public APIs.
- Keep changes focused on the requested behavior.
- Do not run live tests against providers unless explicitly instructed.

## Installation

- Create virtual environment in `venv` directory.
- Activate the virtual environment using `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows).
- Install the required dependencies using `pip install -r requirements.txt`.

## Validation

- Always activate the virtual environment in `venv` before running any python code or validation commands.
- Run `ruff check srv cli test` to validate code style and linting.
- Run `pylint srv cli test` to validate code style and linting.
- Run `python -m compileall -q cli srv test` to verify syntax across all packages.
