"""Playable Dino Game Controller integrated with app gesture pipeline."""
from controllers.base_controller import BaseController
import cv2
import json
import random
import time
from pathlib import Path


class DinoGameController(BaseController):
    def __init__(self):
        self.game_state = "READY"
        self.score = 0.0
        self.high_score = 0.0
        self.last_frame_time = time.time()

        self.ground_ratio = 0.78
        self.dino_x = 120
        self.dino_y = 0.0
        self.dino_w = 44
        self.dino_h = 52
        self.vel_y = 0.0
        self.gravity = 2200.0
        self.jump_velocity = -820.0
        self.on_ground = True
        self.jump_cooldown = 0.14
        self.last_jump = 0.0

        self.obstacles = []
        self.spawn_timer = 0.0
        self.next_spawn_in = 1.0
        self.base_speed = 360.0
        self.current_speed = self.base_speed
        self.max_speed = 760.0
        self.ground_offset = 0.0

        self.flash_until = 0.0
        self.highscore_path = Path("assets") / "dino_highscore.json"
        self._load_high_score()

    def _load_high_score(self):
        try:
            if self.highscore_path.exists():
                data = json.loads(self.highscore_path.read_text())
                self.high_score = float(data.get("high_score", 0.0))
        except Exception:
            self.high_score = 0.0

    def _save_high_score(self):
        try:
            self.highscore_path.parent.mkdir(parents=True, exist_ok=True)
            self.highscore_path.write_text(json.dumps({"high_score": int(self.high_score)}))
        except Exception:
            pass

    def _reset_run(self):
        self.score = 0.0
        self.vel_y = 0.0
        self.on_ground = True
        self.obstacles = []
        self.spawn_timer = 0.0
        self.next_spawn_in = random.uniform(0.9, 1.4)
        self.current_speed = self.base_speed
        self.ground_offset = 0.0
        self.last_jump = 0.0

    def _trigger_jump(self):
        now = time.time()
        if self.on_ground and (now - self.last_jump) > self.jump_cooldown:
            self.vel_y = self.jump_velocity
            self.on_ground = False
            self.last_jump = now

    def on_enter(self):
        self.game_state = "READY"
        self.last_frame_time = time.time()
        self._reset_run()
        print("Dino Game Started")

    def on_exit(self):
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()
        print(f"Dino Game Over - Score: {int(self.score)} | High: {int(self.high_score)}")

    def handle_command(self, command):
        if command == "PINCH":
            if self.game_state == "READY":
                self.game_state = "RUNNING"
                self._trigger_jump()
            elif self.game_state == "RUNNING":
                self._trigger_jump()
            elif self.game_state == "GAME_OVER":
                self._reset_run()
                self.game_state = "RUNNING"
                self._trigger_jump()

        elif command in ("NEXT_TRACK", "PREV_TRACK"):
            if self.game_state == "RUNNING":
                self._trigger_jump()

        elif command == "RESET":
            print("Exiting Dino Game")

    def _spawn_obstacle(self, frame_h):
        obstacle_type = random.choice(["small", "tall"])
        if obstacle_type == "small":
            width = random.randint(26, 36)
            height = random.randint(44, 58)
            color = (20, 180, 20)
        else:
            width = random.randint(28, 42)
            height = random.randint(62, 88)
            color = (40, 210, 40)

        ground_y = int(frame_h * self.ground_ratio)
        y = ground_y - height

        self.obstacles.append({
            "x": 1400,
            "y": y,
            "w": width,
            "h": height,
            "color": color,
        })

    def _rect_overlap(self, a, b):
        return not (
            a[0] + a[2] <= b[0] or
            b[0] + b[2] <= a[0] or
            a[1] + a[3] <= b[1] or
            b[1] + b[3] <= a[1]
        )

    def _update_game(self, dt, frame_w, frame_h):
        ground_y = int(frame_h * self.ground_ratio)

        # Dino physics
        if not self.on_ground:
            self.vel_y += self.gravity * dt
            self.dino_y += self.vel_y * dt

            floor_y = ground_y - self.dino_h
            if self.dino_y >= floor_y:
                self.dino_y = floor_y
                self.vel_y = 0.0
                self.on_ground = True
        else:
            self.dino_y = ground_y - self.dino_h

        # Speed ramp and score
        self.current_speed = min(self.max_speed, self.base_speed + self.score * 1.3)
        self.score += dt * 12.0

        # Spawn obstacles
        self.spawn_timer += dt
        if self.spawn_timer >= self.next_spawn_in:
            self.spawn_timer = 0.0
            self.next_spawn_in = random.uniform(0.9, 1.6)
            self._spawn_obstacle(frame_h)

        # Move obstacles
        for obstacle in self.obstacles:
            obstacle["x"] -= self.current_speed * dt

        self.obstacles = [o for o in self.obstacles if o["x"] + o["w"] > -10]

        # Collision check
        dino_rect = (
            int(self.dino_x + 6),
            int(self.dino_y + 6),
            int(self.dino_w - 12),
            int(self.dino_h - 8),
        )
        for obstacle in self.obstacles:
            obstacle_rect = (
                int(obstacle["x"]),
                int(obstacle["y"]),
                int(obstacle["w"]),
                int(obstacle["h"]),
            )
            if self._rect_overlap(dino_rect, obstacle_rect):
                self.game_state = "GAME_OVER"
                self.flash_until = time.time() + 0.2
                if self.score > self.high_score:
                    self.high_score = self.score
                    self._save_high_score()
                break

        # Ground scroll offset
        self.ground_offset = (self.ground_offset + self.current_speed * dt) % 60

    def _draw_world(self, frame):
        h, w = frame.shape[:2]
        ground_y = int(h * self.ground_ratio)

        # Ground
        cv2.line(frame, (0, ground_y), (w, ground_y), (180, 180, 180), 3)

        # Moving ground dashes
        start = int(-self.ground_offset)
        x = start
        while x < w:
            cv2.line(frame, (x, ground_y + 10), (x + 30, ground_y + 10), (140, 140, 140), 2)
            x += 60

        # Dino body
        dino_x = int(self.dino_x)
        dino_y = int(self.dino_y)
        cv2.rectangle(frame, (dino_x, dino_y), (dino_x + self.dino_w, dino_y + self.dino_h), (230, 230, 230), -1)
        cv2.rectangle(frame, (dino_x + 10, dino_y + 10), (dino_x + 16, dino_y + 16), (0, 0, 0), -1)  # eye
        cv2.rectangle(frame, (dino_x + self.dino_w - 8, dino_y + 30), (dino_x + self.dino_w, dino_y + 38), (40, 40, 40), -1)

        # Dino legs (simple animation)
        leg_y = dino_y + self.dino_h
        if self.on_ground and self.game_state == "RUNNING":
            phase = int(time.time() * 10) % 2
            if phase == 0:
                cv2.line(frame, (dino_x + 12, leg_y), (dino_x + 8, leg_y + 12), (230, 230, 230), 3)
                cv2.line(frame, (dino_x + 28, leg_y), (dino_x + 32, leg_y + 12), (230, 230, 230), 3)
            else:
                cv2.line(frame, (dino_x + 12, leg_y), (dino_x + 14, leg_y + 12), (230, 230, 230), 3)
                cv2.line(frame, (dino_x + 28, leg_y), (dino_x + 24, leg_y + 12), (230, 230, 230), 3)

        # Obstacles
        for obstacle in self.obstacles:
            x1 = int(obstacle["x"])
            y1 = int(obstacle["y"])
            x2 = x1 + int(obstacle["w"])
            y2 = y1 + int(obstacle["h"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), obstacle["color"], -1)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (10, 80, 10), 1)
            cv2.circle(frame, (x1 + 6, y1 + 10), 2, (0, 0, 0), -1)

    def _draw_ui(self, frame):
        h, w = frame.shape[:2]

        cv2.putText(frame, "DINO RUNNER", (w // 2 - 120, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        cv2.putText(frame, f"Score: {int(self.score)}", (40, 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 255, 80), 2)
        cv2.putText(frame, f"Best: {int(self.high_score)}", (40, 82),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)
        cv2.putText(frame, f"Speed: {int(self.current_speed)}", (40, 114),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (170, 170, 255), 1)

        if self.game_state == "READY":
            cv2.putText(frame, "PINCH TO START", (w // 2 - 140, h // 2 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 120), 2)
            cv2.putText(frame, "PINCH / SWIPE TO JUMP", (w // 2 - 170, h // 2 + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 1)

        elif self.game_state == "GAME_OVER":
            cv2.putText(frame, "GAME OVER", (w // 2 - 110, h // 2 - 16),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (40, 40, 255), 3)
            cv2.putText(frame, "PINCH TO RESTART", (w // 2 - 145, h // 2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        cv2.putText(frame, "Pinch: Jump/Start | Two-finger swipe: Jump | Open Palm: Exit",
                    (22, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def update(self, frame):
        h, w = frame.shape[:2]

        now = time.time()
        dt = now - self.last_frame_time
        self.last_frame_time = now
        dt = min(max(dt, 0.001), 0.05)

        if self.game_state == "RUNNING":
            self._update_game(dt, w, h)

        self._draw_world(frame)

        if time.time() < self.flash_until:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 255), -1)
            cv2.addWeighted(overlay, 0.18, frame, 0.82, 0, frame)

        self._draw_ui(frame)
