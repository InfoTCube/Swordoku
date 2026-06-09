# Swordoku — Implementation Plan

## Overview

24 tasks across 6 milestones. Each task maps 1:1 to a GitHub issue. Dependency arrows mean "must be complete before starting".

---

## Dependency Graph

```
#1 Project scaffold
├── #2 DB schema & Alembic
│   ├── #3 Auth endpoints
│   │   ├── #11 Lobby service
│   │   │   ├── #14 Home page
│   │   │   │   └── #15 Lobby waiting room
│   │   │   │       ├── #16 Game board component ──┐
│   │   │   │       └── #17 Opponent panel ─────────┤
│   │   │   └── (also blocks #14, #15)              │
│   │   ├── #13 Auth pages                          │
│   │   │   └── (also blocks #14)                   │
│   │   └── #19 Profile endpoint & page             │
│   ├── #6 Puzzle API endpoint                      │
│   │   └── (blocks #8, #23)                        │
│   └── #20 Leaderboard endpoint & page             │
├── #4 Sudoku generator                             │
│   ├── #5 Difficulty classifier                    │
│   │   └── (blocks #6)                             │
│   └── (also blocks #6, #23)                       │
├── #7 WebSocket connection manager                 │
│   └── #8 Match service & WS flow                  │
│       ├── #9 Move validation                      │
│       │   └── #10 Win detection & ELO update      │
│       │       └── #21 Unit test suite             │
│       └── (also blocks #18) ◄─────────────────────┘
│                                  #18 WS game client
├── #12 React scaffold
│   ├── (blocks #13, #14, #15, #16, #17, #18, #19, #20)
└── #22 Docker & docker-compose
    ├── #23 Seed script & auto-migrations
    └── #24 README & documentation
```

---

## Tasks by Milestone

### Milestone 1 — Foundation

#### #1 · Project scaffold
**Labels:** `milestone-1` `backend`

Set up the complete folder structure and minimal runnable FastAPI app.

**Deliverables:**
- `backend/` with `api/`, `services/`, `models/`, `schemas/`, `core/` layout
- `frontend/` placeholder
- `pyproject.toml` (or `requirements.txt`) with core deps: fastapi, uvicorn, sqlalchemy, alembic, pydantic, python-jose, passlib
- `.env.example` listing all required env vars
- `main.py` — minimal FastAPI app that starts and returns 200 on `GET /health`
- `.gitignore` covering Python, Node, `.env`

**Blocks:** #2, #4, #7, #12, #22

---

#### #2 · Database schema & Alembic
**Labels:** `milestone-1` `backend`

Define all SQLAlchemy ORM models and configure Alembic for migrations.

**Deliverables:**
- Models: `User`, `Puzzle`, `Match`, `MatchParticipant`
- Alembic init + first migration generating all tables
- `get_db` session dependency for FastAPI
- `DATABASE_URL` env var; SQLite for dev, PostgreSQL for production

**Blocked by:** #1
**Blocks:** #3, #6, #8, #11, #20

---

#### #3 · Auth endpoints
**Labels:** `milestone-1` `backend`

Register, login, and JWT middleware.

**Deliverables:**
- `POST /auth/register` — validate uniqueness, bcrypt hash, return user schema
- `POST /auth/login` — verify credentials, return JWT access token
- `get_current_user` FastAPI dependency (decode JWT, load user)
- Pydantic schemas: `UserCreate`, `UserOut`, `Token`
- HTTP 400 on duplicate username/email, 401 on bad credentials

**Blocked by:** #1, #2
**Blocks:** #8, #11, #13, #19

---

### Milestone 2 — Puzzle Engine

#### #4 · Sudoku generator
**Labels:** `milestone-2` `backend`

Python backtracking generator producing valid, uniquely-solvable puzzles.

**Deliverables:**
- `generate_solved_grid()` — creates a complete 9×9 grid
- `make_puzzle(grid, difficulty)` — removes cells while preserving unique solution
- `has_unique_solution(givens)` — constraint-solving uniqueness check
- Returns `givens: list[int]` (81 elements, 0 = empty) and `solution: list[int]`
- All logic in `services/puzzle_generator.py` with no FastAPI dependency

**Blocked by:** #1
**Blocks:** #5, #6, #23

---

#### #5 · Difficulty classifier
**Labels:** `milestone-2` `backend`

