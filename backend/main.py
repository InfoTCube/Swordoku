import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.auth import router as auth_router
from backend.api.routes.leaderboard import router as leaderboard_router
from backend.api.routes.lobbies import router as lobbies_router
from backend.api.routes.matches import router as matches_router
from backend.api.routes.puzzles import router as puzzles_router
from backend.api.routes.users import router as users_router
from backend.api.routes.ws import expire_match, router as ws_router
from backend.core.config import settings
from backend.core.database import SessionLocal
from backend.models.match import Match

logger = logging.getLogger(__name__)


async def _expire_matches_loop() -> None:
    """Every 60 s: finalize any active match whose time limit has elapsed.

    Handles the case where all players disconnected before sending time_up,
    so the server would otherwise keep the match open forever.
    """
    while True:
        await asyncio.sleep(60)
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)
            active_matches = db.query(Match).filter(Match.status == "active").all()
            for match in active_matches:
                if match.started_at is None:
                    continue
                started = match.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                if (now - started).total_seconds() < match.time_limit_s:
                    continue
                try:
                    await expire_match(db, match)
                except Exception:
                    logger.exception("Failed to expire match %s", match.id)
        except Exception:
            logger.exception("Error in match expiry loop")
        finally:
            db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_expire_matches_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Swordoku", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(leaderboard_router)
app.include_router(lobbies_router)
app.include_router(matches_router)
app.include_router(puzzles_router)
app.include_router(users_router)
app.include_router(ws_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
