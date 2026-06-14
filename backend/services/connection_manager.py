from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    async def connect(self, match_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active.setdefault(match_id, []).append(websocket)

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        conns = self.active.get(match_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active.pop(match_id, None)

    async def broadcast_to_match(self, match_id: str, message: dict) -> None:
        for websocket in list(self.active.get(match_id, [])):
            await websocket.send_json(message)

manager = ConnectionManager()