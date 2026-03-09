import cv2


class ModeManager:
    def __init__(self):
        self.modules = {}
        self.active_mode = None  # No module active until menu selection
        self.state_machine = None

    def set_state_machine(self, state_machine):
        """Attach state machine reference for menu data updates."""
        self.state_machine = state_machine

    def register(self, name, module):
        """Register a module without activating it."""
        self.modules[name] = module

    def get_active_mode(self):
        """Return the name of the currently active mode, or None."""
        return self.active_mode

    def get_module(self, mode):
        """Return a registered module or None if not found."""
        return self.modules.get(mode)

    def switch(self, mode):

        if self.active_mode == mode:
            return

        module = self.get_module(mode)
        if not module:
            print(
                f"WARNING: Mode '{mode}' not available. Staying in '{self.active_mode}' mode."
            )
            return

        if self.active_mode:
            old_module = self.modules.get(self.active_mode)
            if old_module:
                old_module.on_exit()

        self.active_mode = mode
        module.on_enter()

        print("MODE SWITCH →", mode)

    def handle_command(self, command):
        # Special commands for music mode setup
        if command == "FETCH_SPOTIFY_DEVICES":
            # Get devices from music controller and update state machine
            if "music" in self.modules:
                music_module = self.modules["music"]
                devices = music_module.get_spotify_devices()
                # Update state machine with device list
                if self.state_machine:
                    self.state_machine.set_spotify_devices(devices)
            return
        elif command.startswith("SELECT_SPOTIFY_DEVICE:"):
            # Extract device index and pass to music controller
            device_index = int(command.split(":")[1])
            if "music" in self.modules:
                self.modules["music"].select_spotify_device(device_index)
            return
        elif command == "MODE_MUSIC_LOCAL":
            self.switch("music")
            if "music" in self.modules:
                self.modules["music"].set_mode("local")
            return
        elif command == "MODE_MUSIC_SPOTIFY":
            self.switch("music")
            if "music" in self.modules:
                self.modules["music"].set_mode("spotify")
            return
        
        # Mode switching commands
        if command == "MODE_MUSIC":
            self.switch("music")
            return
        elif command == "MODE_SYSTEM":
            self.switch("system")
            return
        elif command == "MODE_DINO":
            self.switch("dino")
            return
        elif command == "MODE_CATCH":
            self.switch("catch")
            return
        elif command == "MODE_FRUIT":
            self.switch("fruit")
            return

        elif command == "MODE_DRAWING":
            self.switch("drawing")
            return

        # Forward command to active module only
        if self.active_mode and self.active_mode in self.modules:
            module = self.modules[self.active_mode]
            module.handle_command(command)

    def update(self, frame):
        """Delegate frame rendering to the active module's update()."""
        if self.active_mode:
            module = self.modules.get(self.active_mode)
            if module:
                module.update(frame)

        # Show active mode label
        if self.active_mode:
            label = self.active_mode.upper()
            cv2.putText(
                frame,
                f"Mode: {label}",
                (10, 470),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
            )
