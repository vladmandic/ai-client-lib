# Workspace instructions

Project is a Python project. Please follow the instructions below to ensure consistency and maintainability.
- `/srv` - contains the server code.
- `/cli` - contains the client code.

## Guidelines

- Preserve the existing Python project structure and public APIs.
- Keep changes focused on the requested behavior.

## Validation

- Always activate the virtual environment before running any python code or validation commands.
- Run `ruff check srv/* cli/*` to validate code style and linting.
- Run `pylint srv/* cli/*` to validate code style and linting.
