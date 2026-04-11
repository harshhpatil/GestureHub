"""Fruit Ninja-style game controller driven by hand motion."""
from controllers.base_controller import BaseController
import cv2
import json
import math
import random
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def _distance_point_to_segment(point, start, end):
    px, py = point
    x1, y1 = start
    x2, y2 = end
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / float(dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


class _SlashObject:
    def __init__(self, frame_w, frame_h):
        self.kind = "bomb" if random.random() < 0.08 else "fruit"
        margin = 80
        self.x = float(random.randint(margin, max(margin + 1, frame_w - margin)))
        self.y = float(frame_h + random.randint(20, 120))
        self.vx = float(random.uniform(-110, 110))
        self.vy = float(random.uniform(-920, -760))
        self.radius = random.randint(30, 46)
        self.gravity = 980.0
        self.cut = False
        self.missed = False
        self.cut_at = 0.0
        self.fragment_offset = 0.0

        self.color = (50, 50, 50) if self.kind == "bomb" else random.choice([
            (0, 140, 255),
            (0, 255, 180),
            (255, 200, 0),
            (80, 80, 255),
            (255, 120, 180),
            (120, 255, 120),
        ])

    def update(self, dt):
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.cut:
            self.fragment_offset += 240.0 * dt

    def is_offscreen(self, frame_w, frame_h):
        return self.x < -120 or self.x > frame_w + 120 or self.y > frame_h + 140

    def draw(self, frame):
        center_x = int(self.x)
        center_y = int(self.y)

        if self.kind == "bomb":
            cv2.circle(frame, (center_x, center_y), self.radius, (45, 45, 45), -1)
            cv2.circle(frame, (center_x, center_y), self.radius, (180, 180, 180), 2)
            cv2.line(frame, (center_x, center_y - self.radius), (center_x + 10, center_y - self.radius - 16), (0, 220, 255), 2)
            cv2.circle(frame, (center_x, center_y), 6, (0, 0, 255), -1)
            return

        if self.cut:
            offset = int(self.fragment_offset)
            left_center = (center_x - offset, center_y + offset // 2)
            right_center = (center_x + offset, center_y + offset // 2)
            cv2.ellipse(frame, left_center, (self.radius, self.radius - 4), 25, 40, 220, self.color, -1)
            cv2.ellipse(frame, right_center, (self.radius, self.radius - 4), -25, -40, 140, self.color, -1)
            cv2.line(frame, (left_center[0] - self.radius // 2, left_center[1]),
                     (left_center[0] + self.radius // 2, left_center[1]), (255, 255, 255), 2)
            cv2.line(frame, (right_center[0] - self.radius // 2, right_center[1]),
                     (right_center[0] + self.radius // 2, right_center[1]), (255, 255, 255), 2)
            return

        cv2.circle(frame, (center_x, center_y), self.radius, self.color, -1)
        cv2.circle(frame, (center_x - 8, center_y - 8), max(6, self.radius // 4), (255, 255, 255), -1)
        cv2.circle(frame, (center_x, center_y), self.radius, (255, 255, 255), 2)


class FruitGameController(BaseController):
    def __init__(self):
        self.game_state = "READY"
        self.score = 0
        self.high_score = 0
        self.lives = 5
        self.combo = 0
        self.best_combo = 0
        self.spawn_interval = 1.25
        self.last_spawn_time = time.time()
        self.last_frame_time = time.time()
        self.objects = []
        self.slash_points = []
        self.last_slash_time = 0.0
        self.combo_flash_until = 0.0
        self.combo_flash_text = ""
        self.explosion_until = 0.0
        self.highscore_path = ASSETS_DIR / "fruit_highscore.json"
        self.debug_assets_text = "Shapes Mode"
        self._load_high_score()

    def _load_high_score(self):
        try:
            if self.highscore_path.exists():
                data = json.loads(self.highscore_path.read_text())
                self.high_score = int(data.get("high_score", 0))
        except Exception:
            self.high_score = 0

    def _save_high_score(self):
        try:
            self.highscore_path.parent.mkdir(parents=True, exist_ok=True)
            self.highscore_path.write_text(json.dumps({"high_score": int(self.high_score)}))
        except Exception:
            pass

    def _reset_run(self):
        self.score = 0
        self.lives = 5
        self.combo = 0
        self.best_combo = 0
        self.spawn_interval = 1.25
        self.last_spawn_time = time.time()
        self.last_frame_time = time.time()
        self.objects = []
        self.slash_points = []
        self.last_slash_time = 0.0
        self.combo_flash_until = 0.0
        self.combo_flash_text = ""
        self.explosion_until = 0.0

    def on_enter(self):
        print("Fruit Slice Game Started")
        self.game_state = "READY"
        self._reset_run()

    def on_exit(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()
        print(f"Fruit Game Over - Score: {self.score} | High: {self.high_score}")

    def handle_command(self, command):
        if command == "PINCH":
            if self.game_state == "READY":
                self.game_state = "RUNNING"
                self.last_frame_time = time.time()
            elif self.game_state == "RUNNING":
                self.game_state = "PAUSED"
            elif self.game_state == "PAUSED":
                self.game_state = "RUNNING"
                self.last_frame_time = time.time()
            elif self.game_state == "GAME_OVER":
                self._reset_run()
                self.game_state = "RUNNING"
        elif command == "RESET":
            print("Exiting Fruit Game")

    def _spawn_object(self, frame_w, frame_h):
        if len(self.objects) >= 8:
            return

        burst_count = 1
        if random.random() < 0.18:
            burst_count = 2

        for _ in range(burst_count):
            if len(self.objects) >= 8:
                break
            self.objects.append(_SlashObject(frame_w, frame_h))

    def _update_slash(self, hand_landmarks, frame_w, frame_h):
        if hand_landmarks is None or self.game_state != "RUNNING":
            if self.slash_points and (time.time() - self.last_slash_time) > 0.2:
                self.slash_points.clear()
            return

        index_tip = hand_landmarks.landmark[8]
        point = (int(index_tip.x * frame_w), int(index_tip.y * frame_h))
        now = time.time()

        if self.slash_points:
            prev = self.slash_points[-1]
            distance = math.hypot(point[0] - prev[0], point[1] - prev[1])
            if distance > 5:
                self.slash_points.append(point)
                self.last_slash_time = now
        else:
            self.slash_points.append(point)
            self.last_slash_time = now

        self.slash_points = self.slash_points[-8:]

    def _handle_slice_hits(self):
        if len(self.slash_points) < 2 or self.game_state != "RUNNING":
            return

        slice_count = 0
        for obj in self.objects:
            if obj.cut:
                continue

            hit = False
            for start, end in zip(self.slash_points, self.slash_points[1:]):
                slash_speed = math.hypot(end[0] - start[0], end[1] - start[1])
                if slash_speed < 10:
                    continue
                if _distance_point_to_segment((obj.x, obj.y), start, end) <= obj.radius + 18:
                    hit = True
                    break

            if not hit:
                continue

            obj.cut = True
            obj.cut_at = time.time()
            slice_count += 1

            if obj.kind == "bomb":
                self.game_state = "GAME_OVER"
                self.explosion_until = time.time() + 0.35
                self.combo = 0
                if self.score > self.high_score:
                    self.high_score = self.score
                    self._save_high_score()
                return

            self.score += 12
            self.combo += 1
            self.best_combo = max(self.best_combo, self.combo)

        if slice_count >= 2:
            self.score += 5 * slice_count
            self.combo_flash_text = f"COMBO x{slice_count}"
            self.combo_flash_until = time.time() + 0.45

    def _update_objects(self, dt, frame_w, frame_h):
        for obj in self.objects:
            obj.update(dt)

            if obj.kind == "fruit" and not obj.cut and obj.y - obj.radius > frame_h:
                obj.missed = True
                obj.cut = True
                self.lives -= 1
                self.combo = 0

        self.objects = [
            obj for obj in self.objects
            if not obj.is_offscreen(frame_w, frame_h)
            and not (obj.cut and (time.time() - obj.cut_at) > 0.35)
        ]

        if self.lives <= 0:
            self.game_state = "GAME_OVER"
            if self.score > self.high_score:
                self.high_score = self.score
                self._save_high_score()

    def _draw_background(self, frame):
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (12, 70), (w - 12, h - 60), (18, 18, 18), -1)
        cv2.addWeighted(overlay, 0.34, frame, 0.66, 0, frame)
        cv2.rectangle(frame, (12, 70), (w - 12, h - 60), (85, 85, 85), 1)

    def _draw_slash(self, frame):
        if len(self.slash_points) < 2:
            return

        for i in range(1, len(self.slash_points)):
            thickness = max(2, 8 - (len(self.slash_points) - i))
            color = (255, 255 - i * 18, 80 + i * 20)
            cv2.line(frame, self.slash_points[i - 1], self.slash_points[i], color, thickness)

        cv2.circle(frame, self.slash_points[-1], 8, (255, 255, 255), -1)

    def _draw_ui(self, frame):
        h, w = frame.shape[:2]

        cv2.putText(frame, "FRUIT NINJA MODE", (w // 2 - 160, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 255, 255), 2)
        cv2.putText(frame, f"Score: {self.score}", (24, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.78, (70, 255, 140), 2)
        cv2.putText(frame, f"Best: {self.high_score}", (24, 74),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.56, (210, 210, 210), 1)
        cv2.putText(frame, f"Lives: {self.lives}", (w - 120, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 190, 255), 2)
        cv2.putText(frame, f"Combo: x{self.combo}", (w - 150, 74),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.56, (0, 220, 255), 1)

        status_text = self.game_state
        status_color = {
            "READY": (0, 255, 180),
            "RUNNING": (0, 255, 0),
            "PAUSED": (0, 180, 255),
            "GAME_OVER": (0, 0, 255),
        }.get(self.game_state, (200, 200, 200))
        cv2.putText(frame, f"Status: {status_text}", (24, h - 82),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.58, status_color, 2)
        cv2.putText(frame, "Move your index finger fast to slice | Pinch: Start/Pause | Open Palm: Exit",
                    (22, h - 32), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (210, 210, 210), 1)
        cv2.putText(frame, self.debug_assets_text, (24, h - 56),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 130, 255), 1)

        if self.game_state == "READY":
            cv2.putText(frame, "PINCH TO START", (w // 2 - 125, h // 2 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.95, (0, 255, 150), 2)
            cv2.putText(frame, "Slice fruit with slow steady hand motion. Bombs are rare.",
                        (w // 2 - 185, h // 2 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (220, 220, 220), 1)
        elif self.game_state == "PAUSED":
            cv2.putText(frame, "PAUSED", (w // 2 - 70, h // 2 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
        elif self.game_state == "GAME_OVER":
            cv2.putText(frame, "GAME OVER", (w // 2 - 112, h // 2 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 80, 255), 3)
            cv2.putText(frame, "Pinch to restart", (w // 2 - 92, h // 2 + 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)

        if time.time() < self.combo_flash_until:
            cv2.putText(frame, self.combo_flash_text, (w // 2 - 95, 92),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)

        if time.time() < self.explosion_until:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

    def update(self, frame, hand_landmarks=None):
        h, w = frame.shape[:2]
        now = time.time()
        dt = min(max(now - self.last_frame_time, 0.001), 0.05)
        self.last_frame_time = now

        self._draw_background(frame)
        self._update_slash(hand_landmarks, w, h)

        if self.game_state == "RUNNING" and (now - self.last_spawn_time) >= self.spawn_interval:
            self._spawn_object(w, h)
            self.last_spawn_time = now
            self.spawn_interval = max(0.85, self.spawn_interval - 0.004)

        if self.game_state == "RUNNING":
            self._handle_slice_hits()
            self._update_objects(dt, w, h)

        for obj in self.objects:
            obj.draw(frame)

        self._draw_slash(frame)
        self._draw_ui(frame)
        return frame
