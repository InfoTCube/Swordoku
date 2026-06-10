# Swordoku — Implementation Log

| # | Title | Status | Notes |
|---|---|---|---|
| 1 | Project scaffold | ✅ Done | Backend layout, pyproject.toml, .env.example, .gitignore, health endpoint, frontend placeholder |
| 2 | Database schema & Alembic | ✅ Done | SQLAlchemy models (User, Puzzle, Match, MatchParticipant), core/config.py, core/database.py, Alembic init + first migration |
| 3 | Auth endpoints | ✅ Done | POST /auth/register, POST /auth/login, get_current_user dep, UserCreate/UserOut/Token schemas, core/security.py JWT utils; bcrypt<4.0 pin for passlib compat |
| 4 | Sudoku generator | ✅ Done | generate_solved_grid, make_puzzle, has_unique_solution in services/puzzle_generator.py; MRV backtracker, unique-solution check |
| 5 | Difficulty classifier | ⬜ Todo | |
| 6 | Puzzle API endpoint | ⬜ Todo | |
| 7 | WebSocket connection manager | ⬜ Todo | |
| 8 | Match service & WS flow | ⬜ Todo | |
| 9 | Server-side move validation | ⬜ Todo | |
| 10 | Win detection & ELO update | ⬜ Todo | |
| 11 | Lobby service | ⬜ Todo | |
| 12 | React project scaffold | ⬜ Todo | |
| 13 | Auth pages | ⬜ Todo | |
| 14 | Home page | ⬜ Todo | |
| 15 | Lobby waiting room page | ⬜ Todo | |
| 16 | Game board component | ⬜ Todo | |
| 17 | Live opponent progress panel | ⬜ Todo | |
| 18 | WebSocket game client | ⬜ Todo | |
| 19 | Profile endpoint & page | ⬜ Todo | |
| 20 | Leaderboard endpoint & page | ⬜ Todo | |
| 21 | Unit test suite | ⬜ Todo | |
| 22 | Docker & docker-compose | ⬜ Todo | |
| 23 | Seed script & auto-migrations | ⬜ Todo | |
| 24 | README & documentation | ⬜ Todo | |
