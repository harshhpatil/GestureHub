"""Playable Catch Game Controller integrated with app gesture pipeline."""
from controllers.base_controller import BaseController
import cv2
import json
import random
import time
from pathlib import Path


class CatchGameController(BaseController):
    def __init__(self):
        self.game_state = "READY"
        self.score = 0
        self.high_score = 0
        self.lives = 3

        self.basket_x = 320.0
        self.target_x = 320.0
        self.basket_w = 130
        self.basket_h = 24
        self.basket_step = 48
        self.follow_smooth = 0.26

        self.items = []
        self.spawn_timer = 0.0
        self.next_spawn_in = 0.9
        self.base_fall_speed = 220.0
        self.fall_speed = self.base_fall_speed
        self.max_fall_speed = 620.0

        self.last_frame_time = time.time()
        self.hit_flash_until = 0.0

        self.highscore_path = Path("assets") / "catch_highscore.json"
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
        self.lives = 3
        self.items = []
        self.spawn_timer = 0.0
        self.next_spawn_in = random.uniform(0.7, 1.2)
        self.fall_speed = self.base_fall_speed

    def on_enter(self):
        print("Catch Game Started")
        self.game_state = "READY"
        self.last_frame_time = time.time()
        self._reset_run()

    def on_exit(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()
        print(f"Catch Game Over - Score: {self.score} | High: {self.high_score}")

    def handle_command(self, command):
        if command == "PINCH":
            if self.game_state == "READY":
                self.game_state = "RUNNING"
            elif self.game_state == "RUNNING":
                self.game_state = "PAUSED"
            elif self.game_state == "PAUSED":
                self.game_state = "RUNNING"
            elif self.game_state == "GAME_OVER":
                self._reset_run()
                self.game_state = "RUNNING"

        elif command == "NEXT_TRACK":
            self.basket_x += self.basket_step
        elif command == "PREV_TRACK":
            self.basket_x -= self.basket_step
        elif command == "RESET":
            print("Exiting Catch Game")

    def _spawn_item(self, frame_w):
        radius = random.randint(18, 30)
        x = random.randint(40, frame_w - 40)

        # 82% good fruits, 18% bombs for challenge
        is_bomb = random.random() < 0.18
        if is_bomb:
            color = (50, 50, 50)
            points = -1
            label = "B"
        else:
            palette = [(0, 80, 255), (0, 255, 120), (255, 150, 0), (255, 80, 180)]
            color = random.choice(palette)
            points = 1
            label = ""

        self.items.append({
            "x": float(x),
            "y": float(-radius - 8),
            "r": radius,
            "color": color,
            "points": points,
            "label": label,
        })

    def _update_items(self, dt, frame_w, frame_h):
        self.spawn_timer += dt
        if self.spawn_timer >= self.next_spawn_in:
            self.spawn_timer = 0.0
            self.next_spawn_in = random.uniform(0.45, 1.0)
            self._spawn_item(frame_w)

        self.fall_speed = min(self.max_fall_speed, self.base_fall_speed + self.score * 4.0)

        basket_y = frame_h - 80
        basket_x1 = int(self.basket_x - self.basket_w // 2)
        basket_x2 = int(self.basket_x + self.basket_w // 2)
        basket_y1 = int(basket_y)
        basket_y2 = int(basket_y + self.basket_h)

        alive_items = []
        for item in self.items:
            item["y"] += self.fall_speed * dt

            item_bottom = item["y"] + item["r"]
            item_top = item["y"] - item["r"]
            item_left = item["x"] - item["r"]
            item_right = item["x"] + item["r"]

            in_basket_y = item_bottom >= basket_y1 and item_top <= basket_y2
            in_basket_x = item_right >= basket_x1 and item_left <= basket_x2

            if in_basket_y and in_basket_x:
                if item["points"] > 0:
                    self.score += item["points"]
                else:
                    self.lives -= 1
                    self.hit_flash_until = time.time() + 0.18
                continue

            if item_top > frame_h:
                if item["points"] > 0:
                    self.lives -= 1
                    self.hit_flash_until = time.time() + 0.12
                continue

            alive_items.append(item)

        self.items = alive_items

        if self.lives <= 0:
            self.game_state = "GAME_OVER"
            if self.score > self.high_score:
                self.high_score = self.score
                self._save_high_score()

    def _draw_world(self, frame):
        h, w = frame.shape[:2]

        # Clamp basket in bounds each frame
        self.basket_x = max(self.basket_w // 2 + 6, min(w - self.basket_w // 2 - 6, self.basket_x))

        # Playfield
        cv2.rectangle(frame, (12, 130), (w - 12, h - 50), (90, 90, 90), 1)

        # Basket
        basket_y = h - 80
        x1 = int(self.basket_x - self.basket_w // 2)
        x2 = int(self.basket_x + self.basket_w // 2)
        y1 = int(basket_y)
        y2 = int(basket_y + self.basket_h)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 120), -1)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 90, 50), 2)

        # Falling items
        for item in self.items:
            center = (int(item["x"]), int(item["y"]))
            cv2.circle(frame, center, int(item["r"]), item["color"], -1)
            cv2.circle(frame, center, int(item["r"]), (30, 30, 30), 1)
            if item["label"]:
                cv2.putText(frame, item["label"], (center[0] - 6, center[1] + 6),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    def _draw_ui(self, frame):
        h, w = frame.shape[:2]

        cv2.putText(frame, "CATCH GAME", (w // 2 - 110, 46),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"Score: {int(self.score)}", (30, 44),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 255, 80), 2)
        cv2.putText(frame, f"Best: {int(self.high_score)}", (30, 78),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)
        cv2.putText(frame, f"Lives: {self.lives}", (30, 108),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (120, 180, 255), 2)

        if self.game_state == "READY":
            cv2.putText(frame, "PINCH TO START", (w // 2 - 140, h // 2 - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 120), 2)
        elif self.game_state == "PAUSED":
            cv2.putText(frame, "PAUSED", (w // 2 - 70, h // 2 - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(frame, "PINCH TO RESUME", (w // 2 - 125, h // 2 + 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 1)
        elif self.game_state == "GAME_OVER":
            cv2.putText(frame, "GAME OVER", (w // 2 - 110, h // 2 - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (40, 40, 255), 3)
            cv2.putText(frame, "PINCH TO RESTART", (w // 2 - 145, h // 2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        cv2.putText(frame, "Move INDEX finger: Basket | Pinch: Start/Pause | Open Palm: Exit",
                    (18, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def update(self, frame, hand_landmarks=None):
        h, w = frame.shape[:2]

        # Live basket movement from index finger position
        if hand_landmarks is not None:
            index_tip = hand_landmarks.landmark[8]
            self.target_x = float(index_tip.x * w)
            self.target_x = max(self.basket_w // 2 + 6, min(w - self.basket_w // 2 - 6, self.target_x))
            self.basket_x = (1.0 - self.follow_smooth) * self.basket_x + self.follow_smooth * self.target_x

        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        dt = min(max(dt, 0.001), 0.05)

        if self.game_state == "RUNNING":
            self._update_items(dt, w, h)

        self._draw_world(frame)

        # Pointer guide for index tracking
        if hand_landmarks is not None:
            ix = int(hand_landmarks.landmark[8].x * w)
            cv2.line(frame, (ix, 130), (ix, h - 55), (120, 120, 255), 1)
            cv2.circle(frame, (ix, h - 68), 5, (120, 120, 255), -1)

        if time.time() < self.hit_flash_until:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.14, frame, 0.86, 0, frame)

        self._draw_ui(frame)
