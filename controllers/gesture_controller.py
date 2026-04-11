from gesture_engine.motion_gesture import MotionGestureDetector
import time


DEBUG_GESTURES = False

class BaseGestureController:
    def __init__(self):
        self.motion = MotionGestureDetector()
        self.prev_gesture = None
        self.gesture_history = []
        self.STABILITY_FRAMES = 3
        self.prev_pinch = False
        self.pinch_armed_until = 0
        self.pinch_combo_window = 1.2

    def process_landmarks(self, landmarks, hand_label):
        fingers = [0, 0, 0, 0, 0]
        
        # Thumb UP/DOWN detection (vertical position)
        thumb_tip_y = landmarks[4][1]  # Thumb tip Y-coordinate
        thumb_pip_y = landmarks[3][1]  # Thumb PIP Y-coordinate
        
        if thumb_tip_y < thumb_pip_y - 0.08:  # Thumb pointing UP (normalized coords)
            fingers[0] = 2  # 2 = thumbs up
        elif thumb_tip_y > thumb_pip_y + 0.08:  # Thumb pointing DOWN (normalized coords)
            fingers[0] = -1  # -1 = thumbs down
        else:  # Thumb neutral
            # Original left/right logic
            if hand_label == "Right":
                if landmarks[4][0] > landmarks[3][0]:
                    fingers[0] = 1
            else:
                if landmarks[4][0] < landmarks[3][0]:
                    fingers[0] = 1

        # Other fingers (using Y-coordinates for finger extension detection)
        # For extended fingers in MediaPipe image coords: TIP should be above PIP (lower Y).
        finger_threshold = 0.08  # Normalized coordinate threshold
        if landmarks[6][1] - landmarks[8][1] > finger_threshold:  # Index extended
            fingers[1] = 1
        if landmarks[10][1] - landmarks[12][1] > finger_threshold:  # Middle extended
            fingers[2] = 1
        if landmarks[14][1] - landmarks[16][1] > finger_threshold:  # Ring extended
            fingers[3] = 1
        if landmarks[18][1] - landmarks[20][1] > finger_threshold:  # Pinky extended
            fingers[4] = 1
            
        if DEBUG_GESTURES:
            print(f"DEBUG process_landmarks: thumb_y={thumb_tip_y:.3f}, pip_y={thumb_pip_y:.3f}, fingers={fingers}")
            
        return fingers
    
    def detect_pinch(self, landmarks):
        """Detect pinch gesture (thumb and index finger close together)."""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]

        dx = thumb_tip[0] - index_tip[0]  # X distance (normalized)
        dy = thumb_tip[1] - index_tip[1]  # Y distance (normalized)

        distance = (dx*dx + dy*dy) ** 0.5

        # Pinch threshold: 0.05 in normalized coordinates (about 30-50 pixels on 640x480)
        if distance < 0.05:
            return True

        return False

    def is_index_middle_victory(self, landmarks):
        """Detect index+middle victory shape using fingertip distance."""
        index_tip = landmarks[8]
        middle_tip = landmarks[12]

        dx = index_tip[0] - middle_tip[0]  # X distance (normalized)
        dy = index_tip[1] - middle_tip[1]  # Y distance (normalized)
        distance = (dx * dx + dy * dy) ** 0.5

        # Victory threshold: 0.23 in normalized coordinates (represents finger spread)
        return distance >= 0.23

    def classify_gesture(self, fingers):
        if DEBUG_GESTURES:
            print(f"DEBUG classify_gesture: fingers={fingers}")
        
        # Thumbs Up/Down
        if fingers[0] == 2 and sum(fingers[1:]) == 0:
            return "THUMBS_UP"
        elif fingers[0] == -1 and sum(fingers[1:]) == 0:
            return "THUMBS_DOWN"
        
        # Original gestures
        if sum(fingers) == 0:
            return "FIST"
        elif fingers[1:] == [1,0,0,0]:
            return "INDEX"
        elif fingers[1:] == [1,1,0,0]:  # index + middle (thumb ignored)
            return "TWO_FINGERS"
        elif fingers[1:] == [0,1,1,0]:  # middle + ring (thumb ignored) - Peace sign
            return "PEACE_SIGN"
        elif fingers[1:] == [1,0,0,1]:  # index + pinky (thumb ignored) - Rock/Horns gesture
            return "ROCK"
        elif sum(fingers[1:]) >= 4:  # Ignore thumb for open palm
            return "OPEN_PALM"
        elif fingers[1:] == [1,1,1,0]:  # Ignore thumb for 3 fingers
            return "THREE_FINGERS"
        
        return "UNKNOWN"

    def stabilize(self, gesture):  # ✅ MISSING METHOD ADDED
        if gesture in ("UNKNOWN", "NO_HAND"):
            self.gesture_history.clear()
            self.prev_gesture = None
            return "NO_HAND"

        self.gesture_history.append(gesture)
        if len(self.gesture_history) > self.STABILITY_FRAMES:
            self.gesture_history.pop(0)
        
        if len(self.gesture_history) == self.STABILITY_FRAMES:
            if len(set(self.gesture_history)) == 1:
                return self.gesture_history[-1]
            return "NO_HAND"
        return "NO_HAND"

    def _update_pinch_state(self, landmarks=None):
        if landmarks is None:
            self.prev_pinch = False
            return False

        pinch = self.detect_pinch(landmarks)
        pinch_started = pinch and not self.prev_pinch

        if pinch_started:
            self.pinch_armed_until = time.time() + self.pinch_combo_window

        self.prev_pinch = pinch
        return pinch_started


