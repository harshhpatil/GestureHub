import requests
import time


class ServerListener:

    def __init__(self, dispatcher):

        self.dispatcher = dispatcher
        self.url = "http://localhost:8000/command"
        self.from_server = True  # Flag to prevent feedback loop

    def start(self):

        print("Server listener started")

        while True:

            try:
                r = requests.get(self.url).json()

                command = r.get("action")

                if command:
                    if self.dispatcher.is_recent_local_echo(command):
                        # Skip local echo to prevent duplicate execution (toggle/pause conflicts)
                        continue
                    print("SERVER COMMAND:", command)
                    # Dispatch with from_server=True to prevent POST back to server
                    self.dispatcher.dispatch(command, from_server=True)

            except:
                pass

            time.sleep(0.2)