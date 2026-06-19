# Swordoku

A real-time competitive multiplayer Sudoku platform. Players race to solve the same puzzle simultaneously — first to fill all blank cells wins, or the player with the most correct cells when time runs out.

## Features

- **Multiplayer matches** — any number of players (2-4) solve the same puzzle at the same time
- **Live opponent progress** — see opponents' cell count and mistake count update in real time via WebSocket
- **Lobby system** — create a lobby, share an invite link, configure time and mistake limits, start when ready
- **Casual & ranked modes** — ranked matches update ELO ratings; casual matches do not
- **ELO rating system** — standard ELO (K=32), starting at 1200; updated atomically on match end via round-robin pairwise comparisons for matches with more than two players
- **Mistake limit** — configurable per lobby (default 3, range 0–10); a player is eliminated when their mistake count exceeds the limit; if all players are eliminated the best score still wins
- **Time limit** — configurable per lobby (default 10 min, range 5–25 min); when time runs out the winner is decided by most correct cells, then fewest mistakes
- **Puzzle generation** — server-side backtracking generator; every puzzle is guaranteed to have a unique solution; solution is never sent to clients
- **Difficulty levels** — Easy, Medium, Hard (classified by naked/hidden single analysis of the given cells)
- **Player profiles** — ELO, win/loss record, full paginated match history
- **Global leaderboard** — top players ranked by ELO

---

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Real-time | WebSockets (FastAPI / Starlette) |
| Database | SQLite (dev) / PostgreSQL 16 (Docker) |
| ORM / migrations | SQLAlchemy 2 + Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (`python-jose`, HS256) |
| Password hashing | `passlib[bcrypt]` |
| Frontend | React 18, TypeScript, Vite |
| Styling | Plain CSS |
| Testing | pytest, pytest-asyncio |
| Deployment | Docker + docker-compose |

---

## Quick Start (Docker)

**Prerequisite:** Docker Desktop running.

```bash
# 1. Copy env config — defaults work for local Docker
cp .env.example .env

# 2. Build and start all three services
docker compose up --build
```

| Service | URL |
|---|---|
| App (frontend) | http://localhost |
| API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

The backend automatically runs `alembic upgrade head` and seeds 30 puzzles (10 per difficulty) on first startup.

```bash
docker compose down      # stop; keep database volume
docker compose down -v   # stop and wipe database
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

# Install dependencies (including dev extras for tests)
pip install -e ".[dev]"

# Copy env config
cp .env.example .env

# Run migrations
alembic upgrade head

# Start the API server
uvicorn backend.main:app --reload
```

API at `http://localhost:8000` — interactive docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App at `http://localhost:5173`. The Vite dev server proxies `/api` and `/ws` to port 8000.

### Seed puzzle pool (optional)

```bash
python scripts/seed.py
```

Generates 10 puzzles per difficulty (idempotent — safe to run multiple times).

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest backend/tests/        # all 73 tests
pytest backend/tests/ -v     # verbose output
pytest backend/tests/ -x     # stop on first failure
```

### Test coverage

| Module | What is tested |
|---|---|
| `puzzle_generator` | Valid 9×9 board; correct solution; uniqueness check passes/fails |
| `elo_service` | Higher-rated winner gains less; lower-rated winner gains more; K=32 formula |
| `move_validator` | Correct cell accepted; wrong cell increments mistakes; duplicate/out-of-range rejected |
| `auth_service` | Duplicate username → 400; wrong password → 401 |
| `win_detection` | Filling all blank cells triggers win; fallback ranking by cells then mistakes |

All tests call services directly — no HTTP layer or mocking.

---

## Architecture

```
Browser (React)
    │
    ├── HTTP (REST)  ──────────> FastAPI ──> SQLAlchemy ──> PostgreSQL / SQLite
    │
    └── WebSocket ─────────────> FastAPI
                                    │
                           ConnectionManager
                           (match_id → [WebSocket, ...])
                                    │
                           Match Engine
                           - Move validation
                           - Win / elimination detection
                           - ELO calculation (pairwise round-robin)
                           - Result persistence (single DB transaction)
