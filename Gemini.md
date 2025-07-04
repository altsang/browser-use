
# Gemini Project Context

This document provides a comprehensive overview of the `browser-use` project for the Gemini agent.

## Project Overview

`browser-use` is a Python library that enables AI agents to control a web browser. It uses `playwright` for browser automation and various `langchain` integrations for connecting to different language models. The project is designed to be flexible, with a basic mode for simple tasks and an advanced mode that unlocks full `playwright` capabilities for complex web automation.

### Key Features

-   **AI-driven browser automation:** Control a browser using natural language tasks.
-   **Multiple LLM support:** Integrates with OpenAI, Anthropic, Google Gemini, DeepSeek, and more.
-   **Basic and Advanced Modes:** Choose between a simple interface or full `playwright` functionality.
-   **Extensible:** Users can add custom functions and hooks.
-   **Command-line interface:** Configure and run the agent with various flags.
-   **Memory:** Optional memory functionality for the agent.
-   **UI:** A Gradio UI is available for interactive testing.

## Project Structure

The project is organized into the following main directories:

-   `browser_use/`: The core Python package.
    -   `agent/`: The AI agent implementation.
    -   `browser/`: Browser control and `playwright` integration.
    -   `dom/`: DOM manipulation and element extraction.
    -   `controller/`: Manages the control flow.
    -   `telemetry/`: Usage tracking.
    -   `tools/`: Tools for the agent.
-   `docs/`: Project documentation.
-   `examples/`: Example scripts.
-   `tests/`: Unit and integration tests.

## Development Setup

### Dependencies

The project uses `uv` for dependency management. Key dependencies include:

-   `playwright`
-   `langchain` (and various integrations)
-   `pydantic`
-   `ruff` (for linting and formatting)
-   `pytest` (for testing)
-   `pre-commit` (for code quality)

### Linting and Formatting

The project uses `ruff` for linting and formatting. The configuration is in `pyproject.toml`. The main rules are:

-   Line length: 130
-   Quote style: single
-   Indent style: tab

### Pre-commit Hooks

The project uses `pre-commit` to enforce code quality. The hooks include:

-   `ruff` (linting and formatting)
-   `codespell` (spell checking)
-   Various checks for file integrity and consistency.

### Testing

The project uses `pytest` for testing. Tests are located in the `tests/` directory. To run the tests, use the `pytest` command.

## How to Run

The `README.md` provides detailed instructions on how to run the agent. The basic steps are:

1.  Install the dependencies: `pip install browser-use`
2.  Install `playwright`: `playwright install chromium`
3.  Set up the `.env` file with API keys.
4.  Run an example script, e.g., `python examples/advance.py`.

## My Role

My role is to assist with the development of this project. I will adhere to the project's conventions, including:

-   **Code style:** I will follow the `ruff` configuration in `pyproject.toml`.
-   **Testing:** I will add or update tests when I make changes to the code.
-   **Documentation:** I will update the documentation when I add new features or change existing ones.
-   **Commits:** I will write clear and concise commit messages.
-   **Pull requests:** I will create pull requests for my changes and wait for them to be reviewed and approved.
