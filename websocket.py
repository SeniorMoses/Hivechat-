from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.connections: dict[int, WebSocket] = {}

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket,
    ):
        await websocket.accept()

        self.connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.connections.pop(user_id, None)

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections

    async def send_to_user(
        self,
        user_id: int,
        data: dict,
    ) -> bool:

        websocket = self.connections.get(user_id)

        if websocket is None:
            return False

        try:
            await websocket.send_json(data)
            return True

        except Exception:
            self.disconnect(user_id)
            return False


manager = ConnectionManager()