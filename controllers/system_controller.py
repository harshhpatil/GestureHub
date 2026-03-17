from controllers.base_controller import BaseController
import pyautogui
import subprocess
import re
import cv2


class SystemController(BaseController):

    def __init__(self):
        self.current_volume = self.get_volume()
        self.recent_tabs_open = False

    # lifecycle hooks
    def on_enter(self):
        print("System Module Activated")

    def on_exit(self):
        print("System Module Deactivated")
        if self.recent_tabs_open:
            try:
                pyautogui.keyUp("alt")
            except:
                pass
            self.recent_tabs_open = False

    def update(self, frame):
        """Render system module UI (volume and status) onto frame."""
        h, w = frame.shape[:2]
        
        # Display current volume
        cv2.putText(
            frame,
            f"Volume: {self.current_volume}%",
            (50, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )
        
        # Display system status
        status_mode = "Tab Navigate" if self.recent_tabs_open else "System Ready"
        cv2.putText(
            frame,
            f"Status: {status_mode}",
            (50, 160),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
        )

    def get_volume(self):

        try:
            result = subprocess.run(
                ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                match = re.search(r'(\d+)%', result.stdout)

                if match:
                    self.current_volume = int(match.group(1))
                    return self.current_volume

        except:
            pass

        try:
            result = subprocess.run(
                ["amixer", "get", "Master"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if result.returncode == 0:
                match = re.search(r'\[(\d+)%\]', result.stdout)

                if match:
                    self.current_volume = int(match.group(1))
                    return self.current_volume

        except:
            pass

        return 50

    def set_volume(self, percentage):

        percentage = max(0, min(100, percentage))

        try:
            subprocess.run(
                ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{percentage}%"],
                timeout=2,
                capture_output=True
            )

            self.current_volume = percentage
            return True

        except:
            pass

        try:
            subprocess.run(
                ["amixer", "set", "Master", f"{percentage}%"],
                timeout=2,
                capture_output=True
            )

            self.current_volume = percentage
            return True

        except Exception as e:
            print(f"Warning: Could not set volume: {e}")
            return False

    def handle_command(self, command):

        if command == "OPEN_RECENT_TABS":
            try:
                pyautogui.keyDown("alt")
                pyautogui.press("tab")
                self.recent_tabs_open = True
                print("Recent tabs opened")
            except Exception as e:
                print(f"Failed to open recent tabs: {e}")
            return

        if command == "LEFT_CLICK":
            if self.recent_tabs_open:
                try:
                    pyautogui.keyUp("alt")
                except:
                    pass
                self.recent_tabs_open = False
            pyautogui.click(button="left")
            print("Left click")
            return

        if command in ("VOL_UP", "VOLUME_UP"):

            new_volume = min(100, self.current_volume + 5)
            self.set_volume(new_volume)

            print(f"Volume Up: {self.current_volume}%")

        elif command in ("VOL_DOWN", "VOLUME_DOWN"):

            new_volume = max(0, self.current_volume - 5)
            self.set_volume(new_volume)

            print(f"Volume Down: {self.current_volume}%")

        elif command == "SCROLL_UP":

            pyautogui.scroll(300)

        elif command == "SCROLL_DOWN":

            pyautogui.scroll(-300)

        elif command == "NEXT_TRACK":
            if self.recent_tabs_open:
                pyautogui.press("tab")
            else:
                pyautogui.hscroll(-300)

        elif command == "PREV_TRACK":
            if self.recent_tabs_open:
                pyautogui.hotkey("shift", "tab")
            else:
                pyautogui.hscroll(300)

        elif command == "SCREENSHOT":
            # If tab switcher is open, close it first to avoid accidental focus switch
            if self.recent_tabs_open:
                try:
                    pyautogui.keyUp("alt")
                except:
                    pass
                self.recent_tabs_open = False

            pyautogui.screenshot("screenshot.png")
            print("Screenshot saved")

        elif command == "RESET":

            print("System Reset triggered")

    def update(self, frame):
        """Render system module UI overlay onto the frame."""
        vol = self.current_volume

        # Volume label
        cv2.putText(frame, "System Vol:", (50, 130),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        # Volume bar
        bar_x, bar_y = 50, 145
        bar_w, bar_h = 150, 20
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50, 50, 50), -1)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (255, 255, 255), 2)

        fill = int((vol / 100) * bar_w)
        if vol < 33:
            color = (0, 255, 0)
        elif vol < 66:
            color = (0, 255, 255)
        else:
            color = (0, 0, 255)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill, bar_y + bar_h), color, -1)

        cv2.putText(frame, f"{vol}%", (bar_x + bar_w + 10, bar_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)