Classify a puzzle as Easy / Medium / Hard based on solve-step analysis.

**Deliverables:**
- `classify_difficulty(givens) -> Difficulty` based on number of givens and naked/hidden single counts
- Returns `easy` / `medium` / `hard` enum value
- Used by the generator to produce puzzles at a target difficulty tier

**Blocked by:** #4
**Blocks:** #6

---

#### #6 · Puzzle API endpoint
**Labels:** `milestone-2` `backend`

REST endpoints to generate/persist a puzzle and retrieve its givens.

**Deliverables:**
- `POST /puzzles?difficulty=medium` — generate, persist, return `{id, difficulty, givens}` (solution never in response)
- `GET /puzzles/{id}` — return `{id, difficulty, givens}` for an existing puzzle
- Requires auth (`get_current_user`)

**Blocked by:** #2, #4, #5
**Blocks:** #8, #23

---

### Milestone 3 — Game Core

#### #7 · WebSocket connection manager
**Labels:** `milestone-3` `backend`

In-memory manager that maps `match_id` to active WebSocket connections.

**Deliverables:**
- `ConnectionManager` class: `connect`, `disconnect`, `broadcast_to_match`
- Asyncio-safe (no threading primitives needed, FastAPI is single-threaded async)
- WebSocket endpoint skeleton: `WS /ws/match/{match_id}` — connects and holds

**Blocked by:** #1
**Blocks:** #8

---

#### #8 · Match service & WebSocket flow
**Labels:** `milestone-3` `backend`

Core real-time match logic — create match from lobby, distribute puzzle, relay moves.

