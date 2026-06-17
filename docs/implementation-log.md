# Swordoku — Implementation Log

| # | Title | Status | Notes |
|---|---|---|---|
| 1 | Project scaffold | ✅ Done | Backend layout, pyproject.toml, .env.example, .gitignore, health endpoint, frontend placeholder |
| 2 | Database schema & Alembic | ✅ Done | SQLAlchemy models (User, Puzzle, Match, MatchParticipant), core/config.py, core/database.py, Alembic init + first migration |
| 3 | Auth endpoints | ✅ Done | POST /auth/register, POST /auth/login, get_current_user dep, UserCreate/UserOut/Token schemas, core/security.py JWT utils; bcrypt<4.0 pin for passlib compat |
| 4 | Sudoku generator | ✅ Done | generate_solved_grid, make_puzzle, has_unique_solution in services/puzzle_generator.py; MRV backtracker, unique-solution check |
| 5 | Difficulty classifier | ✅ Done | classify_difficulty in services/difficulty_classifier.py; naked/hidden singles simulation, inline candidate updates after each hidden single placement, thresholds aligned with generator ranges |
| 6 | Puzzle API endpoint | ✅ Done | POST /puzzles?difficulty=, GET /puzzles/{id}, PuzzleOut schema (no solution), auth required; actual difficulty re-classified from carved givens |
| 7 | WebSocket connection manager | ✅ Done | ConnectionManager (connect/disconnect/broadcast_to_match), module-level singleton, WS /ws/match/{match_id} skeleton |
| 8 | Match service & WS flow | ✅ Done | POST /matches (auth required, puzzle existence check), WS /ws/match/{match_id} (token query param auth, board_state on connect, move relay + progress broadcast) |
| 9 | Server-side move validation | ✅ Done | validate_move pure fn + process_move in services/move_validator.py; board_state JSON col on MatchParticipant; rejects given_cell/already_filled; increments cells_correct or mistakes; wired into WS handler |
| 10 | Win detection & ELO update | ✅ Done | services/elo_service.py (calculate_elo, K=32, pure fn), services/win_detection.py (has_won at 81 cells_correct, rank_participants/determine_winner by cells_correct desc then mistakes asc, finalize_match persisting match status/ended_at/winner_id + user elo/wins/losses in one transaction); ranked matches with >2 participants use round-robin pairwise ELO averaged per player; wired into ws.py to trigger on win and broadcast existing MatchEndBroadcast schema; match_service.get_participants helper added |
| 11 | Lobby service | ✅ Done | POST /lobbies, GET /lobbies/{code}, POST /lobbies/{code}/join, POST /lobbies/{code}/start; models Lobby+LobbyMember; services/lobby_service.py; api/routes/lobbies.py; alembic migration also backfills missing board_state column on match_participants |
| 12 | React project scaffold | ✅ Done | Vite + React 18 + TypeScript; React Router v6 with all routes (/,/login,/register,/lobby/:code,/game/:matchId,/profile/:username,/leaderboard); api.ts (Axios + JWT interceptor); ws.ts (WebSocket utility); AuthContext (token + currentUser in localStorage, login/logout); ProtectedRoute; Layout with nav; dev-server proxy to FastAPI :8000 |
| 13 | Auth pages | ✅ Done | /register (username+email+password, client validation, auto-login on success); /login (username+password, form-data to OAuth2 endpoint); inline API error display; redirect to / on success; links between pages; auth-* CSS classes in index.css |
| 14 | Home page | ✅ Done | Two-card layout: "Create lobby" (mode + difficulty radio groups → POST /lobbies → redirect /lobby/:code) and "Join lobby" (code/URL input → redirect /lobby/:code); home-* CSS classes in index.css; ProtectedRoute already guards the route |
| 15 | Lobby waiting room page | ✅ Done | Polls GET /lobbies/{code} every 2s; auto-joins on mount; shows mode/difficulty/players/invite link (copy button); Start button for creator only (2+ players); redirects all clients to /game/:matchId when lobby goes active; FRONTEND_URL config added so invite_url points to the app |
| 16 | Game board component | ⬜ Todo | |
| 17 | Live opponent progress panel | ⬜ Todo | |
| 18 | WebSocket game client | ⬜ Todo | |
| 19 | Profile endpoint & page | ⬜ Todo | |
| 20 | Leaderboard endpoint & page | ⬜ Todo | |
| 21 | Unit test suite | ✅ Done | pytest suite in backend/tests/; 73 tests across 5 modules (puzzle_generator, elo_service, move_validator, auth_service, win_detection); in-memory SQLite fixture in conftest.py; [tool.pytest.ini_options] added to pyproject.toml |
| 22 | Docker & docker-compose | ✅ Done | backend/Dockerfile (python:3.11-slim, alembic upgrade head on startup), frontend/Dockerfile (multi-stage node→nginx, custom nginx.conf with API+WS proxy), docker-compose.yml (postgres:16 with healthcheck chain, pgdata volume, DATABASE_URL auto-overridden) |
| 23 | Seed script & auto-migrations | ⬜ Todo | |
| 24 | README & documentation | ⬜ Todo | |
