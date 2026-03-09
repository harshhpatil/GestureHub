import cv2
import numpy as np
import time
import math


# ── Drawing state machine states ──────────────────────────────
STATE_NEUTRAL = "NEUTRAL"
STATE_DRAW = "DRAW"
STATE_ERASE = "ERASE"
STATE_COLOR_SWITCH = "COLOR_SWITCH"


class DrawingBoardController:
    """Virtual gesture-controlled drawing board with state-machine gesture handling."""

    def __init__(self):
        self.canvas = None
        self.last_point = None
        self.eraser_last_pos = None
        self.last_color_change_time = 0
        self.color_change_cooldown = 0.5
        self.current_color_index = 0
        self.brush_size = 5
        self.eraser_radius = 75

        # ── State machine ────────────────────────────────────
        self._state = STATE_NEUTRAL
        self._state_frames = 0          # consecutive frames in candidate state
        self._candidate_state = None    # candidate waiting for confirmation
        self._CONFIRM_FRAMES = 2        # frames needed to confirm a transition

        self.colors = [
            (0, 255, 255),    # Yellow
            (0, 255, 0),      # Green
            (0, 0, 255),      # Red
            (255, 0, 0),      # Blue
            (255, 0, 255),    # Magenta
            (0, 165, 255),    # Orange
            (255, 255, 0),    # Cyan
        ]
        self.color_names = ["Yellow", "Green", "Red", "Blue", "Magenta", "Orange", "Cyan"]

    # ── Gesture detection ─────────────────────────────────────

    def detect_gesture(self, hand_landmarks):
        """Detect hand gestures from MediaPipe landmarks."""
        index_up = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
        middle_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
        ring_up = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
        pinky_up = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y

        if index_up and not middle_up and not ring_up and not pinky_up:
            return STATE_DRAW
        if index_up and pinky_up and not middle_up and not ring_up:
            return STATE_COLOR_SWITCH
        if index_up and middle_up and ring_up and pinky_up:
            return STATE_ERASE
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return STATE_NEUTRAL
        return STATE_NEUTRAL

    # ── State machine transition (flicker-free) ───────────────

    def _transition(self, raw_gesture):
        """Hysteresis-based state transition — requires _CONFIRM_FRAMES
        consecutive identical readings before switching state."""
        if raw_gesture == self._state:
            # Already in this state; reset candidate counter
            self._candidate_state = None
            self._state_frames = 0
            return

        if raw_gesture == self._candidate_state:
            self._state_frames += 1
        else:
            self._candidate_state = raw_gesture
            self._state_frames = 1

        if self._state_frames >= self._CONFIRM_FRAMES:
            # Commit the transition — clear context from old state
            if self._state != STATE_DRAW:
                self.last_point = None
            if self._state != STATE_ERASE:
                self.eraser_last_pos = None
            self._state = raw_gesture
            self._candidate_state = None
            self._state_frames = 0

    # ── Coordinate helpers ────────────────────────────────────

    def get_palm_center(self, hand_landmarks, w, h):
        """Calculate palm center from wrist and middle MCP."""
        wrist = hand_landmarks.landmark[0]
        middle_mcp = hand_landmarks.landmark[9]
        cx = int((wrist.x + middle_mcp.x) / 2 * w)
        cy = int((wrist.y + middle_mcp.y) / 2 * h)
        return (cx, cy)

    def get_index_pos(self, hand_landmarks, w, h):
        """Get index finger tip position."""
        idx = hand_landmarks.landmark[8]
        return (int(idx.x * w), int(idx.y * h))

    # ── Interpolation for smooth paths ────────────────────────

    @staticmethod
    def _interpolate(p1, p2, step=4):
        """Yield evenly spaced points between p1 and p2.
        Ensures smooth continuous strokes even during rapid movement."""
        x1, y1 = p1
        x2, y2 = p2
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < step:
            yield p2
            return
        steps = max(int(dist / step), 1)
        for i in range(1, steps + 1):
            t = i / steps
            yield (int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t))

    # ── Erase helper ──────────────────────────────────────────

    def hard_erase(self, palm_pos):
        """Hard erase on canvas at palm position with interpolation."""
        if self.canvas is None:
            return
        if self.eraser_last_pos:
            for pt in self._interpolate(self.eraser_last_pos, palm_pos, step=self.eraser_radius // 2):
                cv2.circle(self.canvas, pt, self.eraser_radius, (0, 0, 0), -1)
        else:
            cv2.circle(self.canvas, palm_pos, self.eraser_radius, (0, 0, 0), -1)

    # ── Main update (called every frame) ──────────────────────

    def update(self, frame, hand_landmarks=None):
        """Update drawing board with hand gestures.
        Returns modified frame with drawing overlay."""
        h, w = frame.shape[:2]

        if self.canvas is None:
            self.canvas = np.zeros_like(frame)

        # Blend canvas onto camera feed
        output = cv2.addWeighted(frame, 0.7, self.canvas, 0.3, 0)

        if hand_landmarks is not None:
            raw_gesture = self.detect_gesture(hand_landmarks)
            self._transition(raw_gesture)

            # ── Act on confirmed state ────────────────────────
            if self._state == STATE_DRAW:
                pos = self.get_index_pos(hand_landmarks, w, h)
                if self.last_point:
                    for pt in self._interpolate(self.last_point, pos, step=3):
                        cv2.circle(self.canvas, pt, self.brush_size,
                                   self.colors[self.current_color_index], -1)
                self.last_point = pos
                # Live cursor
                cv2.circle(output, pos, self.brush_size + 2,
                           self.colors[self.current_color_index], 2)

            elif self._state == STATE_ERASE:
                palm_pos = self.get_palm_center(hand_landmarks, w, h)
                self.hard_erase(palm_pos)
                self.eraser_last_pos = palm_pos
                # Visual ring
                cv2.circle(output, palm_pos, self.eraser_radius, (255, 255, 255), 2)
                cv2.putText(output, "ERASER",
                            (palm_pos[0] - 40, palm_pos[1] - self.eraser_radius - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            elif self._state == STATE_COLOR_SWITCH:
                if time.time() - self.last_color_change_time > self.color_change_cooldown:
                    self.current_color_index = (self.current_color_index + 1) % len(self.colors)
                    self.last_color_change_time = time.time()

            # NEUTRAL — do nothing (fist / no gesture)
        else:
            # No hand detected — keep state but clear tracking points
            self.last_point = None
            self.eraser_last_pos = None

        # ── HUD overlay ───────────────────────────────────────
        state_label = self._state
        label_color = {
            STATE_DRAW: (0, 255, 100),
            STATE_ERASE: (0, 140, 255),
            STATE_COLOR_SWITCH: (255, 200, 0),
            STATE_NEUTRAL: (180, 180, 180),
        }.get(state_label, (180, 180, 180))

        # Title bar
        overlay_bar = output.copy()
        cv2.rectangle(overlay_bar, (0, 0), (w, 70), (20, 20, 20), -1)
        cv2.addWeighted(overlay_bar, 0.6, output, 0.4, 0, output)

        cv2.putText(output, "DRAWING BOARD", (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 204), 2)
        cv2.putText(output, state_label, (15, 58),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, label_color, 1)

        # Color swatch
        cv2.rectangle(output, (w - 170, 10), (w - 10, 60),
                      self.colors[self.current_color_index], -1)
        cv2.rectangle(output, (w - 170, 10), (w - 10, 60), (80, 80, 80), 1)
        cv2.putText(output, self.color_names[self.current_color_index],
                    (w - 155, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 2)

        # Bottom instruction bar
        overlay_bot = output.copy()
        cv2.rectangle(overlay_bot, (0, h - 40), (w, h), (20, 20, 20), -1)
        cv2.addWeighted(overlay_bot, 0.6, output, 0.4, 0, output)
        cv2.putText(output, "INDEX: Draw | ROCK-ON: Color | PALM: Erase | FIST: Neutral",
                    (w // 2 - 260, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

        return output

    def clear_canvas(self):
        """Clear drawing canvas."""
        if self.canvas is not None:
            self.canvas = np.zeros_like(self.canvas)
        self.last_point = None
        self.eraser_last_pos = None

    def on_enter(self):
        """Called when drawing board mode is activated."""
        self.canvas = None
        self.last_point = None
        self.eraser_last_pos = None
        self._state = STATE_NEUTRAL
        self._candidate_state = None
        self._state_frames = 0
        print("🎨 Drawing Board Activated")

    def on_exit(self):
        """Called when drawing board mode is deactivated."""
        print("🎨 Drawing Board Deactivated")

    def handle_command(self, command):
        """Handle commands (e.g., from gesture controller or menu)."""
        if command == "CLEAR":
            self.clear_canvas()
            print("Canvas cleared")
