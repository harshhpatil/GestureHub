import cv2
import mediapipe as mp
import time
from controllers.music_controller import MusicController
from controllers.drawing_controller import DrawingBoardController
from command_layer.command_dispatcher import CommandDispatcher
from controllers.gesture_controller import (
    MenuGestureController,
    MusicGestureController,
    SystemGestureController,
    GameGestureController,
)
from controllers.system_controller import SystemController
from controllers.dino_controller import DinoGameController
from controllers.catch_controller import CatchGameController
from controllers.fruit_controller import FruitGameController
from networking.server_listener import ServerListener
from core.mode_manager import ModeManager
from core.state_machine import StateMachine
import threading


# ── Menu UI configuration ──────────────────────────────────
MENU_ITEMS = ["MUSIC", "DRAWING", "SYSTEM", "GAMES"]
GAME_ITEMS = ["DINO", "CATCH", "FRUIT"]
MUSIC_ITEMS = ["LOCAL MUSIC", "SPOTIFY"]

# ── HUD accent colour (matches dashboard #00FFCC cyan) ────
HUD_ACCENT = (204, 255, 0)   # BGR equivalent of RGB(0, 255, 204)

# ── "Waiting for Hand" pulse animation ─────────────────────
PULSE_FREQ = 2       # cycles per second
PULSE_MAX = 255      # peak green-channel intensity


def draw_hud_bar(frame, y1, y2):
    """Draw a semi-transparent dark bar across the frame."""
    overlay = frame.copy()
    h, w = frame.shape[:2]
    cv2.rectangle(overlay, (0, y1), (w, y2), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)


def draw_menu(frame, menu_items, selected_index, title="GESTURE HUB"):
    """
    Render a responsive menu overlay on the frame.
    Scales all UI elements relative to frame dimensions.
    """
    h, w = frame.shape[:2]

    # Calculate responsive dimensions
    panel_width = int(w * 0.75)
    panel_height = int(h * 0.7)
    panel_x1 = (w - panel_width) // 2
    panel_y1 = int(h * 0.15)
    panel_x2 = panel_x1 + panel_width
    panel_y2 = panel_y1 + panel_height

    # Semi-transparent dark background for menu
    overlay = frame.copy()
    cv2.rectangle(overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.70, frame, 0.30, 0, frame)

    # Border
    cv2.rectangle(frame, (panel_x1, panel_y1), (panel_x2, panel_y2), (60, 60, 60), 1)

    # Title
    title_y = panel_y1 + int(panel_height * 0.12)
    title_font_scale = max(0.7, w / 800)
    cv2.putText(
        frame, title,
        (w // 2 - int(len(title) * title_font_scale * 12), title_y),
        cv2.FONT_HERSHEY_SIMPLEX, title_font_scale, HUD_ACCENT, 2,
    )

    # Menu items
    item_start_y = panel_y1 + int(panel_height * 0.28)
    item_spacing = int(panel_height * 0.18)
    item_font_scale = max(0.6, w / 900)

    for i, item in enumerate(menu_items):
        y = item_start_y + i * item_spacing

        if i == selected_index:
            hx1 = panel_x1 + int(panel_width * 0.05)
            hx2 = panel_x2 - int(panel_width * 0.05)
            hy1 = y - int(item_spacing * 0.35)
            hy2 = y + int(item_spacing * 0.25)
            # Accent highlight
            ov = frame.copy()
            cv2.rectangle(ov, (hx1, hy1), (hx2, hy2), HUD_ACCENT, -1)
            cv2.addWeighted(ov, 0.85, frame, 0.15, 0, frame)
            text_color = (0, 0, 0)
        else:
            text_color = (200, 200, 200)

        text_x = panel_x1 + int(panel_width * 0.08)
        cv2.putText(frame, item, (text_x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, item_font_scale, text_color, 2)

    # Instructions
    instruction_y = panel_y2 - int(panel_height * 0.08)
    instruction_font_scale = max(0.35, w / 1200)
    cv2.putText(
        frame, "Swipe to Navigate  |  Pinch to Select",
        (panel_x1 + int(panel_width * 0.05), instruction_y),
        cv2.FONT_HERSHEY_SIMPLEX, instruction_font_scale, (140, 140, 140), 1,
    )


# ── Initialize systems ─────────────────────────────────────
music = MusicController()
drawing_board = DrawingBoardController()
system = SystemController()
dino = DinoGameController()
catch = CatchGameController()
fruit = FruitGameController()

dispatcher = CommandDispatcher()
state_machine = StateMachine(dispatcher)
mode_manager = ModeManager()
mode_manager.set_state_machine(state_machine)

mode_manager.register("system", system)
mode_manager.register("music", music)
mode_manager.register("drawing", drawing_board)
mode_manager.register("dino", dino)
mode_manager.register("catch", catch)
mode_manager.register("fruit", fruit)

dispatcher.register_router(mode_manager)

menu_gesture_controller = MenuGestureController()
music_gesture_controller = MusicGestureController()
system_gesture_controller = SystemGestureController()
game_gesture_controller = GameGestureController()


def get_active_gesture_controller():
    """Return the appropriate gesture controller based on current state."""
    current_state = state_machine.get_state()

    if current_state in ("MENU", "GAME_MENU", "MUSIC_MENU", "SPOTIFY_DEVICE_MENU"):
        return menu_gesture_controller

    active_mode = mode_manager.get_active_mode()
    if active_mode == "music":
        return music_gesture_controller
    if active_mode == "system":
        return system_gesture_controller
    if active_mode in ["dino", "catch", "fruit"]:
        return game_gesture_controller
    if active_mode == "drawing":
        return menu_gesture_controller

    return menu_gesture_controller


# Server listener thread (daemon – auto-exits with main)
listener = ServerListener(dispatcher)
listener_thread = threading.Thread(target=listener.start, daemon=True)
listener_thread.start()


# ── MediaPipe setup ────────────────────────────────────────
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.5,
)


# ── Camera initialisation with graceful fallback ──────────
def open_camera():
    """Try camera index 1, then fall back to 0."""
    for idx in (1, 0):
        cap = cv2.VideoCapture(idx, cv2.CAP_ANY)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 30)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            print(f"Camera opened on index {idx}")
            return cap
        cap.release()
    return None