class MenuGestureController(BaseGestureController):
    def __init__(self):
        super().__init__()

    def detect_commands(self, stable_gesture, hand_pos, landmarks=None, active_mode=None):
        commands = []

        if active_mode == "drawing" and stable_gesture == "FIST":
                commands.append("RESET")

        if stable_gesture == "TWO_FINGERS":
            # Clear motion buffer when ENTERING TWO_FINGERS (fresh start for this gesture)
            if self.prev_gesture != "TWO_FINGERS":
                self.motion.clear_buffer()
            
            self.prev_gesture = "TWO_FINGERS"
            self.motion.update(hand_pos)

            swipe = self.motion.detect_swipe()
            if swipe == "SWIPE_RIGHT":
                commands.append("NEXT_TRACK")
            elif swipe == "SWIPE_LEFT":
                commands.append("PREV_TRACK")
        else:
            # Update prev_gesture for all other gestures
            if stable_gesture not in ["NO_HAND", "UNKNOWN"]:
                self.prev_gesture = stable_gesture

        if self._update_pinch_state(landmarks):
            commands.append("PINCH")

        return commands


class MusicGestureController(BaseGestureController):
    def __init__(self):
        super().__init__()
        self.reset_guard_until = 0

    def detect_commands(self, stable_gesture, hand_pos, landmarks=None, active_mode=None):
        commands = []
        now = time.time()

        if stable_gesture == "OPEN_PALM":
            commands.append("RESET")
            self.reset_guard_until = now + 0.8
            self.prev_gesture = stable_gesture

        elif now < self.reset_guard_until:
            # Ignore transient gestures right after palm-reset to avoid accidental STOP/TOGGLE
            self.prev_gesture = stable_gesture

        elif (stable_gesture and stable_gesture not in ("NO_HAND", "TWO_FINGERS") and
              stable_gesture != self.prev_gesture):

            if stable_gesture == "INDEX":
                commands.append("TOGGLE_PLAY")
            elif stable_gesture == "THUMBS_UP":
                commands.append("VOLUME_UP")
            elif stable_gesture == "THUMBS_DOWN":
                commands.append("VOLUME_DOWN")

            self.prev_gesture = stable_gesture

        if stable_gesture == "TWO_FINGERS":
            # Clear motion buffer when ENTERING TWO_FINGERS (fresh start for this gesture)
            if self.prev_gesture != "TWO_FINGERS":
                self.motion.clear_buffer()
            
            self.prev_gesture = "TWO_FINGERS"
            self.motion.update(hand_pos)

            swipe = self.motion.detect_swipe()
            if swipe == "SWIPE_RIGHT":
                commands.append("NEXT_TRACK")
            elif swipe == "SWIPE_LEFT":
                commands.append("PREV_TRACK")

        if self._update_pinch_state(landmarks):
            commands.append("PINCH")
        
        return commands


