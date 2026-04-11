# GestureHUB Technical Report

Date: April 11, 2026
Audience: Team, examiner, and maintainers

## 1. Executive Summary

GestureHUB is a webcam-driven gesture control platform built in Python. It uses MediaPipe hand tracking to recognize gestures, then routes those gestures into a menu/state layer and finally into feature-specific controllers for music, system actions, drawing, and games.

The project is organized as a desktop application with a live camera UI, a separate GUI launcher, and a small HTTP command server for dashboard/mobile integration. The production runtime is the controller-based path under `app/main.py`; the standalone scripts in `games/` are legacy prototypes retained as references and for packaging assets.

## 2. High-Level Architecture

The architecture is layered and event-driven:

1. Camera and hand tracking capture a frame stream.
2. MediaPipe extracts hand landmarks from each frame.
3. Gesture controllers classify landmark shapes and motion into semantic commands such as `PINCH`, `NEXT_TRACK`, `RESET`, and `SWIPE_LEFT`.
4. The state machine decides whether the user is in the top menu, a sub-menu, or idle in an active mode.
5. The mode manager activates the selected controller and forwards commands to it.
6. The active controller updates the frame overlay and performs side effects such as music playback, drawing, or system control.
7. The command dispatcher mirrors local commands to the server, and the server can also feed commands back into the app.

In short, the project is split into three responsibilities:

- Perception: detect hands and gestures.
- Decision: choose what the gesture means in the current app state.
- Execution: perform the action in the active feature module.

## 3. Runtime Entry Points

The main runtime starts in `app/main.py`. That file does the following:

- Initializes the controllers and shared routing objects.
- Starts the command server listener in a background daemon thread.
- Configures MediaPipe Hands.
- Opens the webcam with a fallback from camera index 1 to 0.
- Enters the frame-processing loop.

The GUI launcher in `app/gui_launcher.py` is the second entry point. It provides a Tkinter control panel that can:

- Launch the main gesture app.
- Launch the command server.
- Show process state and logs.
- Offer direct launch buttons for individual modes.

The server entry point in `app/run_server.py` starts the FastAPI app under Uvicorn on port 8000.

## 4. End-to-End Data Flow

This is the actual frame-to-action path used by the application:

1. `cv2.VideoCapture` reads a frame from the webcam.
2. The frame is flipped horizontally for mirrored interaction.
3. MediaPipe converts the frame to RGB and returns hand landmarks.
4. The active gesture controller converts landmarks into finger-state vectors.
5. A gesture label is classified from finger states.
6. The gesture is stabilized over several frames to reduce jitter.
7. The controller emits one or more commands.
8. The `StateMachine` consumes the commands and decides whether they affect navigation or the current mode.
9. The `CommandDispatcher` forwards commands to the `ModeManager` and mirrors them to the local command server.
10. The active module updates the frame overlay and/or executes the side effect.
11. OpenCV draws the HUD, menu, or mode-specific UI and displays the frame.

This design keeps gesture recognition independent from feature logic, which makes the system easier to extend.

## 5. Core Modules and Their Roles

### `app/main.py`

This is the production orchestrator.

It owns the main loop, creates all controllers, and decides which gesture controller should be active based on the current app state. It also renders the top-level menus and the global HUD overlay.

Key responsibilities:

- Bootstrapping the app.
- Managing camera and MediaPipe setup.
- Selecting the active gesture controller.
- Handling startup mode via `GESTUREHUB_START_MODE` or CLI argument.
- Running the frame loop and rendering overlay UI.

### `core/state_machine.py`

The state machine handles navigation logic.

States include:

- `MENU`
- `GAME_MENU`
- `MUSIC_MENU`
- `SPOTIFY_DEVICE_MENU`
- `IDLE`

It interprets high-level commands such as `NEXT_TRACK`, `PREV_TRACK`, `PINCH`, and `RESET`, then decides whether those commands should move through menus or be forwarded to the active mode.

### `core/mode_manager.py`

The mode manager is the execution router.

It maintains the active feature module and knows how to switch between `music`, `drawing`, `system`, `dino`, `catch`, and `fruit`. It also handles a few special setup commands for Spotify device discovery and music mode selection.

### `command_layer/command_dispatcher.py`

This is the command bridge.

