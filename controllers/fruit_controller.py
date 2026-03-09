"""
Fruit Slice Game Controller - Slice fruits by swiping hand
"""
from controllers.base_controller import BaseController
import cv2
import random
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def _load_fruit_image(filename):
    image = cv2.imread(str(ASSETS_DIR / filename), cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"[WARN] Missing fruit image: {ASSETS_DIR / filename}")
    return image


def _prepare_sprite(png, radius):
    if png is None:
        return None, None

    target_size = max(24, radius * 2)
    resized = cv2.resize(png, (target_size, target_size), interpolation=cv2.INTER_AREA)

    if resized.shape[2] == 4:
        sprite_bgr = resized[:, :, :3]
        alpha = (resized[:, :, 3] / 255.0)[:, :, None]
        return sprite_bgr, alpha

    return resized[:, :, :3], None


def _overlay_sprite(frame, sprite_bgr, sprite_alpha, center_x, center_y):
    if sprite_bgr is None:
        return False

    h, w = sprite_bgr.shape[:2]

    x1 = center_x - w // 2
    y1 = center_y - h // 2
    x2 = x1 + w
    y2 = y1 + h

    if x2 <= 0 or y2 <= 0 or x1 >= frame.shape[1] or y1 >= frame.shape[0]:
        return False

    crop_x1 = max(0, x1)
    crop_y1 = max(0, y1)
    crop_x2 = min(frame.shape[1], x2)
    crop_y2 = min(frame.shape[0], y2)

    overlay_bgr = sprite_bgr[crop_y1 - y1:crop_y2 - y1, crop_x1 - x1:crop_x2 - x1]

    if sprite_alpha is not None:
        alpha = sprite_alpha[crop_y1 - y1:crop_y2 - y1, crop_x1 - x1:crop_x2 - x1]
        frame_region = frame[crop_y1:crop_y2, crop_x1:crop_x2]
        frame[crop_y1:crop_y2, crop_x1:crop_x2] = (
            alpha * overlay_bgr + (1.0 - alpha) * frame_region
        ).astype("uint8")
    else:
        frame[crop_y1:crop_y2, crop_x1:crop_x2] = overlay_bgr

    return True


class _FallingFruit:
    def __init__(self, frame_w, image_pool):
        self.x = random.randint(60, max(61, frame_w - 60))
        self.y = -40
        self.speed = random.randint(5, 10)
        self.radius = random.randint(20, 28)
        self.cut = False
        self.image = random.choice(image_pool) if image_pool else None
        self.sprite_bgr, self.sprite_alpha = _prepare_sprite(self.image, self.radius)
        self.color = random.choice([(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 0, 255)])

    def move(self):
        self.y += self.speed

    def draw(self, frame):
        if self.cut:
            return

        drawn = _overlay_sprite(frame, self.sprite_bgr, self.sprite_alpha, self.x, self.y)
        if not drawn:
            cv2.circle(frame, (self.x, self.y), self.radius, self.color, -1)
            cv2.circle(frame, (self.x - 8, self.y - 8), 8, (255, 255, 255), -1)

class FruitGameController(BaseController):
    def __init__(self):
        self.game_active = False
        self.score = 0
        self.high_score = 0
        self.lives = 3
        self.combo = 0
        self.instruction_text = "Swipe: Slice Fruits | Pinch: Start/Stop | Palm: Exit"
        self.spawn_interval = 1.0
        self.max_fruits = 6
        self.last_spawn_time = time.time()
        self.fruits = []
        self.debug_assets_text = ""
        self.image_pool = [
            _load_fruit_image("apple.png"),
            _load_fruit_image("orange.png"),
            _load_fruit_image("banana.png"),
            _load_fruit_image("watermelon.png"),
        ]
        self.image_pool = [img for img in self.image_pool if img is not None]
        self.using_images = len(self.image_pool) > 0
        self.debug_assets_text = "Sprites: ON" if self.using_images else "Sprites: OFF (fallback shapes)"
        
    def on_enter(self):
        print("Fruit Slice Game Started")
        self.game_active = False
        self.score = 0
        self.lives = 3
        self.combo = 0
        self.fruits.clear()
        self.last_spawn_time = time.time()
        
    def on_exit(self):
        print(f"Fruit Game Over - Score: {self.score} | High: {self.high_score}")
        if self.score > self.high_score:
            self.high_score = self.score
        self.game_active = False
    
    def handle_command(self, command):
        """Map gestures to game actions."""
        if command == "PINCH":
            self.game_active = not self.game_active
            status = "STARTED" if self.game_active else "PAUSED"
            print(f"Game {status}")
        elif command == "NEXT_TRACK":  # Right swipe
            if self.game_active:
                self.score += 10
                self.combo += 1
                print(f"Fruit sliced! Score: {self.score} | Combo: {self.combo}")
        elif command == "PREV_TRACK":  # Left swipe
            if self.game_active:
                self.score += 10
                self.combo += 1
                print(f"Fruit sliced! Score: {self.score} | Combo: {self.combo}")
        elif command == "RESET":
            print("Exiting Fruit Game")

    def _spawn_fruit(self, frame_w):
        if len(self.fruits) >= self.max_fruits:
            return
        self.fruits.append(_FallingFruit(frame_w, self.image_pool))

    def _update_fruits(self, frame_h):
        for fruit in self.fruits:
            fruit.move()

        self.fruits = [f for f in self.fruits if not f.cut and f.y < frame_h + 80]
            
    def update(self, frame):
        """Render game UI onto frame."""
        h, w = frame.shape[:2]

        if self.game_active and (time.time() - self.last_spawn_time) >= self.spawn_interval:
            self._spawn_fruit(w)
            self.last_spawn_time = time.time()

        if self.game_active:
            self._update_fruits(h)
            for fruit in self.fruits:
                fruit.draw(frame)
        
        # Game title
        cv2.putText(frame, "FRUIT SLICE GAME", (w//2 - 140, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
        
        # Score and stats
        cv2.putText(frame, f"Score: {self.score} | Lives: {self.lives} | Combo: {self.combo}",
                    (40, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (0, 255, 0), 2)
        
        # Game state
        game_state = "RUNNING" if self.game_active else "PAUSED"
        state_color = (0, 255, 0) if self.game_active else (0, 0, 255)
        cv2.putText(frame, f"Status: {game_state}", (40, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, state_color, 1)
        
        # Instructions
        cv2.putText(frame, self.instruction_text, (30, h - 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

        cv2.putText(frame, self.debug_assets_text, (30, h - 65),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 255, 0) if self.using_images else (0, 0, 255), 1)
        
        # Game area
        cv2.rectangle(frame, (10, 160), (w - 10, h - 60), (100, 100, 100), 1)
        
        # Swipe indicator
        if self.combo > 0:
            cv2.putText(frame, f"Nice Combo! x{self.combo}",
                        (w//2 - 80, 200), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 255), 2)
