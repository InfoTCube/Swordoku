from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

    def add_connection(self, match_id: str, websocket: WebSocket) -> None:
        self.active.setdefault(match_id, []).append(websocket)

    def disconnect(self, match_id: str, websocket: WebSocket) -> None:
        conns = self.active.get(match_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self.active.pop(match_id, None)

    async def close_match_connections(self, match_id: str) -> None:
        """Send a normal close frame to every socket for this match then remove them."""
        for websocket in list(self.active.get(match_id, [])):
            try:
                await websocket.close(code=1000)
            except Exception:
                pass
        self.active.pop(match_id, None)

    async def broadcast_to_match(self, match_id: str, message: dict) -> None:
        for websocket in list(self.active.get(match_id, [])):
            try:
                await websocket.send_json(message)
            except Exception:
                self.disconnect(match_id, websocket)

manager = ConnectionManager()