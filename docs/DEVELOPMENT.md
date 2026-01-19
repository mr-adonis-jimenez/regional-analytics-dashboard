# Development Setup Guide

This guide will help you set up your development environment for the Geo-Analytics API.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Workflow](#development-workflow)
- [Code Quality](#code-quality)
- [Testing](#testing)
- [Debugging](#debugging)
- [Database Management](#database-management)
- [API Documentation](#api-documentation)
- [Contributing](#contributing)

## Prerequisites

### Required Software

- Python 3.11+
- Docker and Docker Compose
- Git
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Recommended Tools

- VS Code or PyCharm
- Postman or Insomnia (API testing)
- pgAdmin or DBeaver (database management)
- Redis Commander (Redis GUI)

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mr-adonis-jimenez/Geo-Analytics-API.git
cd Geo-Analytics-API
```

### 2. Create Virtual Environment

```bash
# Using venv
python -m venv venv

# Activate on Linux/Mac
source venv/bin/activate

# Activate on Windows
venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Or using pip-tools
pip-sync requirements.txt requirements-dev.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your local settings:

```env
# Application
APP_ENV=development
APP_DEBUG=true
APP_PORT=8000
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://geouser:geopass@localhost:5432/geoanalytics_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Development
RELOAD=true
LOG_LEVEL=DEBUG
```

### 5. Start Development Services

#### Using Docker Compose (Recommended)

```bash
# Start all services (database, redis, API)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Manual Setup

```bash
# Start PostgreSQL (if not using Docker)
sudo service postgresql start

# Start Redis (if not using Docker)
sudo service redis-server start

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 6. Database Setup

```bash
# Create database
createdb geoanalytics_dev

# Run migrations
alembic upgrade head

# Seed database (if seed script exists)
python scripts/seed_db.py
```

## Development Workflow

### Project Structure

```
Geo-Analytics-API/
├── .github/              # GitHub Actions workflows
├── alembic/              # Database migrations
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── src/
│   ├── api/             # API routes
│   ├── core/            # Core functionality
│   ├── models/          # Database models
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── utils/           # Utility functions
├── tests/               # Test files
├── main.py              # Application entry point
├── requirements.txt     # Production dependencies
└── requirements-dev.txt # Development dependencies
```

### Running the Application

```bash
# Development mode with auto-reload
uvicorn main:app --reload

# With custom host and port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Using Python directly
python main.py
```

### Hot Reload

The development server automatically reloads when you make changes to:
- Python files
- Configuration files

### Environment Variables

You can override environment variables:

```bash
# Temporarily set variables
APP_PORT=8080 LOG_LEVEL=DEBUG python main.py

# Or use .env file (automatically loaded)
```

## Code Quality

### Linting

We use multiple linters to maintain code quality:

```bash
# Ruff (fast Python linter)
ruff check .

# Fix auto-fixable issues
ruff check --fix .

# Black (code formatter)
black .

# Check formatting without changes
black --check .

# isort (import sorting)
isort .

# Check imports
isort --check-only .
```

### Type Checking

```bash
# mypy (static type checker)
mypy src/

# With stricter checks
mypy --strict src/
```

### Pre-commit Hooks

Install pre-commit hooks to run checks automatically:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Code Style Guidelines

- Follow PEP 8
- Maximum line length: 100 characters
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_api.py::test_health_check

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

### Test Categories

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# Slow tests (marked as slow)
pytest -m "not slow"
```

### Test Coverage

Aim for >80% test coverage:

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing

# HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Debugging

### VS Code Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false
    }
  ]
}
```

### Debugging Tips

```python
# Use Python debugger
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()

# Print debugging
import logging
logger = logging.getLogger(__name__)
logger.debug(f"Variable value: {variable}")
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Different log levels
logger.debug("Detailed information")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical error")
```

## Database Management

### Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Check current version
alembic current

# View migration history
alembic history
```

### Database CLI

```bash
# Connect to database
psql geoanalytics_dev

# Common commands
\dt          # List tables
\d+ table   # Describe table
\q          # Quit
```

### Seed Data

Create `scripts/seed_db.py`:

```python
from src.database import SessionLocal
from src.models import User, Analytics

def seed_database():
    db = SessionLocal()
    try:
        # Add seed data
        user = User(name="Test User", email="test@example.com")
        db.add(user)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
```

## API Documentation

### Interactive Docs

Once the server is running:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

### Adding Documentation

```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.get(
    "/items/",
    response_model=List[Item],
    summary="List all items",
    description="Retrieve a paginated list of all items",
    response_description="List of items with pagination"
)
async def list_items(
    skip: int = 0,
    limit: int = 100
):
    """
    List all items with pagination.
    
    Args:
        skip: Number of items to skip
        limit: Maximum number of items to return
    
    Returns:
        List of items
    """
    return get_items(skip=skip, limit=limit)
```

## Contributing

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Create bugfix branch
git checkout -b fix/bug-description

# Create docs branch
git checkout -b docs/documentation-update
```

### Commit Messages

Follow conventional commits:

```
feat: add new endpoint for analytics
fix: resolve database connection issue
docs: update API documentation
test: add unit tests for services
refactor: improve error handling
style: format code with black
chore: update dependencies
```

### Pull Request Checklist

Before submitting:

- [ ] Code passes all tests
- [ ] Code is formatted (black, isort)
- [ ] Code passes linting (ruff)
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No merge conflicts

### Code Review Process

1. Create pull request
2. CI/CD checks must pass
3. Request review from team members
4. Address feedback
5. Get approval
6. Merge to main

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Ensure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Connection Errors

```bash
# Check if PostgreSQL is running
sudo service postgresql status

# Verify connection string
echo $DATABASE_URL
```

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [pytest Documentation](https://docs.pytest.org/)

## Getting Help

- Check existing issues on GitHub
- Ask in team Slack channel
- Consult the [troubleshooting guide](./TROUBLESHOOTING.md)
- Create a GitHub issue with details