class SystemGestureController(BaseGestureController):
    def __init__(self):
        super().__init__()
        self.action_lock_until = 0
        self.volume_repeat_interval = 0.18
        self.last_volume_emit = 0

    def detect_commands(self, stable_gesture, hand_pos, landmarks=None, active_mode=None):
        commands = []
        now = time.time()

        # Continuous volume control while thumb gesture is held
        if stable_gesture in ("THUMBS_UP", "THUMBS_DOWN"):
            if stable_gesture != self.prev_gesture:
                self.last_volume_emit = 0

            if now - self.last_volume_emit >= self.volume_repeat_interval:
                if stable_gesture == "THUMBS_UP":
                    commands.append("VOLUME_UP")
                else:
                    commands.append("VOLUME_DOWN")
                self.last_volume_emit = now

            self.prev_gesture = stable_gesture

        if stable_gesture == "OPEN_PALM":
            commands.append("RESET")
            self.prev_gesture = stable_gesture

        elif (stable_gesture and stable_gesture != "NO_HAND" and
              stable_gesture != self.prev_gesture):

            if stable_gesture == "ROCK":
                commands.append("SCREENSHOT")
                self.pinch_armed_until = 0
                self.motion.clear_buffer()
                self.action_lock_until = now + 0.35

            self.prev_gesture = stable_gesture

        if stable_gesture == "TWO_FINGERS":
            if now < self.action_lock_until:
                self._update_pinch_state(landmarks)
                return commands

            if landmarks is not None and self.is_index_middle_victory(landmarks):
                if self.prev_gesture != "TWO_FINGERS_VICTORY":
                    commands.append("LEFT_CLICK")
                    self.prev_gesture = "TWO_FINGERS_VICTORY"
                    self.motion.clear_buffer()
            else:
                # Clear motion buffer when ENTERING TWO_FINGERS swipe mode
                if self.prev_gesture != "TWO_FINGERS":
                    self.motion.clear_buffer()
                
                self.prev_gesture = "TWO_FINGERS"
                self.motion.update(hand_pos)

                swipe = self.motion.detect_swipe()
                if swipe == "SWIPE_RIGHT":
                    commands.append("NEXT_TRACK")
                elif swipe == "SWIPE_LEFT":
                    if now <= self.pinch_armed_until:
                        commands.append("OPEN_RECENT_TABS")
                        self.pinch_armed_until = 0
                    else:
                        commands.append("PREV_TRACK")

                scroll = self.motion.detect_scroll()
                if scroll == "SCROLL_UP":
                    commands.append("SCROLL_UP")
                elif scroll == "SCROLL_DOWN":
                    commands.append("SCROLL_DOWN")

        if stable_gesture not in ("THUMBS_UP", "THUMBS_DOWN"):
            self.last_volume_emit = 0

        self._update_pinch_state(landmarks)
        return commands

class GameGestureController(BaseGestureController):
    """Generic game gesture controller - swipes, pinches, and open palm."""
    def detect_commands(self, stable_gesture, hand_pos, landmarks=None, active_mode=None):
        commands = []

        # Open palm returns to menu
        if stable_gesture == "OPEN_PALM":
            commands.append("RESET")
            self.prev_gesture = stable_gesture

        # Two-finger swipes for game actions
        elif stable_gesture == "TWO_FINGERS":
            # Clear motion buffer when ENTERING TWO_FINGERS (fresh start for this gesture)
            if self.prev_gesture != "TWO_FINGERS":
                self.motion.clear_buffer()
            
            self.prev_gesture = "TWO_FINGERS"
            self.motion.update(hand_pos)

            swipe = self.motion.detect_swipe()
            if swipe == "SWIPE_RIGHT":
                commands.append("NEXT_TRACK")
            elif swipe == "SWIPE_LEFT":
                commands.append("PREV_TRACK")
        
        else:
            # Update prev_gesture for all other gestures
            if stable_gesture not in ["NO_HAND", "UNKNOWN"]:
                self.prev_gesture = stable_gesture

        # Pinch for game start/stop
        if self._update_pinch_state(landmarks):
            commands.append("PINCH")

        return commands