```

### Layer map

```
backend/
├── api/routes/        ← FastAPI routers (HTTP + WebSocket endpoints)
├── services/          ← Business logic (auth, match, ELO, puzzle, lobby)
├── models/            ← SQLAlchemy ORM models
├── schemas/           ← Pydantic request / response schemas
└── core/              ← Config, DB session, JWT utilities
```

No business logic lives in routers. Services are independently testable without an HTTP context.

---

## Folder Structure

```
Swordoku/
├── backend/
│   ├── main.py                    — FastAPI app, CORS, router registration, /health
│   ├── Dockerfile
│   ├── api/routes/
│   │   ├── auth.py                — /auth/register, /auth/login
│   │   ├── users.py               — /users/{username}, /users/{username}/matches
│   │   ├── puzzles.py             — POST /puzzles, GET /puzzles/{id}
│   │   ├── matches.py             — POST /matches
│   │   ├── lobbies.py             — /lobbies CRUD + /start
│   │   ├── leaderboard.py         — GET /leaderboard
│   │   └── ws.py                  — WS /ws/match/{match_id}
│   ├── core/
│   │   ├── config.py              — Settings (pydantic-settings)
│   │   ├── database.py            — Engine, SessionLocal, get_db dependency
│   │   └── security.py            — JWT encode / decode, password hashing
│   ├── models/
│   │   ├── user.py                — User
│   │   ├── puzzle.py              — Puzzle
│   │   ├── match.py               — Match, MatchParticipant
│   │   └── lobby.py               — Lobby, LobbyMember
│   ├── schemas/
│   │   ├── user.py                — UserCreate, UserOut, UserProfile, MatchHistoryEntry, LeaderboardEntry
│   │   ├── puzzle.py              — PuzzleOut
│   │   ├── match.py               — MatchCreate, MatchOut, WS broadcast schemas
│   │   └── lobby.py               — LobbyCreate, LobbyOut, LobbyStartOut
│   ├── services/
│   │   ├── auth_service.py        — register_user, login_user, get_current_user
│   │   ├── match_service.py       — create_match, get_match, get_participants
│   │   ├── lobby_service.py       — create_lobby, join_lobby, start_lobby
│   │   ├── connection_manager.py  — WebSocket pool (match_id → connections)
│   │   ├── move_validator.py      — process_move (validate cell against stored solution)
│   │   ├── win_detection.py       — has_won, finalize_match, ELO update
│   │   ├── elo_service.py         — calculate_elo (pure function, K=32)
│   │   ├── puzzle_generator.py    — generate_solved_grid, make_puzzle
│   │   └── difficulty_classifier.py — classify_difficulty
│   └── tests/
│       ├── conftest.py            — In-memory SQLite fixture
│       ├── test_auth_service.py
│       ├── test_elo_service.py
│       ├── test_move_validator.py
│       ├── test_puzzle_generator.py
│       └── test_win_detection.py
├── frontend/
│   ├── src/
│   │   ├── api.ts                 — Axios instance with JWT interceptor
│   │   ├── ws.ts                  — WebSocket utility (connect, send, onmessage)
│   │   ├── context/AuthContext.tsx — Token + currentUser, login/logout
│   │   ├── components/
│   │   │   ├── Layout.tsx         — Nav bar with auth links
│   │   │   ├── GameBoard.tsx      — Interactive 9×9 Sudoku grid
│   │   │   ├── OpponentPanel.tsx  — Live opponent progress cards
│   │   │   └── ProtectedRoute.tsx — Redirects to /login if unauthenticated
│   │   └── pages/
│   │       ├── Home.tsx           — Create / join lobby
│   │       ├── Login.tsx
│   │       ├── Register.tsx
│   │       ├── Lobby.tsx          — Waiting room, invite link, Start button
│   │       ├── Game.tsx           — Match page wiring board + WS + panel
│   │       ├── Profile.tsx        — Stats + match history
│   │       └── Leaderboard.tsx    — Global ELO ranking table
│   ├── Dockerfile
│   └── nginx.conf                 — Reverse proxy to backend for API + WS
├── alembic/                       — Migration scripts
├── scripts/
│   └── seed.py                    — Populate 30 puzzles (10 per difficulty)
├── docs/
│   ├── project-description.md
│   └── implementation-plan.md
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
└── .env.example
```

---

## Environment Variables

Copy `.env.example` to `.env` before running locally or in Docker.

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./swordoku.db` | SQLAlchemy connection string. Docker overrides this to the PostgreSQL URL automatically. |
| `SECRET_KEY` | `change-me-to-a-random-secret` | JWT signing secret. **Change before any shared deployment.** |
| `ALGORITHM` | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT lifetime in minutes. |
| `ENVIRONMENT` | `development` | Runtime environment label. |
| `FRONTEND_URL` | `http://localhost:5173` | Used for CORS allowed origin and lobby invite links. Docker sets this to `http://localhost`. |

Generate a secure `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## API Reference

All endpoints are relative to the base URL (e.g., `http://localhost:8000`).

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Register a new user. Body: `{username, email, password}`. Username: 1–32 chars, alphanumeric/`_`/`-`. Password: 8–72 chars. Returns `UserOut`. |
| `POST` | `/auth/login` | No | Login with form data `{username, password}`. Returns `{access_token, token_type}`. |

### Users

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/users/{username}` | Yes | Get profile: `{username, elo_rating, wins, losses}`. |
| `GET` | `/users/{username}/matches` | Yes | Paginated match history. Query: `?limit=20&offset=0` (limit max 100). |

### Puzzles

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/puzzles` | Yes | Generate and persist a puzzle. Query: `?difficulty=easy\|medium\|hard`. Returns `{id, difficulty, givens}` — solution is never exposed. |
| `GET` | `/puzzles/{id}` | Yes | Retrieve existing puzzle givens by ID. |

