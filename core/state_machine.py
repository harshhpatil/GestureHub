import time


class StateMachine:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.state = "MENU"
        self.palm_start_time = None
        self.PALM_HOLD_TIME = 1.2
        
        # Top-level menu items
        self.top_menu_items = ["music", "drawing", "system", "games"]
        self.game_menu_items = ["dino", "catch", "fruit"]
        self.music_menu_items = ["local", "spotify"]
        self.spotify_devices = []  # Will be populated dynamically
        self.menu_index = 0
        
        # For backward compatibility
        self.menu_items = self.top_menu_items

    def handle_commands(self, commands):
        for command in commands:
            if self.state == "IDLE":
                self.handle_idle(command)
            elif self.state == "MENU":
                self.handle_menu(command)
            elif self.state == "GAME_MENU":
                self.handle_game_menu(command)
            elif self.state == "MUSIC_MENU":
                self.handle_music_menu(command)
            elif self.state == "SPOTIFY_DEVICE_MENU":
                self.handle_spotify_device_menu(command)

    def handle_idle(self, command):

        if command == "RESET":
            if self.palm_start_time is None:
                self.palm_start_time = time.time()

            hold_time = time.time() - self.palm_start_time

            if hold_time >= self.PALM_HOLD_TIME:
                print("ENTERING MENU")
                self.state = "MENU"
                self.palm_start_time = None

            return

        else:
            self.palm_start_time = None

        self.dispatcher.dispatch(command, from_server=False)

    def handle_menu(self, command):
        """Handle navigation and selection in top-level menu."""
        if command == "NEXT_TRACK":
            self.menu_index = (self.menu_index + 1) % len(self.top_menu_items)
            print("MENU →", self.top_menu_items[self.menu_index])

        elif command == "PREV_TRACK":
            self.menu_index = (self.menu_index - 1) % len(self.top_menu_items)
            print("MENU →", self.top_menu_items[self.menu_index])

        elif command == "PINCH":
            selected = self.top_menu_items[self.menu_index]
            print("SELECTED:", selected)

            if selected == "music":
                # Transition to music submenu
                self.state = "MUSIC_MENU"
                self.menu_index = 0
                print("ENTERING MUSIC MENU")
            elif selected == "drawing":
                self.dispatcher.dispatch("MODE_DRAWING")
                self.state = "IDLE"
                self.menu_index = 0
            elif selected == "system":
                self.dispatcher.dispatch("MODE_SYSTEM")
                self.state = "IDLE"
                self.menu_index = 0
            elif selected == "games":
                # Transition to game submenu
                self.state = "GAME_MENU"
                self.menu_index = 0
                print("ENTERING GAME MENU")

    def handle_game_menu(self, command):
        """Handle navigation and selection in game submenu."""
        if command == "RESET":
            self.state = "MENU"
            self.menu_index = 0
            print("BACK TO MENU")

        elif command == "NEXT_TRACK":
            self.menu_index = (self.menu_index + 1) % len(self.game_menu_items)
            print("GAME MENU →", self.game_menu_items[self.menu_index])

        elif command == "PREV_TRACK":
            self.menu_index = (self.menu_index - 1) % len(self.game_menu_items)
            print("GAME MENU →", self.game_menu_items[self.menu_index])

        elif command == "PINCH":
            selected = self.game_menu_items[self.menu_index]
            print("SELECTED GAME:", selected)

            if selected == "dino":
                self.dispatcher.dispatch("MODE_DINO")
            elif selected == "catch":
                self.dispatcher.dispatch("MODE_CATCH")
            elif selected == "fruit":
                self.dispatcher.dispatch("MODE_FRUIT")

            self.state = "IDLE"
            self.menu_index = 0

    def get_state(self):
        return self.state

    def get_menu_index(self):
        return self.menu_index
    
    def handle_music_menu(self, command):
        """Handle navigation and selection in music submenu."""
        if command == "RESET":
            self.state = "MENU"
            self.menu_index = 0
            print("BACK TO MENU")

        elif command == "NEXT_TRACK":
            self.menu_index = (self.menu_index + 1) % len(self.music_menu_items)
            print("MUSIC MENU →", self.music_menu_items[self.menu_index])

        elif command == "PREV_TRACK":
            self.menu_index = (self.menu_index - 1) % len(self.music_menu_items)
            print("MUSIC MENU →", self.music_menu_items[self.menu_index])

        elif command == "PINCH":
            selected = self.music_menu_items[self.menu_index]
            print("SELECTED MUSIC MODE:", selected)

            if selected == "local":
                self.dispatcher.dispatch("MODE_MUSIC_LOCAL")
                self.state = "IDLE"
                self.menu_index = 0
            elif selected == "spotify":
                # Fetch devices and transition to device menu
                self.dispatcher.dispatch("FETCH_SPOTIFY_DEVICES")
                if self.spotify_devices:
                    self.state = "SPOTIFY_DEVICE_MENU"
                    self.menu_index = 0
                    print("ENTERING SPOTIFY DEVICE MENU")
                else:
                    print("No Spotify devices found. Open Spotify and try again.")

    def handle_spotify_device_menu(self, command):
        """Handle navigation and selection in Spotify device menu."""
        if command == "RESET":
            self.state = "MUSIC_MENU"
            self.menu_index = 0
            print("BACK TO MUSIC MENU")
            return

        if not self.spotify_devices:
            print("No Spotify devices available!")
            return

        if command == "NEXT_TRACK":
            self.menu_index = (self.menu_index + 1) % len(self.spotify_devices)
            print("SPOTIFY DEVICE →", self.spotify_devices[self.menu_index])

        elif command == "PREV_TRACK":
            self.menu_index = (self.menu_index - 1) % len(self.spotify_devices)
            print("SPOTIFY DEVICE →", self.spotify_devices[self.menu_index])

        elif command == "PINCH":
            selected_device = self.spotify_devices[self.menu_index]
            print("SELECTED DEVICE:", selected_device)
            self.dispatcher.dispatch(f"SELECT_SPOTIFY_DEVICE:{self.menu_index}")
            self.dispatcher.dispatch("MODE_MUSIC_SPOTIFY")
            self.state = "IDLE"
            self.menu_index = 0

    def set_spotify_devices(self, devices):
        """Update available Spotify devices (called by dispatcher)."""
        self.spotify_devices = devices
        print(f"Spotify devices updated: {len(devices)} found")

    def get_current_menu_items(self):
        """Return menu items for current state."""
        if self.state == "MENU":
            return self.top_menu_items
        elif self.state == "GAME_MENU":
            return self.game_menu_items
        elif self.state == "MUSIC_MENU":
            return self.music_menu_items
        elif self.state == "SPOTIFY_DEVICE_MENU":
            return self.spotify_devices
        return []
