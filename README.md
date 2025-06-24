# Date Calculator API

A simple and elegant date calculation API built with FastAPI that provides date arithmetic and interval calculations.

## Features

### 📅 Date Calculation
- Add or subtract days, weeks, or months from a base date
- Accurate month calculations that handle month boundaries correctly
- Session-based storage for calculation history

### 📊 Date Interval Calculation
- Calculate the exact difference between two dates
- Results include days, weeks, and months with remainder days
- Detailed breakdown showing full periods and remainders

### 🎨 Interactive Web Interface
- Clean, modern UI built with HTMX and TailwindCSS
- Real-time calculations without page reloads
- Editable descriptions for each calculation
- Calculation history with delete functionality

## Quick Start

### Requirements
- Python 3.11+
- uv (recommended) or pip

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/date-calculator-api.git
cd date-calculator-api

# Install dependencies
uv sync

# Run the development server
uv run python -m app.main
```

The API will be available at `http://localhost:8000`

### Usage

1. **Web Interface**: Visit `http://localhost:8000/date-calculator/` for the interactive calculator
2. **API Documentation**: Visit `http://localhost:8000/docs` for the automatic API documentation

### API Endpoints

- `GET /date-calculator/` - Main calculator interface
- `POST /date-calculator/calculate` - Perform date calculations
- `POST /date-calculator/calculate_interval` - Calculate date intervals
- `POST /date-calculator/pickup` - Pick up calculation results to form
- `DELETE /date-calculator/delete/{id}` - Delete specific calculation
- `POST /date-calculator/delete/all` - Clear all calculations
- `POST /date-calculator/save_description/{id}` - Save calculation description

## Development

### Project Structure
```
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── models.py        # Data models (DateData, DateInterval)
│   ├── routes.py        # API routes
│   └── session.py       # Session management
├── templates/           # Jinja2 templates
│   ├── date_calculator/ # Calculator templates
│   └── macros/          # Reusable template macros
├── static/              # Static assets (CSS, JS)
└── tests/               # Test suite
```

### Running Tests

```bash
uv run pytest tests/ -v
```

### Code Quality

```bash
# Type checking
uv run mypy app/

# Linting and formatting
uv run ruff check app/
uv run ruff format app/
```

## Examples

### Date Calculation
```python
from datetime import date
from app.models import DateData

# Calculate 3 months after today
data = DateData.from_form_input(
    base_date="2024-01-15",
    operation="after",
    amount=3,
    unit="months",
    id="new_calc"
)
result = DateData.calculate_date(data)
print(result.result)  # 2024-04-15
```

### Date Interval
```python
from app.models import DateInterval

# Calculate interval between two dates
interval = DateInterval.from_form_input(
    start_date="2024-01-01",
    end_date="2024-12-31"
)
print(f"Days: {interval.days_diff}")
print(f"Months: {interval.months_full} months, {interval.months_remainder_days} days")
```

## License

MIT License - feel free to use this project for any purpose.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

This project was extracted from a larger application and refactored into a standalone API for date calculations.