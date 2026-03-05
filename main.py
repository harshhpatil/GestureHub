import cv2
import mediapipe as mp
from controllers.music_controller import MusicController
from gesture_engine.motion_gesture import MotionGestureDetector

# Initialize controllers
music = MusicController()
motion = MotionGestureDetector()

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)

# FIXED: Camera index 1 (as you confirmed) + proper settings
cap = cv2.VideoCapture(1, cv2.CAP_ANY)
cap.set(3, 640)
cap.set(4, 480)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

if not cap.isOpened():
    print("Camera not accessible. Run: v4l2-ctl --list-devices")
    exit()

prev_gesture = None
gesture_history = []
STABILITY_FRAMES = 3

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    fingers = [0, 0, 0, 0, 0]
    gesture = "NO HAND"
    stable_gesture = "NO HAND"  # FIXED: Define outside if-block
    hand_label = "None"

    if results.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            landmarks = []
            h, w, c = frame.shape

            # Collect landmarks
            for id, lm in enumerate(hand_landmarks.landmark):
                cx = int(lm.x * w)
                cy = int(lm.y * h)
                landmarks.append((id, cx, cy))

            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            hand_label = results.multi_handedness[idx].classification[0].label

            # Thumb detection (left/right aware)
            if hand_label == "Right":
                if landmarks[4][1] > landmarks[3][1]:
                    fingers[0] = 1
            else:
                if landmarks[4][1] < landmarks[3][1]:
                    fingers[0] = 1

            # Other fingers with threshold filtering
            if landmarks[6][2] - landmarks[8][2] > 15:    # Index
                fingers[1] = 1
            if landmarks[10][2] - landmarks[12][2] > 15:  # Middle
                fingers[2] = 1
            if landmarks[14][2] - landmarks[16][2] > 15:  # Ring
                fingers[3] = 1
            if landmarks[18][2] - landmarks[20][2] > 15:  # Pinky
                fingers[4] = 1

            # Motion tracking
            hand_center_x = landmarks[0][1]
            motion.update(hand_center_x)

            # Gesture Classification
            if sum(fingers) == 0:
                gesture = "FIST"
            elif fingers == [0, 1, 0, 0, 0]:
                gesture = "INDEX"
            elif sum(fingers) >= 4:
                gesture = "OPEN PALM"
            elif fingers == [0, 1, 1, 1, 0]:
                gesture = "THREE FINGERS"
            else:
                gesture = "UNKNOWN"

            # Stability Filter
            if gesture != "UNKNOWN" and gesture != "NO HAND":
                gesture_history.append(gesture)
                if len(gesture_history) > STABILITY_FRAMES:
                    gesture_history.pop(0)

            if len(gesture_history) == STABILITY_FRAMES:
                stable_gesture = max(set(gesture_history), key=gesture_history.count)

            # Trigger Logic
            if (stable_gesture != prev_gesture and 
                stable_gesture != "NO HAND" and 
                stable_gesture != "UNKNOWN"):
                
                print(f"TRIGGER: {stable_gesture} (prev: {prev_gesture})")
                
                if stable_gesture == "INDEX":
                    music.toggle_play_pause()
                elif stable_gesture == "FIST":
                    music.stop_music()
                
                prev_gesture = stable_gesture

    # SWIPE LOGIC (MOVED OUTSIDE - now safe)
    swipe = None
    if stable_gesture == "THREE FINGERS":
        swipe = motion.detect_swipe()
        if swipe == "SWIPE_RIGHT":
            print("SWIPE RIGHT - Next Track")
            music.next_track()
        elif swipe == "SWIPE_LEFT":
            print("SWIPE LEFT - Previous Track")
            music.prev_track()

    # Display Info
    cv2.putText(frame, gesture, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
    cv2.putText(frame, str(fingers), (50, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    
    status = music.get_status()
    cv2.putText(frame, f"Music: {status}", (50, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    # Hand label and SWIPE MODE
    cv2.putText(frame, hand_label, (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    if stable_gesture == "THREE FINGERS":
        cv2.putText(frame, "SWIPE MODE", (50, 170), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("Gesture Control", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
gesture_history.clear()