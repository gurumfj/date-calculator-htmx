# Date Calculator HTMX

A standalone FastAPI application for date calculations with interval computations, featuring an interactive HTMX-powered web interface.

## Features

### ⚡ Real-time Calculations
- **Date Arithmetic**: Add or subtract days, weeks, or months from any base date
- **Interval Calculations**: Calculate exact differences between two dates
- **Smart Month Handling**: Accurate calculations that properly handle month boundaries
- **Instant Results**: No page reloads required thanks to HTMX

### 🎨 Modern Web Interface
- **Clean Design**: Built with TailwindCSS for a professional look
- **Interactive Cards**: Calculation results displayed in organized cards
- **Editable Descriptions**: Add custom notes to your calculations
- **Calculation History**: Session-based storage with delete functionality
- **Responsive Layout**: Works seamlessly on desktop and mobile devices

### 🔧 Developer-Friendly
- **RESTful API**: Well-documented endpoints for programmatic access
- **Type Safety**: Built with Pydantic models for robust data validation
- **Easy Deployment**: Simple setup with environment-based configuration
- **Extensible**: Clean architecture for adding new features

## Quick Start

### Prerequisites
- **Python 3.8+** (Python 3.11+ recommended)
- **uv** (recommended) or pip for package management
- **Git** for cloning the repository

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

The application will be available at `http://localhost:8000`

### 🚀 Getting Started

1. **Interactive Calculator**: Visit `http://localhost:8000/` to start calculating dates
2. **API Documentation**: Visit `http://localhost:8000/docs` for OpenAPI/Swagger documentation
3. **Health Check**: Visit `http://localhost:8000/health` to verify the service is running

### 💡 Usage Tips

- **Date Picker**: Use the date input to select your base date
- **Quick Operations**: Use radio buttons to select days, weeks, or months
- **History Management**: Click on any calculation to add a description
- **Reuse Results**: Use the "使用" (Use) button to quickly pick up previous results
- **Clear History**: Use the trash button to remove individual calculations or clear all

## ⚙️ Configuration

Create a `.env` file from the template:

```bash
cp .env.sample .env
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SECRET_KEY` | Session security key | `your-secret-key...` | ⚠️ **Change in production** |
| `HOST` | Server bind address | `0.0.0.0` | No |
| `PORT` | Server port | `8000` | No |
| `DEBUG` | Enable debug mode | `false` | No |

### 🔒 Security Notes

- **Always change `SECRET_KEY` in production**
- Generate a secure key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Use environment variables or a secure vault for production secrets

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

### 🧪 Testing
```bash
# Run all tests
uv run python -m pytest

# Run with coverage
uv run python -m pytest --cov=app

# Run specific test file
uv run python -m pytest tests/test_models.py -v
```

### 🎯 Code Quality
```bash
# Check code style and potential issues
uv run ruff check .

# Auto-format code
uv run ruff format .

# Run both checks
uv run ruff check . && uv run ruff format .
```

### 🚀 Deployment

#### Development
```bash
uv run dev
```

#### Production
```bash
# Direct uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# With workers (for production)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With Docker (create Dockerfile)
docker build -t date-calculator .
docker run -p 8000:8000 date-calculator
```

## Technology Stack

- **Backend**: FastAPI, Pydantic
- **Frontend**: HTMX, Alpine.js, Tailwind CSS
- **Templating**: Jinja2
- **Session**: Starlette SessionMiddleware

## 📖 Examples

### Web Interface Usage

1. **Basic Date Calculation**:
   - Select a base date (e.g., 2024-01-15)
   - Choose amount (e.g., 3) and unit (months)
   - Click "向後計算" (Calculate Forward) or "向前計算" (Calculate Backward)
   - Result appears instantly below

2. **Date Interval Calculation**:
   - Switch to "日期間隔" (Date Interval) tab
   - Select start date and end date
   - View detailed breakdown of the interval

### API Usage

#### Date Calculation
```python
from datetime import date
from app.models import DateData

# Calculate 3 months after 2024-01-15
data = DateData.from_form_input(
    base_date="2024-01-15",
    operation="after",      # or "before"
    amount=3,
    unit="months",          # "days", "weeks", "months"
    id="calc_001",
    description="Quarterly review date"
)

result = DateData.calculate_date(data)
print(f"Result: {result.result}")  # 2024-04-15
print(f"Description: {result.description}")
```

#### Date Interval
```python
from app.models import DateInterval

# Calculate interval between project start and end
interval = DateInterval.from_form_input(
    start_date="2024-01-01",
    end_date="2024-12-31",
    description="Project duration"
)

print(f"Total days: {interval.days_diff}")
print(f"Breakdown: {interval.months_full} months, {interval.months_remainder_days} days")
print(f"Weeks: {interval.weeks_full} weeks, {interval.weeks_remainder_days} days")
```

#### HTTP API Calls
```bash
# Calculate date
curl -X POST "http://localhost:8000/calculate" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "base_date=2024-01-15&operation=after&amount=3&unit=months&id=test"

# Calculate interval
curl -X POST "http://localhost:8000/calculate_interval" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "start_date=2024-01-01&end_date=2024-12-31"
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