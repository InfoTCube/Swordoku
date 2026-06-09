from fastapi import FastAPI

app = FastAPI(title="Swordoku")


@app.get("/health")
async def health():
    return {"status": "ok"}
