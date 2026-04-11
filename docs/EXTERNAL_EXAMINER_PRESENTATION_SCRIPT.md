# Full Scripted Presentation for External Examiner

Duration target: 10 to 12 minutes
Presenter tone: confident, clear, practical

## Opening (0:00 - 0:45)

"Good morning/afternoon respected examiner. We are presenting GestureHUB, a real-time hand-gesture interaction platform built in Python. The core idea is to convert natural hand gestures into reliable actions across games, system controls, drawing, and music playback, without touch input devices."

"Our project focus is not only gesture recognition, but also robust state management, modular architecture, and practical usability under real-world conditions."

## Problem Statement (0:45 - 1:30)

"Traditional keyboard and mouse interaction is not always ideal in every context. We wanted to explore touchless control that is intuitive and extendable. Existing demos often stop at gesture detection; our goal was to build a complete interaction stack where gestures become structured commands routed into multiple modules."

## Objectives (1:30 - 2:00)

"We defined four objectives:"

- "Accurate and stable hand gesture interpretation in real-time"
- "State-based navigation to avoid accidental actions"
- "Multi-module integration: games, utilities, and media"
- "Remote command visibility through a lightweight server/dashboard layer"

## Architecture Walkthrough (2:00 - 3:30)

"The architecture has five layers."

"Layer one is vision input. OpenCV captures frames and MediaPipe extracts hand landmarks."

"Layer two is gesture interpretation. We use gesture controllers and motion analysis to detect static signs and swipes. We also apply stabilization to reduce jitter."

"Layer three is orchestration. A StateMachine controls menu flow, and a ModeManager routes commands to the active module."

"Layer four is feature execution. We have dedicated controllers for drawing, music, system utilities, and games."

"Layer five is networking. A FastAPI command server supports HTTP and WebSocket, and the listener integrates server commands into local execution."

"This separation helped us keep each component maintainable and testable in isolation."

## Live Demo Narration (3:30 - 8:00)

"Now I will demonstrate the runtime behavior."

Step 1: Startup
"I start the command server and then the main application. The camera initializes, and the interface shows live FPS and gesture status."

Step 2: Menu Navigation
"Using a two-finger swipe, I move through top-level options. Using pinch, I select a module. This shows gesture-to-state transitions in action."

Step 3: Drawing Module
"In drawing mode, index-finger movement draws strokes, a designated gesture cycles colors, and open-hand erase cleans regions. This demonstrates continuous tracking and stateful gesture handling."

Step 4: Game Module
"I switch to a game mode to show low-latency command response under continuous frame processing. The same gesture language maps to game interactions through module-level logic."

Step 5: Music Module
"I demonstrate playback controls. In local mode, the app handles track toggling and navigation. Spotify mode is also supported when an active device is available."

Step 6: Optional System Controls
"I can trigger volume and navigation utilities, depending on desktop permissions. This demonstrates integration with host OS actions."

## Engineering Decisions (8:00 - 9:15)

"A few engineering choices were important:"

- "State-machine-driven menus prevent command ambiguity"
- "Command dispatch is modular, so adding new modules is straightforward"
- "Asynchronous network forwarding avoids blocking real-time gesture loop"
- "Fallback handling exists for camera index and music mode availability"

"These decisions were made to prioritize reliability during live interaction."

## Limitations and Honest Assessment (9:15 - 10:15)

"Our current limitations are:"

- "Performance and recognition quality depend on lighting and camera quality"
- "Some system actions vary across OS permissions"
- "Spotify control depends on active authenticated device context"

"Despite these constraints, core interaction remains stable and demonstrable through deterministic modules like drawing and game control."

## Future Enhancements (10:15 - 11:00)

"Planned improvements include:"

- "Adaptive calibration for different lighting environments"
- "Per-user gesture sensitivity profiles"
- "Automated smoke tests for startup and endpoint checks"
- "Hardened deployment with env-based secret management"

## Closing (11:00 - 11:30)

"To conclude, GestureHUB demonstrates a complete real-time gesture interaction pipeline, moving beyond recognition into architecture, control routing, and practical multi-feature integration. Thank you. We are ready for questions."

## Q&A Ready One-Liners

If asked: Why state machine?
"Because gesture systems are noisy; state constraints prevent accidental cross-module actions."

If asked: Why MediaPipe?
"It gives reliable landmark extraction with good real-time performance on standard hardware."

If asked: What is novel in your implementation?
"The novelty is in integration design: gesture semantics + stateful orchestration + multi-module control with network observability."

If asked: What would you improve first?
"Deployment hardening and calibration UX, because they improve real-world reliability immediately."