It sends local commands to the `ModeManager`, then asynchronously POSTs them to the HTTP server so the command stream can be shared with remote clients. It also keeps a short recent-command buffer to suppress echo loops.

### `networking/command_server.py`

This is the FastAPI-based command server.

It provides:

- `POST /command` for accepting commands.
- `GET /command` for polling the next command.
- `WS /ws` for websocket clients.

The server stores commands in memory and broadcasts them to websocket clients when they arrive.

### `networking/server_listener.py`

This is the client-side polling loop.

It repeatedly requests `GET /command` and dispatches any received actions into the local app. Combined with the dispatcher, this creates a local command sync path without requiring a complex message broker.

### `gesture_engine/motion_gesture.py`

This module detects motion-based gestures such as swipes and scrolls using a short position history buffer.

It is used by the gesture controllers to translate repeated hand movement into discrete commands.

### `controllers/gesture_controller.py`

This is the gesture interpretation layer.

It takes landmark arrays from MediaPipe and produces semantic app commands. There are four controller variants:

- `MenuGestureController` for menu navigation.
- `MusicGestureController` for playback and track controls.
- `SystemGestureController` for OS-level actions.
- `GameGestureController` for game navigation and start/stop actions.

These controllers share common gesture classification logic but differ in the command mapping.

### `controllers/music_controller.py`

This controller handles both local MP3 playback and Spotify control.

It can:

- Load local tracks from `assets/` and `assets/music/`.
- Play, pause, skip, and rewind local audio with `pygame`.
- Authenticate with Spotify using OAuth via `spotipy`.
- Query available Spotify devices and transfer playback.
- Render music status and device selection overlays.

### `controllers/drawing_controller.py`

This controller implements the drawing board.

It uses gesture-based states to switch between drawing, erasing, color switching, and neutral mode. A NumPy canvas is layered onto the camera frame so the drawing persists across frames.

### `controllers/system_controller.py`

This controller maps gestures to desktop actions.

It uses `pyautogui` and system utilities to:

- Change volume.
- Scroll.
- Switch tabs.
- Trigger a left click.
- Take a screenshot.

It also keeps track of whether the Alt-tab switcher is open so it can safely release Alt on exit.

### `controllers/dino_controller.py`, `controllers/catch_controller.py`, `controllers/fruit_controller.py`

These are the integrated game controllers.

They implement the full game loop for each mode, including:

- Game state transitions such as READY, RUNNING, PAUSED, and GAME_OVER.
- Score tracking and high-score persistence.
- Frame-based animation and collision logic.
- Gesture-to-action mapping for pinch, swipe, and open-palm exit.

These controllers are the production versions used by `app/main.py`.

### `games/`

These files are older standalone prototypes of the same game ideas.

They are not the primary runtime path, but they remain in the repository and are included in build packaging. Their value is historical and as reference material for how the game concepts evolved.

## 6. Gesture Logic in Detail

Gesture recognition is split into two levels.

### Level 1: Landmark-to-finger-state conversion

`BaseGestureController.process_landmarks()` takes MediaPipe landmark coordinates and turns them into a compact five-element finger state vector.

It detects:

- Thumb up/down/sideways.
- Index, middle, ring, and pinky extension.

### Level 2: Finger-state-to-gesture classification

`classify_gesture()` maps the finger state vector to labels such as:

- `FIST`
- `INDEX`
- `TWO_FINGERS`
- `OPEN_PALM`
- `PEACE_SIGN`
- `ROCK`
- `THUMBS_UP`
- `THUMBS_DOWN`

### Stabilization

`stabilize()` requires several consecutive identical readings before a gesture becomes active. This prevents flickering and reduces accidental transitions.

### Motion gestures

For swipe and scroll interactions, the controllers store recent hand positions and feed them into `MotionGestureDetector`.

That detector emits commands like:

- `SWIPE_LEFT`
- `SWIPE_RIGHT`
- `SCROLL_UP`
- `SCROLL_DOWN`

## 7. Mode and State Behavior

The app uses a menu-first interaction model:

- Open palm returns the user to menu in most modes.
- Two-finger swipe usually navigates between menu entries or tracks.
- Pinch selects menu items or starts/stops a mode.
- Special gestures in each module are mapped to the most relevant action for that module.

Examples:

