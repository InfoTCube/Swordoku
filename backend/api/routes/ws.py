from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.services.connection_manager import manager

router = APIRouter()

@router.websocket("/ws/match/{match_id}")
async def match_ws(match_id: str, websocket: WebSocket) -> None:
    await manager.connect(match_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # We have to handle data later in next PR
    except WebSocketDisconnect:
        manager.disconnect(match_id, websocket)