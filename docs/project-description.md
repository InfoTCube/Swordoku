# Swordoku — Competitive Online Sudoku Platform

## Project Overview

Swordoku is a web-based competitive multiplayer Sudoku platform where players race to solve the same puzzle simultaneously. It combines the classic logic puzzle with real-time competitive gameplay, an ELO-based rating system, player profiles, and a global leaderboard.

The core concept: Sudoku is already a race against yourself — Swordoku makes it a race against someone else. The moment an opponent's cell count ticks up on your screen, the puzzle becomes urgent.

**Context**: This is a university course project ("Języki skryptowe"). The scope below reflects the MVP required for that submission — production-scale concerns (Redis, Celery, horizontal scaling) are noted in the Future section but are explicitly out of scope.

---

## MVP Scope

### User Auth
- Register and login with username + password.
- JWT-based session (access token stored client-side).
- Passwords hashed with bcrypt.

### Lobby System
- Any logged-in player can create a lobby (casual or ranked mode).
- Creator receives a shareable invite link.
- Other players join via that link.
- Match starts when the creator clicks "Start" (minimum 2 players).
- No queue-based matchmaking in MVP — lobby + invite link only.

### Puzzle Generation
- Puzzles generated on demand using a Python backtracking algorithm.
- Every puzzle guaranteed to have a unique solution.
- Difficulty levels: Easy, Medium, Hard.
- The solution is stored server-side and **never sent to the client**.

### Real-Time Match (WebSockets)
- All players in a lobby receive the same puzzle at match start.
- Each player's moves are validated server-side on submission.
- Opponent progress (cells filled, mistake count) is broadcast live to all participants.
- In-memory connection manager (dict keyed by match ID) — single-server, no Redis needed at this scale.

### Win Condition
- First player to correctly complete the puzzle wins.
- If a time limit is reached with no completion, winner is determined by:
  1. Most correctly filled cells.
  2. Fewest mistakes (tiebreaker).

### ELO Rating
- Every registered player starts at ELO 1200.
- After each **ranked** match, ratings are updated using the standard ELO formula.
- ELO update and match result are written in a single database transaction.
- Casual matches have no ELO impact.

### Player Profile
- Username, ELO rating, win/loss record.
- Visible to all logged-in users.

### Global Leaderboard
- Top players ranked by ELO rating.

---

## Technical Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI |
| Real-time | WebSockets (FastAPI / Starlette) |
| Database | PostgreSQL (SQLite for local dev) |
| ORM / migrations | SQLAlchemy + Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (`python-jose`) |
| Password hashing | `passlib[bcrypt]` |
| Puzzle generation | Custom Python (backtracking) |
| Frontend | React (TypeScript) |
| Testing | pytest, pytest-asyncio |
| Deployment | Docker + docker-compose |

---

## Architecture

```
Browser (React)
    |
    |-- HTTP (REST)  ──────────────> FastAPI ──> SQLAlchemy ──> PostgreSQL
    |
    |-- WebSocket ─────────────────> FastAPI
                                        |
                               In-memory ConnectionManager
                               (match_id → [WebSocket, ...])
                                        |
                               Match Engine (Python)
                               - Move validation
                               - Win detection
                               - ELO calculation
                               - Result persistence
```

### Layering

```
api/          ← FastAPI routers (HTTP + WebSocket endpoints)
services/     ← Business logic: auth, match, ELO, puzzle, lobby
models/       ← SQLAlchemy ORM models
schemas/      ← Pydantic request/response schemas
core/         ← Config, DB session, JWT utils
```

No business logic lives in routers. Services are independently testable without HTTP context.

### Key Backend Modules

- **auth service**: Register, login, JWT issuance and verification.
- **lobby service**: Create lobby, generate invite token, join by token, track lobby state.
- **puzzle service**: Generate a valid Sudoku grid at requested difficulty; expose givens to clients, keep solution in DB.
- **match service**: Distribute puzzle on match start, receive and validate moves via WebSocket, detect win/draw, persist result.
- **elo service**: Pure-function ELO calculation — easy to unit test, called by match service on ranked match end.

