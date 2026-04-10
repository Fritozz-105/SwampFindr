# SwampFindr Backend API

REST API backend for SwampFindr, built with Flask and included Swagger documentation.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration management
│   ├── agents/              # Agent system code
│   │   ├── __init__.py
│   │   ├── prompts.py       # System prompts & templates
│   │   ├── tools.py         # Agent tools/functions
│   │   └── memory.py        # Conversation memory management
│   │
│   ├── routes/              # API endpoints
│   │   ├── __init__.py      # Blueprint registration
│   │   └── api.py           # Listings API routes
|   |
│   ├── services/            # Business logic layer
│   │   └── __init__.py
│   ├── schemas/             # Data validation schemas
│   │   └── __init__.py
│   └── utils/               # Helper functions. Also the mongodb setup
│       └── __init__.py
├── tests/                   # Test suite
│   ├── __init__.py
│   └── test_api.py
├── scripts/                 # Data Pipeline Scripts
│   └── listings.py
|   └── helpers.py
├── run.py                   # Application entry point
├── pyproject.toml           # UV/Python dependencies
└── README.md                # This file
```

## Setup

### Prerequisites

- Python 3.11 or higher
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

1. **Clone the repository** (if not already done)

2. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

3. **Install dependencies using UV:**

   ```bash
   uv sync
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` with your configuration values.

### Running the Application

#### Development Mode

```bash
# Using Python directly
uv run python run.py

# Or activate the virtual environment first
source .venv/bin/activate  # On macOS/Linux
# .venv\Scripts\activate   # On Windows
python run.py
```

The API will be available at:

- **API Base URL:** `http://localhost:8080/api/v1`
- **Swagger UI Docs:** `http://localhost:8080/api/v1/docs`

#### Production Mode

```bash
FLASK_ENV=production python run.py
```

## Development

When pushing your changes, also update the Heroku remote
`git subtree push --prefix backend heroku main`

## 📚 API Documentation

Once the server is running, visit `http://localhost:8080/api/v1/docs` for interactive Swagger documentation.

### Available Endpoints

#### Listings

- `GET /api/v1/listings/` - Get all listings with optional filters
- `POST /api/v1/listings/` - Create a new listing
- `GET /api/v1/listings/<id>` - Get specific listing
- `PUT /api/v1/listings/<id>` - Update a listing
- `DELETE /api/v1/listings/<id>` - Delete a listing
- `GET /api/v1/listings/search` - Search listings

### Query Parameters

- `city` - Filter by city
- `minPrice` - Minimum rent price
- `maxPrice` - Maximum rent price
- `beds` - Number of bedrooms
- `baths` - Number of bathrooms

### Example Request

```bash
curl http://localhost:8080/api/v1/listings/?city=Gainesville&minPrice=1000&maxPrice=2000
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=app

# Run specific test file
uv run pytest tests/test_api.py

# Run with verbose output
uv run pytest -v
```

## 🛠️ Development

### Code Style

This project uses Black for code formatting and Flake8 for linting.

```bash
# Install dev dependencies
uv sync --group dev

# Format code
uv run black app/ tests/

# Lint code
uv run flake8 app/ tests/

# Type checking
uv run mypy app/
```

### Adding New Dependencies

```bash
# Add a new package
uv add package-name

# Add a dev dependency
uv add --dev package-name

# Sync after manual pyproject.toml changes
uv sync
```

### Project Configuration

Configuration is managed in `app/config.py` with support for multiple environments:

- `DevelopmentConfig` - Local development
- `ProductionConfig` - Production deployment
- `TestingConfig` - Running tests

Set the environment using the `FLASK_ENV` variable:

```bash
export FLASK_ENV=production  # or development, testing
```

## 📁 Key Files

- **`run.py`** - Application entry point
- **`app/__init__.py`** - Flask app factory pattern
- **`app/config.py`** - Configuration classes
- **`app/routes/`** - API endpoint definitions
- **`app/models/`** - Database models (add SQLAlchemy models here)
- **`app/services/`** - Business logic (keep routes thin)
- **`app/schemas/`** - Request/response validation schemas
- **`tests/`** - Test files using pytest

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
FLASK_ENV=development
DEBUG=True
SECRET_KEY=your-secret-key-here
PORT=8080
CONFIDENT_API_KEY=optional-for-deepeval-traces

# Add database URL when ready
# DATABASE_URL=postgresql://user:password@localhost:5432/swampfindr
```
