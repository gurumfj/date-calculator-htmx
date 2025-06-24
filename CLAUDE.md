# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based date calculator application with an HTMX-powered frontend. The application provides both date arithmetic (adding/subtracting days, weeks, months) and date interval calculations through an interactive web interface.

## Development Commands

### Core Commands
```bash
# Install dependencies
uv sync

# Run development server (with auto-reload)
uv run dev

# Run production server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# Alternative: Direct start command
uv run start
```

### Testing
```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=app

# Run specific test file
uv run python -m pytest tests/test_models.py -v
```

### Code Quality
```bash
# Check code style and issues
uv run ruff check .

# Auto-format code
uv run ruff format .

# Run type checking
uv run mypy app

# Run both checks and formatting
uv run ruff check . && uv run ruff format .
```

## Architecture Overview

### Core Components
- **FastAPI Application** (`app/main.py`): Main application with routes for date calculations, session management, and HTMX endpoints
- **Data Models** (`app/models.py`): Pydantic models for `DateData` (date arithmetic) and `DateInterval` (interval calculations)
- **Session Management** (`app/session.py`): Utilities for storing calculation history in browser sessions

### Key Design Patterns
- **Session-based Storage**: All calculations are stored in browser sessions, no database required
- **HTMX Integration**: Frontend uses HTMX for seamless partial page updates without JavaScript
- **Dual Calculation Types**: Supports both forward/backward date arithmetic and interval calculations
- **Template Fragments**: Uses granular HTML templates for HTMX partial responses

### Frontend Structure
- **Templates**: Jinja2 templates in `templates/date_calculator/` with component-based organization
- **Static Assets**: CSS (TailwindCSS), icons, and other assets in `static/`
- **HTMX Patterns**: Forms submit via HTMX with targeted DOM updates for results

### Data Flow
1. User interacts with form (date arithmetic or interval calculation)
2. HTMX submits form data to FastAPI endpoints
3. Pydantic models validate and process calculation logic
4. Results stored in session and returned as HTML fragments
5. HTMX updates specific DOM elements with results

### Key Endpoints
- `GET /`: Main calculator interface
- `POST /calculate`: Date arithmetic calculations
- `POST /calculate_interval`: Date interval calculations
- `POST /pickup`: Pick up previous results to form
- `DELETE /delete/{id}`: Delete specific calculation
- `POST /save_description/{id}`: Save calculation descriptions

## Environment Configuration

The application uses environment variables for configuration:
- `SECRET_KEY`: Session security key (must change in production)
- `HOST`: Server bind address (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `DEBUG`: Enable debug mode (default: `false`)

Copy `.env.sample` to `.env` for local development configuration.

## Development Notes

### Month Calculations
The `DateData.calculate_date()` method implements accurate month arithmetic that properly handles month boundaries and leap years, rather than using approximations.

### Session Management
All calculation history is session-based and temporary. No persistent storage is used, making the application stateless and easy to deploy.

### Template Organization
Templates are organized into reusable fragments for HTMX partial updates. Key templates include result cards, form content, and table components.