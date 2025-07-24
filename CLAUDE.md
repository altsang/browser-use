# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
```bash
pytest                           # Run all tests
pytest tests/test_agent.py      # Run specific test file
pytest -k "test_name"           # Run specific test by name
pytest --asyncio-mode=auto      # Run async tests (configured in pytest.ini)
```

### Linting and Formatting
```bash
ruff check                      # Check for linting issues
ruff format                     # Format code
ruff check --fix               # Fix auto-fixable issues
codespell                      # Check spelling
pre-commit run --all-files     # Run all pre-commit hooks
```

### Development Dependencies
```bash
uv sync --dev                  # Install development dependencies with UV
pip install browser-use        # Install main package
pip install "browser-use[memory]"  # Install with memory functionality (requires Python<3.13)
playwright install chromium   # Install browser for testing
```

### Running Examples
```bash
# Basic example
python examples/simple.py

# Advanced example with command-line options  
python examples/use-cases/restaurant_standee_detection.py --no-headless --advanced-mode --model gpt-4o

# With screenshots enabled
python examples/use-cases/restaurant_standee_detection.py --screenshots --no-headless --advanced-mode

# Bulk restaurant image collection
python examples/use-cases/bulk_restaurant_image_scraper.py --max-restaurants 50 --interior-limit 10 --exterior-limit 5

# UI/Web interface example
python examples/ui/gradio_demo.py
```

### Command-line Flags
Common flags for example scripts:
- `--cdp-port PORT`: CDP port for browser connection (for connecting to existing browser)
- `--headless/--no-headless`: Run browser in headless/visible mode
- `--advanced-mode/--no-advanced-mode`: Enable/disable advanced Playwright capabilities
- `--model MODEL`: Model to use (default: gpt-4o)
- `--use-azure`: Use Azure OpenAI instead of OpenAI
- `--task "TASK"`: Custom task to perform
- `--screenshots`: Enable taking screenshots during automation
- `--debug`: Enable debug logging

### Environment Setup
- Required: Set LLM provider API keys in `.env` file (OPENAI_API_KEY, ANTHROPIC_API_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, AZURE_OPENAI_API_VERSION, GEMINI_API_KEY, DEEPSEEK_API_KEY, GROK_API_KEY, NOVITA_API_KEY)
- Optional: NAVER_USERNAME/NAVER_PASSWORD for Naver-specific examples
- Python >=3.11,<4.0 required (memory functionality requires <3.13 due to PyTorch compatibility)
- Use `uv` for dependency management (configured in pyproject.toml)

## Architecture Overview

### Core Components Architecture
The codebase follows a layered architecture with clear separation of concerns:

**Agent Layer** (`browser_use/agent/`):
- `service.py`: Main Agent class orchestrating browser automation with LLM
- `message_manager/`: Handles LLM message formatting and conversation management  
- `memory/`: Long-term memory functionality using vector embeddings
- `prompts.py`: System and agent prompts for LLM interactions

**Browser Layer** (`browser_use/browser/`):
- `browser.py`: Browser configuration and Playwright initialization
- `context.py`: BrowserContext - main interface for browser interactions
- `chrome.py`: Chrome-specific browser implementations

**Controller Layer** (`browser_use/controller/`):
- `service.py`: Controller manages action execution and browser state
- `registry/`: Action registry system for pluggable browser actions

**DOM Layer** (`browser_use/dom/`):
- `service.py`: DOM tree extraction and element processing
- `buildDomTree.js`: JavaScript for DOM tree extraction sent to browser
- `clickable_element_processor/`: Identifies and processes clickable elements
- `history_tree_processor/`: Manages DOM state history for agent context

### Key Interaction Patterns

**Agent-Browser Communication Flow**:
1. Agent receives task and generates browser actions via LLM
2. Controller executes actions through BrowserContext 
3. DomService extracts current page state as DOM tree
4. Agent processes DOM feedback and plans next actions
5. MessageManager maintains conversation context with token limits

**Advanced Mode Features**:
- JavaScript execution via `page.evaluate()`
- Iframe traversal and interaction
- Enhanced Korean text detection for Naver websites
- Screenshot capabilities with base64 encoding
- Dynamic element selection with retry logic

### Tool System
- `tools/registry.py`: Central tool registration system
- `tools/standee_detection/`: YOLO-based image detection tool
- `tools/mcp_protocol.py`: Model Context Protocol integration
- Tools are automatically discovered and registered with the agent

### Testing Structure
- `tests/`: Comprehensive test suite with async support
- `conftest.py`: Shared test fixtures and browser setup
- `mind2web_data/`: Test data for web automation benchmarks
- Tests cover core functionality, browser interactions, and tool integrations

### Configuration Management
- `pyproject.toml`: Main project configuration with UV dependency management
- Ruff configured for code formatting (single quotes, tabs, 130 char line length)
- pytest.ini configures async test mode with markers for slow, integration, unit tests
- Memory functionality available as optional dependency (`pip install "browser-use[memory]"`)
- No additional .cursorrules or similar configuration files present

## Important Implementation Notes

### Browser Automation Patterns
- Use `BrowserContext` for all browser interactions, not raw Playwright
- Advanced mode (`advanced_mode=True`) enables full Playwright capabilities
- Screenshots use cross-platform paths: `os.path.expanduser("~")/screenshots/`
- CDP port extraction for existing browser connections in remote environments

### LLM Integration
- Supports multiple providers (OpenAI, Anthropic, Azure, Gemini, DeepSeek, etc.)
- Message management handles token limits and conversation pruning
- System prompts are loaded from markdown files for easier editing
- Tool calling uses structured output with Pydantic models

### Error Handling
- Custom exception hierarchy in `exceptions.py`
- Browser errors wrapped in `BrowserError` class
- Agent errors tracked in `AgentError` with step context
- Telemetry service tracks usage and errors for debugging

### Testing Patterns
- Use pytest markers: `@pytest.mark.slow`, `@pytest.mark.integration`, `@pytest.mark.unit`
- Run specific test types: `pytest -m "not slow"` to skip slow tests
- Async tests are automatically detected (configured in pytest.ini)
- Browser fixtures available in `conftest.py` for test setup