- In the top menu, swipe left/right changes the selected item and pinch activates it.
- In music mode, swipe left/right skips tracks, thumb gestures control volume, and pinch handles menu/device selection.
- In system mode, thumb gestures control volume continuously, two-finger movement handles swipe and scroll, and a rock gesture triggers a screenshot.
- In games, pinch generally starts or restarts the game and swipes are used for in-game actions where appropriate.

## 8. Libraries Used, Where They Are Used, and Why

### `opencv-python`

Used in:

- `app/main.py`
- `controllers/drawing_controller.py`
- `controllers/music_controller.py`
- `controllers/system_controller.py`
- `controllers/dino_controller.py`
- `controllers/catch_controller.py`
- `controllers/fruit_controller.py`
- `games/`

Why:

- Capture webcam frames.
- Draw UI overlays, shapes, and text.
- Blend transparent layers.
- Show the live gesture interface.

How:

- `cv2.VideoCapture` reads the camera.
- `cv2.cvtColor` converts BGR to RGB for MediaPipe.
- `cv2.putText`, `cv2.rectangle`, `cv2.circle`, `cv2.line` render overlays.
- `cv2.addWeighted` creates translucent HUD and canvas effects.

### `mediapipe`

Used in:

- `app/main.py`
- `games/`
- gesture detection pipeline

Why:

- It provides ready-made, fast hand landmark detection with good real-time performance.

How:

- `mp.solutions.hands.Hands(...)` creates the hand tracker.
- `hands.process(frame_rgb)` returns landmarks and handedness.
- Landmarks are converted into normalized coordinates for gesture rules.

### `numpy`

Used in:

- `controllers/drawing_controller.py`

Why:

- It provides efficient image-sized arrays for the persistent drawing canvas.

How:

- `np.zeros_like(frame)` creates a blank overlay canvas.
- The canvas is composited back onto the live frame each update.

### `pygame`

Used in:

- `controllers/music_controller.py`

Why:

- It is the simplest bundled audio playback layer for local MP3 control.

How:

- `pygame.mixer.init()` starts the audio backend.
- `pygame.mixer.music.load()`, `.play()`, `.pause()`, and `.unpause()` handle local playback.

### `spotipy`

Used in:

- `controllers/music_controller.py`

Why:

- It wraps the Spotify Web API with OAuth support for playback control and device discovery.

How:

- `SpotifyOAuth(...)` handles authentication.
- `Spotify(auth_manager=...)` creates the client.
- `devices()`, `pause_playback()`, `start_playback()`, `next_track()`, and `previous_track()` implement control.

### `pyautogui`

Used in:

- `controllers/system_controller.py`

Why:

- It is a cross-platform way to automate keyboard and mouse actions.

How:

- `keyDown`, `keyUp`, `press`, `hotkey`, `click`, `scroll`, and `screenshot` implement the system actions.

### `requests`

Used in:

- `command_layer/command_dispatcher.py`
- `networking/server_listener.py`

Why:

- It provides simple HTTP communication between the app and the local command server.

How:

- The dispatcher POSTs commands asynchronously to `/command`.
- The listener polls `/command` for remote actions.

### `fastapi`

Used in:

- `networking/command_server.py`

Why:

- It makes the command server lightweight, typed, and easy to expose over HTTP and WebSocket.

How:

- Defines POST, GET, and websocket endpoints.
- Handles CORS so the dashboard/mobile client can connect.

### `uvicorn`

Used in:

- `app/run_server.py`

Why:

- It is the ASGI server that runs the FastAPI app.

How:

- `uvicorn.run(...)` hosts the server on port 8000.

### `psutil`

Used in:

- `app/gui_launcher.py`

Why:

- It lets the launcher inspect live process memory and running status.

How:

- `psutil.Process(pid)` is used to display memory and status in the launcher UI.

### `tkinter` / `ttk`

Used in:

- `app/gui_launcher.py`

Why:

- It provides the desktop control panel for launching the app and server.

How:

- Tkinter builds the window, notebook tabs, buttons, logs, and process monitoring panels.

### Standard library modules

Used throughout the project:

- `threading` for background server and HTTP sends.
- `subprocess` for launching the app/server and controlling system audio.
- `pathlib` for path-safe file handling.
- `json` for high-score persistence.
- `time` for gesture cooldowns, animation timing, and game loops.
- `random` for game spawning.
- `math` for distance and interpolation calculations.
- `os` and `sys` for startup configuration and runtime path setup.