**Deliverables:**
- `POST /matches` — create match record (status=active), assign puzzle, return match ID
- On WS connect: send current board state to joining client
- Receive move message `{cell: int, value: int}` from client
- Validate move (via #9), update participant state, broadcast `{type: "progress", user_id, cells_correct, mistakes}` to all
- Broadcast `{type: "match_end", ...}` when match resolves

**Blocked by:** #2, #3, #6, #7
**Blocks:** #9, #18

---

#### #9 · Server-side move validation
**Labels:** `milestone-3` `backend`

Validate each submitted cell value against the stored solution.

**Deliverables:**
- `validate_move(puzzle_id, cell_index, value) -> bool` pure function
- Reject: already-filled cell, cell_index out of 0–80, value out of 1–9
- Increment `mistakes` counter on wrong value; `cells_correct` on right value
- Solution fetched from DB; never exposed to client

**Blocked by:** #8
**Blocks:** #10

---

#### #10 · Win detection & ELO update
**Labels:** `milestone-3` `backend`

Detect match completion, rank players, apply ELO, persist result atomically.

**Deliverables:**
- Trigger win when player reaches 81 `cells_correct`
- On time limit: rank by `cells_correct` desc, then `mistakes` asc
- `calculate_elo(rating_a, rating_b, result) -> (new_a, new_b)` pure function (K=32)
- Write `elo_before`, `elo_after` to `match_participants`
- Update `users.elo_rating`, `wins`, `losses` + set `matches.status/ended_at/winner_id` in a single DB transaction

**Blocked by:** #9
**Blocks:** #21

---

### Milestone 4 — Lobby & Frontend

#### #11 · Lobby service
**Labels:** `milestone-4` `backend`

Create, join, and start lobbies via invite codes.

**Deliverables:**
- `POST /lobbies` — create lobby (mode, difficulty), return `{id, code, invite_url}`
- `GET /lobbies/{code}` — return lobby state: players, mode, difficulty, status
- `POST /lobbies/{code}/join` — add `current_user` to lobby (up to max players)
- `POST /lobbies/{code}/start` — creator only; triggers `POST /matches` internally, returns `match_id`
- Lobby state can be stored as a DB table (`lobbies`, `lobby_members`) or in-memory dict

**Blocked by:** #2, #3
**Blocks:** #14, #15

---

#### #12 · React project scaffold
**Labels:** `milestone-4` `frontend`

Vite + React + TypeScript with routing, API client, and auth context.

**Deliverables:**
- Vite scaffold with React 18 + TypeScript
- React Router v6 with routes: `/`, `/login`, `/register`, `/lobby/:code`, `/game/:matchId`, `/profile/:username`, `/leaderboard`
- `api.ts` — Axios instance with base URL + JWT auth header injection
- `ws.ts` — WebSocket utility (connect, send, onmessage)
- `AuthContext` — stores token, exposes `login/logout/currentUser`
- `ProtectedRoute` component — redirects to `/login` if unauthenticated
- Basic `Layout` with nav links

**Blocked by:** #1
**Blocks:** #13, #14, #15, #16, #17, #18, #19, #20

---

#### #13 · Auth pages
**Labels:** `milestone-4` `frontend`

Register and login pages with form validation.

**Deliverables:**
- `/register` — form (username, email, password), client-side validation, calls `POST /auth/register`
- `/login` — form (username, password), calls `POST /auth/login`, stores token via `AuthContext`
- Redirect to `/` on success; display inline API error messages
- Link between the two pages

**Blocked by:** #3, #12
**Blocks:** #14

---

#### #14 · Home page
**Labels:** `milestone-4` `frontend`

Landing page for creating or joining a lobby.

**Deliverables:**
- "Create lobby" section — select mode (casual/ranked) + difficulty, calls `POST /lobbies`, redirects to `/lobby/:code`
- "Join lobby" section — input field for invite code/URL, redirects to `/lobby/:code`
- Requires auth (protected route)

**Blocked by:** #11, #12, #13
**Blocks:** #15

---

#### #15 · Lobby waiting room page
**Labels:** `milestone-4` `frontend`

Waiting room at `/lobby/:code`.

**Deliverables:**
- Polls `GET /lobbies/{code}` every 2 s to refresh player list
- Shows: lobby mode, difficulty, joined players, copy-invite-link button
- "Start game" button visible to creator only; calls `POST /lobbies/{code}/start`
- On start: redirects all clients to `/game/:matchId` (received from start response)
- Minimum-player-count guard before enabling start button

**Blocked by:** #11, #12, #14
**Blocks:** #16, #17

---

#### #16 · Game board component
**Labels:** `milestone-4` `frontend`

Interactive 9×9 Sudoku grid.

**Deliverables:**
- Renders 81 cells with correct 3×3 box borders
- Given cells: read-only, visually distinct (e.g. bold / grey background)
- Player-input cells: keyboard 1–9 to enter, Backspace to erase
- Highlights conflicts in same row/col/box
- Marks incorrect cells in red on server validation response
- Exports `onCellChange(cell: number, value: number)` callback for WS integration

**Blocked by:** #12, #15
**Blocks:** #18

---

#### #17 · Live opponent progress panel
**Labels:** `milestone-4` `frontend`

Panel showing all opponents' real-time progress.

**Deliverables:**
- List entry per opponent: username, cells filled / 81, mistake count
- Simple progress bar
- Data updated on each `progress` WebSocket broadcast
- Shows "Finished!" badge when opponent completes

**Blocked by:** #12, #15
**Blocks:** #18

---

#### #18 · WebSocket game client integration
**Labels:** `milestone-4` `frontend`

Wire the game page together: board + opponent panel + WebSocket.

**Deliverables:**
- Connect to `WS /ws/match/{matchId}` on `/game/:matchId` mount; disconnect on unmount
- Send `{cell, value}` on `onCellChange`
- Dispatch `progress` messages to opponent panel state
- Dispatch `match_end` message → show result overlay (Win / Lose / Draw, ELO delta for ranked)
- Timer countdown display
- Handle WS disconnect: show reconnecting indicator

**Blocked by:** #8, #16, #17

---

### Milestone 5 — Profile & Leaderboard

#### #19 · Profile endpoint & page
**Labels:** `milestone-5` `backend` `frontend`

Player profile — backend REST + React page.

**Deliverables:**
- `GET /users/{username}` — return `{username, elo_rating, wins, losses}`
- React `/profile/:username` — displays the above stats
- Link to own profile in nav bar

**Blocked by:** #3, #12

---

#### #20 · Leaderboard endpoint & page
**Labels:** `milestone-5` `backend` `frontend`

Global ELO leaderboard — backend REST + React page.

**Deliverables:**
- `GET /leaderboard?limit=50` — top N players ordered by `elo_rating` desc; returns `[{rank, username, elo_rating, wins, losses}]`
- React `/leaderboard` — table with rank, username (links to profile), ELO, W/L

**Blocked by:** #2, #12

---

### Milestone 6 — Tests & Deployment

#### #21 · Unit test suite
**Labels:** `milestone-6` `backend`

pytest coverage for all business logic.

**Test targets:**

| Module | Cases |
|---|---|
| `puzzle_generator` | Generated board is valid 9×9; solution is correct; uniqueness check passes/fails correctly |
| `elo_service` | Higher-rated winner gains less; lower-rated winner gains more; K=32 formula |
| `move_validator` | Correct cell accepted; wrong cell increments mistakes; duplicate cell rejected; out-of-range rejected |
| `auth_service` | Duplicate username → 400; wrong password → 401 |
| `win_detection` | All 81 correct triggers win; fallback rank by cells then mistakes |

All tests hit services directly, no HTTP layer.

**Blocked by:** #3, #4, #9, #10

---

#### #22 · Docker & docker-compose
**Labels:** `milestone-6` `backend`

Containerise the full stack.

**Deliverables:**
- `backend/Dockerfile` — Python 3.11-slim, install deps, run Uvicorn
- `frontend/Dockerfile` — Node build stage → nginx serve stage
- `docker-compose.yml` — services: `backend`, `frontend`, `db` (postgres:16)
- Env var wiring via `.env` file
- Health check on `backend` service
- `docker-compose up --build` brings the full app up

**Blocked by:** #1
**Blocks:** #23, #24

---

#### #23 · Seed script & auto-migrations
**Labels:** `milestone-6` `backend`

Run migrations on startup and populate an initial puzzle pool.

**Deliverables:**
- Backend startup runs `alembic upgrade head` before accepting requests
- `scripts/seed.py` generates and inserts 10 puzzles per difficulty (30 total)
- Seed is idempotent (checks for existing puzzles before inserting)
- Called from `docker-compose` via a one-shot init container or backend startup hook

**Blocked by:** #22, #4, #6

---

#### #24 · README & documentation
**Labels:** `milestone-6`

Technical and user documentation in `README.md`.

**Deliverables:**
- Project overview and feature list
- Architecture diagram (text)
- Folder structure explanation
- Local dev setup (with and without Docker)
- Environment variables reference table
- `docker-compose up --build` quickstart
- How to run tests: `pytest backend/tests/`
- API endpoint reference (method, path, auth required, brief description)

**Blocked by:** #22

---

## Summary Table

| # | Title | Milestone | Blocked by | Blocks |
|---|---|---|---|---|
| 1 | Project scaffold | M1 | — | 2, 4, 7, 12, 22 |
| 2 | Database schema & Alembic | M1 | 1 | 3, 6, 8, 11, 20 |
| 3 | Auth endpoints | M1 | 1, 2 | 8, 11, 13, 19 |
| 4 | Sudoku generator | M2 | 1 | 5, 6, 23 |
| 5 | Difficulty classifier | M2 | 4 | 6 |
| 6 | Puzzle API endpoint | M2 | 2, 4, 5 | 8, 23 |
| 7 | WebSocket connection manager | M3 | 1 | 8 |
| 8 | Match service & WS flow | M3 | 2, 3, 6, 7 | 9, 18 |
| 9 | Server-side move validation | M3 | 8 | 10 |
| 10 | Win detection & ELO update | M3 | 9 | 21 |
| 11 | Lobby service | M4 | 2, 3 | 14, 15 |
| 12 | React project scaffold | M4 | 1 | 13, 14, 15, 16, 17, 18, 19, 20 |
| 13 | Auth pages | M4 | 3, 12 | 14 |
| 14 | Home page | M4 | 11, 12, 13 | 15 |
| 15 | Lobby waiting room page | M4 | 11, 12, 14 | 16, 17 |
| 16 | Game board component | M4 | 12, 15 | 18 |
| 17 | Live opponent progress panel | M4 | 12, 15 | 18 |
| 18 | WebSocket game client | M4 | 8, 16, 17 | — |
| 19 | Profile endpoint & page | M5 | 3, 12 | — |
| 20 | Leaderboard endpoint & page | M5 | 2, 12 | — |
| 21 | Unit test suite | M6 | 3, 4, 9, 10 | — |
| 22 | Docker & docker-compose | M6 | 1 | 23, 24 |
| 23 | Seed script & auto-migrations | M6 | 22, 4, 6 | — |
| 24 | README & documentation | M6 | 22 | — |
