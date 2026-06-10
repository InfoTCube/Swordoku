from fastapi import FastAPI

from backend.api.routes.auth import router as auth_router

app = FastAPI(title="Swordoku")

app.include_router(auth_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
