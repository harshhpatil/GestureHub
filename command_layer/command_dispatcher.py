import requests
import time
from collections import deque


class CommandDispatcher:

    def __init__(self):

        self.router = None
        self.server_url = "http://localhost:8000/command"
        self._recent_local = deque(maxlen=40)
        self._echo_window_sec = 1.2

    def register_router(self, router):

        self.router = router

    def dispatch(self, command, from_server=False):

        print("COMMAND:", command)

        # Send command to router (ModeManager)
        if self.router:
            self.router.handle_command(command)

        # Send to server if local
        if not from_server:
            # Track local commands so server echoes can be ignored safely
            self._recent_local.append((command, time.time()))
            try:
                requests.post(self.server_url, json={"action": command}, timeout=2)
            except Exception as e:
                print("Warning: Could not send command to server", e)
                pass

    def is_recent_local_echo(self, command):
        """Return True if command was just sent locally and likely came back from server queue."""
        now = time.time()
        # prune old entries
        while self._recent_local and (now - self._recent_local[0][1]) > self._echo_window_sec:
            self._recent_local.popleft()

        for cmd, ts in reversed(self._recent_local):
            if cmd == command and (now - ts) <= self._echo_window_sec:
                return True
        return False