cap = open_camera()
if cap is None:
    print("ERROR: No camera accessible. Run: v4l2-ctl --list-devices")
    exit(1)


# ── FPS counter ────────────────────────────────────────────
_fps_time = time.time()
_fps_val = 0
_fps_count = 0

# ── Calibration / waiting-for-hand state ───────────────────
_hand_seen = False


# ── Main loop ──────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w = frame.shape[:2]
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    # ── FPS calculation ────────────────────────────────────
    _fps_count += 1
    elapsed = time.time() - _fps_time
    if elapsed >= 0.5:
        _fps_val = int(_fps_count / elapsed)
        _fps_count = 0
        _fps_time = time.time()

    gesture = "NO_HAND"
    stable_gesture = "NO_HAND"
    gesture_controller = get_active_gesture_controller()

    if results.multi_hand_landmarks:
        _hand_seen = True
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            landmarks = []

            for lm_id, lm in enumerate(hand_landmarks.landmark):
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                landmarks.append((lm_id, cx, cy))

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            hand_label = results.multi_handedness[idx].classification[0].label

            fingers = gesture_controller.process_landmarks(landmarks, hand_label)
            gesture = gesture_controller.classify_gesture(fingers)

            hand_pos = (landmarks[0][1], landmarks[0][2])

            stable_gesture = gesture_controller.stabilize(gesture)
            commands = gesture_controller.detect_commands(
                stable_gesture, hand_pos, landmarks
            )

            state_machine.handle_commands(commands)
    else:
        stable_gesture = gesture_controller.stabilize("NO_HAND")

    # ── State-driven rendering ─────────────────────────────
    current_state = state_machine.get_state()

    if current_state == "MENU":
        draw_menu(frame, MENU_ITEMS, state_machine.get_menu_index(), "GESTURE HUB")

    elif current_state == "GAME_MENU":
        draw_menu(frame, GAME_ITEMS, state_machine.get_menu_index(), "SELECT GAME")

    elif current_state == "MUSIC_MENU":
        draw_menu(frame, MUSIC_ITEMS, state_machine.get_menu_index(), "MUSIC MODE")

    elif current_state == "SPOTIFY_DEVICE_MENU":
        devices = state_machine.spotify_devices
        if devices:
            device_names = [d if isinstance(d, str) else d.get('name', 'Unknown Device') for d in devices]
            draw_menu(frame, device_names, state_machine.get_menu_index(), "SPOTIFY DEVICES")
        else:
            draw_menu(frame, ["No devices found", "Open Spotify App"], 0, "SPOTIFY DEVICES")

    elif current_state == "IDLE":
        active_mode = mode_manager.get_active_mode()
        if active_mode == "drawing":
            hl = results.multi_hand_landmarks[0] if results.multi_hand_landmarks else None
            frame = drawing_board.update(frame, hl)
        elif active_mode == "catch":
            hl = results.multi_hand_landmarks[0] if results.multi_hand_landmarks else None
            catch.update(frame, hl)
        else:
            mode_manager.update(frame)

    # ── HUD overlay (top bar) ──────────────────────────────
    draw_hud_bar(frame, 0, 32)

    # Gesture label
    cv2.putText(frame, stable_gesture, (10, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, HUD_ACCENT, 1)

    # FPS
    cv2.putText(frame, f"{_fps_val} FPS", (w - 80, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 160), 1)

    # Mode indicator (right of gesture label)
    active_mode = mode_manager.get_active_mode()
    if active_mode and current_state == "IDLE":
        cv2.putText(frame, active_mode.upper(), (w // 2 - 30, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)

    # ── "Waiting for Hand" calibration overlay ─────────────
    if not _hand_seen:
        draw_hud_bar(frame, h // 2 - 30, h // 2 + 30)
        pulse = int(abs((time.time() * PULSE_FREQ % 2) - 1) * PULSE_MAX)
        cv2.putText(frame, "Waiting for Hand...", (w // 2 - 120, h // 2 + 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (pulse, 255, pulse), 2)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break


# ── Cleanup ────────────────────────────────────────────────
hands.close()
cap.release()
cv2.destroyAllWindows()