### Frontend Pages

- **Auth**: Register / login forms.
- **Home**: Create lobby or join via link.
- **Lobby**: Waiting room — shows joined players, start button for creator.
- **Game**: Interactive 9×9 board, live opponent progress panel, timer.
- **Profile**: Username, ELO, win/loss record.
- **Leaderboard**: Global ELO ranking table.

---

## Data Model

### `users`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| username | text | Unique |
| email | text | Unique |
| password_hash | text | bcrypt |
| elo_rating | integer | Default 1200 |
| wins | integer | Default 0 |
| losses | integer | Default 0 |
| created_at | timestamp | |

### `puzzles`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| difficulty | enum | easy / medium / hard |
| givens | jsonb | Initial cell values (81-element array, 0 = empty) |
| solution | jsonb | Full solved grid — never sent to clients |
| created_at | timestamp | |

### `matches`
| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| puzzle_id | UUID | FK → puzzles |
| mode | enum | casual / ranked |
| status | enum | waiting / active / finished |
| started_at | timestamp | |
| ended_at | timestamp | Null until resolved |
| winner_id | UUID | FK → users, nullable |

### `match_participants`
| Field | Type | Notes |
|---|---|---|
| match_id | UUID | FK → matches |
| user_id | UUID | FK → users |
| cells_correct | integer | |
| mistakes | integer | |
| solve_time_ms | integer | Null if not finished |
| elo_before | integer | Null for casual |
| elo_after | integer | Null for casual |

---

## Tests

Covered by `pytest` + `pytest-asyncio`:

| Area | What to test |
|---|---|
| Puzzle validator | Valid/invalid boards, uniqueness check, edge cases |
| ELO calculator | Expected gain/loss for various rating differences, edge cases |
| Move validation | Correct cell, wrong cell, out-of-bounds, already-filled cell |
| Auth | Register duplicate username/email, login with wrong password |
| Win detection | First-to-finish path, fallback ranking by cells/mistakes |

UI is not tested. All testable logic lives in `services/`, not in routers.

---

## Deployment

Single `docker-compose.yml` spins up:
- `backend` — FastAPI app (Uvicorn)
- `frontend` — React app (nginx)
- `db` — PostgreSQL

```bash
docker-compose up --build
```

Alembic migrations run automatically on backend startup. A seed script pre-populates a small puzzle pool for dev/demo use.

---

## Milestones

| # | Milestone | Deliverable |
|---|---|---|
| 1 | Foundation | Project scaffold, DB schema, Alembic, auth endpoints (register/login), Pydantic schemas, basic error handling |
| 2 | Puzzle engine | Backtracking generator, uniqueness validator, difficulty classification, REST endpoint to fetch a puzzle |
| 3 | Game core | WebSocket match session, move validation, win detection, ELO update, result persistence |
| 4 | Lobby & frontend | Lobby create/join flow, full React UI (auth, lobby, game board, live opponent panel) |
| 5 | Profile & leaderboard | Profile page, global ELO leaderboard, match result display |
| 6 | Tests & deployment | pytest suite (puzzle, ELO, validation, auth), Docker + docker-compose, README |

---

## Out of Scope (Future Considerations)

- **Queue-based ranked matchmaking** — ELO-based pairing without needing a friend to play against.
- **Redis + horizontal scaling** — required if running multiple backend workers; not needed for single-server deployment.
- **Match history page** — list of past matches with results.
- **Rating history chart** — ELO over time on the profile page.
- **Friends / friends leaderboard** — social layer.
- **Spectator mode** — watch live matches.
- **Bot opponents** — for when no human opponent is available.
- **Glicko-2 / TrueSkill** — more accurate rating model accounting for puzzle variance; standard ELO is sufficient for MVP.
- **Anti-cheat** — speed anomaly detection for abnormally fast solves.
- **Tournament brackets** — single-elimination or Swiss format.
