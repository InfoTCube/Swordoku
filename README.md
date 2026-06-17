# Swordoku

A real-time multiplayer Sudoku battle game. Race opponents to solve the same puzzle — fastest with fewest mistakes wins.

## Stack

- **Backend** — FastAPI, SQLAlchemy, Alembic, WebSockets
- **Frontend** — React 18, TypeScript, Vite
- **Database** — SQLite (dev) / PostgreSQL (prod)

## Local Development

> Docker support is planned. Until then, run the backend directly.

### Prerequisites

- Python 3.11+

### First-time setup

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -e .

# Copy env config and fill in values
cp .env.example .env

# Create the database and run migrations
alembic upgrade head
```

### Run the backend

```bash
uvicorn backend.main:app --reload
```

API is available at `http://localhost:8000`.  
Health check: `GET http://localhost:8000/health`  
Interactive docs: `http://localhost:8000/docs`

### Run tests

```bash
pip install -e ".[dev]"
pytest backend/tests/          # all tests
pytest backend/tests/ -v       # verbose
pytest backend/tests/ -x       # stop on first failure
```
