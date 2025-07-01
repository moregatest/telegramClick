# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TelegramClick is a zero-intrusion Click CLI to Telegram Bot converter that allows transforming existing Click CLI tools into fully functional Telegram bots within 5 minutes without modifying existing code.

## Core Architecture

The project consists of four main components:

1. **Framework** (`src/telegram_click/framework.py`): The core `ClickToTelegramConverter` class that handles the conversion logic between Click commands and Telegram bot interactions.

2. **Factory Functions** (`src/telegram_click/factory.py`): Provides convenience functions like `create_bot_from_click_group()` and `create_bot_from_cli_file()` for different use cases.

3. **Decorators** (`src/telegram_click/decorators.py`): Offers decorator-based approaches including `@telegram_bot`, `@secure_telegram_bot`, and `@production_telegram_bot` for easy integration.

4. **Types and Utilities** (`src/telegram_click/types.py`, `src/telegram_click/utils.py`): Core data structures like `TelegramClickConfig`, `TelegramClickContext`, and utility functions for parameter conversion and validation.

## Development Commands

### Setup Environment
```bash
# Install dependencies and setup dev environment
uv sync --dev
```

### Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_framework.py

# Run tests with coverage
uv run pytest --cov
```

### Code Quality
```bash
# Format code
uv run black .
uv run isort .

# Type checking
uv run mypy src/

# Linting
uv run flake8 src/
```

### Build and Install
```bash
# Build package
uv build

# Install in development mode
uv pip install -e .
```

## Key Design Patterns

### Three Usage Patterns
1. **Decorator Pattern**: Use `@telegram_bot` decorator on Click groups for new projects
2. **Factory Pattern**: Use `create_bot_from_cli_file()` for wrapping existing CLI files without modification
3. **Direct Instantiation**: Use `ClickToTelegramConverter` directly for maximum control

### Parameter Conversion Logic
The framework automatically converts Click parameter types to appropriate Telegram UI elements:
- `click.Choice` → Inline keyboard buttons
- `click.BOOL` → Yes/No buttons  
- `click.INT/FLOAT` → Text input with validation
- Regular strings → Text input

### Security Features
- Admin user restrictions via `admin_users` parameter
- Command filtering with `commands_whitelist` and `commands_blacklist`
- Production-ready decorators with built-in dangerous command blocking

## Testing Strategy

Tests are organized by component:
- `test_framework.py`: Core converter functionality
- `test_cli.py`: CLI interface testing
- `test_utils.py`: Utility function testing

Mock objects are used extensively for Telegram bot testing to avoid requiring actual bot tokens during development.

## Configuration

Configuration is centralized in the `TelegramClickConfig` dataclass, supporting both direct Click group objects and file path-based CLI discovery.