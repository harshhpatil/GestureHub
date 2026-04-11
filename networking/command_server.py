from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

class CommandServer:

    def __init__(self):

        self.app = FastAPI()
        self.commands = []
        self.clients = []

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.post("/command")
        async def receive_command(data: dict):

            command = data.get("action")

            if command:
                self.commands.append(command)

                # broadcast to websocket clients
                disconnected = []
                for ws in self.clients:
                    try:
                        await ws.send_json({"action": command})
                    except:
                        disconnected.append(ws)
                
                # Remove disconnected clients
                for ws in disconnected:
                    if ws in self.clients:
                        self.clients.remove(ws)

            return {"status": "ok"}

        @self.app.get("/command")
        async def get_command():

            if self.commands:
                return {"action": self.commands.pop(0)}

            return {"action": None}

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):

            await websocket.accept()
            self.clients.append(websocket)

            try:
                while True:
                    await websocket.receive_text()
            except:
                if websocket in self.clients:
                    self.clients.remove(websocket)