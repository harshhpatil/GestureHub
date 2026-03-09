import cv2
import mediapipe as mp
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
# Top-level menu items (games accessible via submenu)
MENU_ITEMS = ["MUSIC", "DRAWING", "SYSTEM", "GAMES"]
GAME_ITEMS = ["DINO", "CATCH", "FRUIT"]
MUSIC_ITEMS = ["LOCAL MUSIC", "SPOTIFY"]


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
    cv2.rectangle(overlay, (panel_x1, panel_y1), (panel_x2, panel_y2), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)
    
    # Title at top of panel
    title_y = panel_y1 + int(panel_height * 0.12)
    title_font_scale = max(0.7, w / 800)  # Scale font based on width
    cv2.putText(
        frame, title, 
        (w // 2 - int(len(title) * title_font_scale * 25), title_y),
        cv2.FONT_HERSHEY_SIMPLEX, title_font_scale, (0, 255, 255), 2
    )
    
    # Calculate menu item positions
    item_start_y = panel_y1 + int(panel_height * 0.28)
    item_spacing = int(panel_height * 0.18)
    item_font_scale = max(0.6, w / 900)
    
    # Draw menu items
    for i, item in enumerate(menu_items):
        y = item_start_y + i * item_spacing
        
        # Highlight selected item with green background
        if i == selected_index:
            highlight_x1 = panel_x1 + int(panel_width * 0.05)
            highlight_x2 = panel_x2 - int(panel_width * 0.05)
            highlight_y1 = y - int(item_spacing * 0.35)
            highlight_y2 = y + int(item_spacing * 0.25)
            cv2.rectangle(frame, (highlight_x1, highlight_y1), (highlight_x2, highlight_y2), (0, 255, 0), -1)
            text_color = (0, 0, 0)  # Black text on green background
        else:
            text_color = (255, 255, 255)  # White text
        
        # Draw item text (centered)
        text_x = panel_x1 + int(panel_width * 0.08)
        cv2.putText(
            frame, item, (text_x, y),
            cv2.FONT_HERSHEY_SIMPLEX, item_font_scale, text_color, 2
        )
    
    # Instructions at bottom
    instruction_y = panel_y2 - int(panel_height * 0.08)
    instruction_font_scale = max(0.35, w / 1200)
    cv2.putText(
        frame,
        "Swipe to Navigate | Pinch to Select",
        (panel_x1 + int(panel_width * 0.05), instruction_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        instruction_font_scale,
        (180, 180, 180),
        1,
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
    
    # All menu states use MenuGestureController for navigation
    if current_state in ("MENU", "GAME_MENU", "MUSIC_MENU", "SPOTIFY_DEVICE_MENU"):
        return menu_gesture_controller
    
    # IDLE state: route to module-specific gesture controller
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
    model_complexity=0,  # Fastest model
    min_detection_confidence=0.6,  # Lower for better detection
    min_tracking_confidence=0.5,  # Lower for smoother tracking
)

cap = cv2.VideoCapture(1, cv2.CAP_ANY)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 30)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffer for lower latency

if not cap.isOpened():
    print("Camera not accessible. Run: v4l2-ctl --list-devices")
    exit()


# ── Main loop ──────────────────────────────────────────────
while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    gesture = "NO_HAND"
    stable_gesture = "NO_HAND"
    gesture_controller = get_active_gesture_controller()

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            landmarks = []
            h, w, c = frame.shape

            for id, lm in enumerate(hand_landmarks.landmark):
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                landmarks.append((id, cx, cy))

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

    # Common: gesture label (small, top-left corner)
    cv2.putText(
        frame, stable_gesture, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
    )

    if current_state == "MENU":
        # Top-level menu: MUSIC, SYSTEM, GAMES
        draw_menu(frame, MENU_ITEMS, state_machine.get_menu_index(), "GESTURE HUB")

    elif current_state == "GAME_MENU":
        # Game submenu: DINO, CATCH, FRUIT
        draw_menu(frame, GAME_ITEMS, state_machine.get_menu_index(), "SELECT GAME")

    elif current_state == "MUSIC_MENU":
        # Music submenu: LOCAL MUSIC, SPOTIFY
        draw_menu(frame, MUSIC_ITEMS, state_machine.get_menu_index(), "MUSIC MODE")

    elif current_state == "SPOTIFY_DEVICE_MENU":
        # Spotify device selection menu
        devices = state_machine.spotify_devices
        if devices:
            device_names = [d if isinstance(d, str) else d.get('name', 'Unknown Device') for d in devices]
            draw_menu(frame, device_names, state_machine.get_menu_index(), "SPOTIFY DEVICES")
        else:
            draw_menu(frame, ["No devices found", "Open Spotify App"], 0, "SPOTIFY DEVICES")

    elif current_state == "IDLE":
        # IDLE state: delegate rendering to active module (no menu overlay)
        active_mode = mode_manager.get_active_mode()
        if active_mode == "drawing":
            hand_landmarks = None
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
            frame = drawing_board.update(frame, hand_landmarks)
        elif active_mode == "catch":
            hand_landmarks = None
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
            catch.update(frame, hand_landmarks)
        else:
            mode_manager.update(frame)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break


# ── Cleanup ────────────────────────────────────────────────
hands.close()
cap.release()
cv2.destroyAllWindows()
