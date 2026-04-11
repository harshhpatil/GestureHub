import requests
import time
import threading
from collections import deque


class CommandDispatcher:

    def __init__(self):

        self.router = None
        self.server_url = "http://localhost:8000/command"
        self._recent_local = deque(maxlen=40)
        self._echo_window_sec = 1.2

    def register_router(self, router):

        self.router = router

    def _send_to_server_async(self, command):
        """Non-blocking HTTP request to server (runs in background thread)."""
        try:
            requests.post(self.server_url, json={"action": command}, timeout=2)
        except Exception as e:
            # Silent fail - don't spam console with network warnings
            pass

    def dispatch(self, command, from_server=False):

        print("COMMAND:", command)

        # Send command to router (ModeManager) - SYNCHRONOUS (main thread)
        if self.router:
            self.router.handle_command(command)

        # Send to server if local - ASYNCHRONOUS (background thread, non-blocking)
        if not from_server:
            # Track local commands so server echoes can be ignored safely
            self._recent_local.append((command, time.time()))
            # Start background thread for network I/O (non-blocking)
            thread = threading.Thread(target=self._send_to_server_async, args=(command,), daemon=True)
            thread.start()

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