### Lobbies

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/lobbies` | Yes | Create a lobby. Body: `{mode, difficulty, time_limit_min?, mistake_limit?}`. Defaults: 10 min, 3 mistakes. Returns lobby with invite code and URL. |
| `GET` | `/lobbies/{code}` | Yes | Get lobby state: players, mode, difficulty, status. |
| `POST` | `/lobbies/{code}/join` | Yes | Join a lobby by its invite code. |
| `POST` | `/lobbies/{code}/start` | Yes | Creator only; generates a puzzle, creates the match, returns `{match_id}`. |

### Matches

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/matches` | Yes | Create a match record directly (used internally by lobby start). |

### Leaderboard

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/leaderboard` | No | Top players by ELO. Query: `?limit=50&offset=0` (limit 1–200). |

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | No | Returns `{"status": "ok"}`. Used by Docker health checks. |

### WebSocket

**Path:** `WS /ws/match/{match_id}`

The connection handshake is:
1. Server accepts the WebSocket connection.
2. Client sends `{"token": "<jwt>"}` as the first text message (within 10 s).
3. Server validates the token and match membership, then sends the initial `board_state` message.
4. Client sends move messages; server broadcasts updates to all participants.

#### Client → server messages

| Type | Fields | Description |
|---|---|---|
| *(auth, first message)* | `{token: string}` | JWT authentication. Must be sent immediately after connection. |
| `move` | `{type, cell: 0–80, value: 1–9}` | Submit a cell value. |
| `time_up` | `{type}` | Client signals that the timer has expired. Server validates elapsed time (10 s grace window) before finalising. |

#### Server → client messages

| Type | Fields | Description |
|---|---|---|
| `board_state` | `{givens, blank_count, board_state, mistakes, eliminated_user_ids, started_at, time_limit_s, mistake_limit, participants_state}` | Sent once on connect. Contains the puzzle, the player's current progress, and a snapshot of all opponents' state. |
| `move_result` | `{type, cell, correct}` | Sent only to the player who submitted the move. |
| `progress` | `{type, user_id, username, cells_correct, mistakes}` | Broadcast to all participants after every accepted move. |
| `player_eliminated` | `{type, user_id, username}` | Broadcast when a player's mistake count exceeds `mistake_limit`. |
| `match_end` | `{type, winner_id, reason, elo_deltas}` | Broadcast when the match resolves. `reason`: `completed`, `time_up`, or `mistake_limit`. `elo_deltas` is a `{user_id: delta}` map, present only for ranked matches. |
| `error` | `{type, detail}` | Sent to the client when a message is rejected (invalid format, eliminated player, etc.). |

---

## Data Model

### `users`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `username` | text | Unique, 1–32 chars, alphanumeric/`_`/`-` |
| `email` | text | Unique |
| `password_hash` | text | bcrypt |
| `elo_rating` | integer | Default 1200 |
| `wins` | integer | Default 0 |
| `losses` | integer | Default 0 |
| `created_at` | timestamp | |

### `puzzles`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `difficulty` | enum | `easy` / `medium` / `hard` |
| `givens` | JSON | 81-element array, 0 = empty cell |
| `solution` | JSON | Full solved grid — never sent to clients |
| `created_at` | timestamp | |

### `matches`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `puzzle_id` | UUID | FK → puzzles |
| `mode` | enum | `casual` / `ranked` |
| `status` | enum | `waiting` / `active` / `finished` |
| `time_limit_s` | integer | Default 600 (10 min) |
| `mistake_limit` | integer | Default 3; player eliminated when `mistakes > mistake_limit` |
| `started_at` | timestamp | |
| `ended_at` | timestamp | Null until resolved |
| `winner_id` | UUID | FK → users, null on draw |

### `match_participants`

| Field | Type | Notes |
|---|---|---|
| `match_id` | UUID | FK → matches (composite PK) |
| `user_id` | UUID | FK → users (composite PK) |
| `cells_correct` | integer | |
| `mistakes` | integer | |
| `board_state` | JSON | Player's current 81-element cell array |
| `solve_time_ms` | integer | Set only for the match winner |
| `elo_before` | integer | Null for casual matches |
| `elo_after` | integer | Null for casual matches |

### `lobbies`

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `code` | text (8 chars) | Unique invite code |
| `creator_id` | UUID | FK → users |
| `mode` | enum | `casual` / `ranked` |
| `difficulty` | enum | `easy` / `medium` / `hard` |
| `status` | enum | `waiting` / `active` |
| `match_id` | UUID | Set after start, FK → matches |
| `time_limit_min` | integer | Default 10, range 5–25 |
| `mistake_limit` | integer | Default 3, range 0–10 |

### `lobby_members`

| Field | Type | Notes |
|---|---|---|
| `lobby_id` | UUID | FK → lobbies (composite PK) |
| `user_id` | UUID | FK → users (composite PK) |
| `joined_at` | timestamp | |
