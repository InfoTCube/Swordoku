# Swordoku

A real-time multiplayer Sudoku battle game. Race opponents to solve the same puzzle — fastest with fewest mistakes wins.

## Stack

- **Backend** — FastAPI, SQLAlchemy, Alembic, WebSockets
- **Frontend** — React 18, TypeScript, Vite
- **Database** — SQLite (dev) / PostgreSQL (prod via Docker)

---

## Quick Start (Docker)

**Prerequisites:** Docker Desktop running.

```bash
# 1. Copy env config (the defaults work fine for local Docker)
cp .env.example .env

# 2. Build and start all three services
docker compose up --build
```

| Service | URL |
|---|---|
| App (frontend) | http://localhost |
| API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

The backend automatically runs database migrations on startup.

To stop and remove containers:

```bash
docker compose down          # keep the database volume
docker compose down -v       # also wipe the database
```

---

## Local Development (without Docker)

### Prerequisites

- Python 3.11+
- Node.js 20+

### Backend

```bash
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# Install dependencies
pip install -e .

# Copy env config
cp .env.example .env

# Run migrations and start the server
alembic upgrade head
uvicorn backend.main:app --reload
```

API available at `http://localhost:8000` — docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173` (proxies API calls to port 8000).

---

## Tests

```bash
pip install -e ".[dev]"
pytest backend/tests/          # all tests
pytest backend/tests/ -v       # verbose
pytest backend/tests/ -x       # stop on first failure
```
