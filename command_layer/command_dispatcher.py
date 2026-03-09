import requests


class CommandDispatcher:

    def __init__(self):

        self.router = None
        self.server_url = "http://localhost:8000/command"

    def register_router(self, router):

        self.router = router

    def dispatch(self, command, from_server=False):

        print("COMMAND:", command)

        # Send command to router (ModeManager)
        if self.router:
            self.router.handle_command(command)

        # Send to server if local
        if not from_server:
            try:
                requests.post(self.server_url, json={"action": command}, timeout=2)
            except Exception as e:
                print("Warning: Could not send command to server", e)
                pass