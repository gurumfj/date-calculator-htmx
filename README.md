# Date Calculator HTMX

A standalone FastAPI application for date calculations with interval computations, featuring an interactive HTMX-powered web interface.

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
git clone https://github.com/gurumfj/date-calculator-htmx.git
cd date-calculator-htmx

# Install dependencies
uv sync

# Set up environment variables (optional)
cp .env.sample .env
# Edit .env with your preferred settings

# Run the development server
uv run dev
```

The API will be available at `http://localhost:8000`

### Usage

1. **Web Interface**: Visit `http://localhost:8000/` for the interactive calculator
2. **API Documentation**: Visit `http://localhost:8000/docs` for the automatic API documentation

## Configuration

Environment variables can be set in `.env` file:

- `SECRET_KEY`: Secret key for session management (change in production)
- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8000)
- `DEBUG`: Enable debug mode (default: false)

### API Endpoints

- `GET /` - Main calculator interface
- `POST /calculate` - Perform date calculations
- `POST /calculate_interval` - Calculate date intervals
- `POST /pickup` - Pick up calculation results to form
- `DELETE /delete/{id}` - Delete specific calculation
- `POST /delete/all` - Clear all calculations
- `POST /save_description/{id}` - Save calculation description

## Development

### Project Structure
```
├── app/
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # Pydantic models and business logic
│   └── session.py       # Session management utilities
├── templates/
│   └── date_calculator/ # HTML templates
├── static/              # Static assets (CSS, JS)
├── .env.sample         # Environment variables template
└── pyproject.toml      # Project configuration
```

### Running Tests
```bash
uv run python -m pytest
```

### Code Quality
```bash
uv run ruff check .
uv run ruff format .
```

### Production Deployment
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Technology Stack

- **Backend**: FastAPI, Pydantic
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Templating**: Jinja2
- **Session**: Starlette SessionMiddleware

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