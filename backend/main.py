from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.auth import router as auth_router
from backend.api.routes.leaderboard import router as leaderboard_router
from backend.api.routes.lobbies import router as lobbies_router
from backend.api.routes.matches import router as matches_router
from backend.api.routes.puzzles import router as puzzles_router
from backend.api.routes.users import router as users_router
from backend.api.routes.ws import router as ws_router
from backend.core.config import settings

app = FastAPI(title="Swordoku")

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