## 9. Packaging and Distribution

The repository supports multiple packaging targets:

- Windows `.exe` via `scripts/build_exe.py` and PyInstaller.
- macOS `.app` via `scripts/build_app.py` and PyInstaller.
- Linux `.deb` via `scripts/build_deb.sh`.

Packaging includes application code, assets, controllers, networking, and supporting modules.

The packaging scripts explicitly include hidden imports and bundled data for:

- `mediapipe`
- `cv2`
- `psutil`
- `uvicorn`
- `fastapi`
- local assets and controller packages

This is important because the app depends on both Python modules and runtime data files such as images, music, and score JSON files.

## 10. Configuration and Data Files

Key configuration values are stored in `config/config.py` and `config/spotify_config.py`.

Important runtime data includes:

- `assets/*_highscore.json` for persisted game scores.
- `assets/music/` for local MP3 tracks.
- `assets/pictures/` for visual assets.

The project currently hardcodes Spotify credentials in `spotify_config.py`, which works for a demo but should be moved to environment variables for a real deployment.

## 11. User Interaction Model

The user experience is designed around a small set of learnable gestures:

- Open palm: back to menu or reset context.
- Pinch: select, start, pause, or confirm.
- Two-finger swipe: navigate menus or skip tracks.
- Thumb up/down: volume up/down in system and music contexts.
- Rock gesture: screenshot in system mode.

This keeps the gesture vocabulary compact and reusable across features.

## 12. Reliability and Design Tradeoffs

Strengths:

- Clear separation between gesture recognition and feature actions.
- Works with a single webcam and standard desktop environment.
- Supports both local and networked command flow.
- Controller-based design makes feature extension straightforward.

Tradeoffs and limitations:

- Gesture accuracy depends on lighting, camera quality, and hand position.
- Spotify playback depends on an active Spotify device and valid OAuth state.
- System automation depends on desktop permissions and OS tools.
- Several modules use broad exception handling, which reduces crash risk but hides detailed errors.

## 13. What Is Actively Used vs. Legacy

Actively used in the main runtime:

- `app/main.py`
- `core/`
- `command_layer/`
- `controllers/`
- `gesture_engine/`
- `networking/`

Legacy/reference code:

- `games/`

The build scripts still package `games/`, but the main app logic now lives in the controller-based implementation.

## 14. Current Project Status

The project is demo-ready.

Verified in the current workspace:

- Core imports resolve.
- The server entry point is present and wired to FastAPI/Uvicorn.
- The main app uses a complete controller pipeline.
- Local game high-score persistence is in place.
- Dependencies are declared in `requirements.txt`.

## 15. Recommended Demo Flow

For the strongest presentation, show the system in this order:

1. Start the command server.
2. Start the main app.
3. Demonstrate menu navigation with swipe and pinch.
4. Demonstrate drawing mode.
5. Demonstrate one game mode.
6. Demonstrate local music playback.
7. Show Spotify and system control as advanced capabilities if the environment is stable.

## 16. Main Risks

1. Camera tracking can degrade in low light.
2. Spotify control needs the Spotify client open and reachable.
3. System-level controls can vary across Linux desktop setups.
4. Hardcoded Spotify secrets should be removed before wider distribution.
5. Broad `except` blocks make debugging harder than it should be.

## 17. Improvement Roadmap

1. Move Spotify secrets to environment variables.
2. Replace broad exception handling with specific exceptions and structured logs.
3. Add a startup smoke test for server, camera, and dependency checks.
4. Add a short README with one-command startup instructions.
5. Consider merging or clearly labeling the legacy `games/` scripts so the runtime surface is less confusing.

## 18. Bottom Line

GestureHUB is a layered gesture-control desktop system built around MediaPipe + OpenCV + controller-based routing. The architecture is sensible: it separates gesture recognition, app state, and feature execution, which is why the project can support menus, games, drawing, music, system actions, and network commands in one codebase.

For a presentation or exam, the clearest story is this: the webcam sees the hand, MediaPipe turns it into landmarks, the gesture controller turns landmarks into commands, the state machine decides what those commands mean right now, and the active controller executes the feature.
