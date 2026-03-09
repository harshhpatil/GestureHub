import cv2
import mediapipe as mp
import numpy as np
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.8, min_tracking_confidence=0.8, max_num_hands=1)

# Settings & State
canvas = None
last_point = None
eraser_last_pos = None
last_color_change_time = 0
color_change_cooldown = 0.5 

colors = [(0, 255, 255), (0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 165, 255), (255, 255, 0)]
color_names = ["Yellow", "Green", "Red", "Blue", "Magenta", "Orange", "Cyan"]
current_color_index = 0
brush_size = 5
ERASER_RADIUS = 75  # Hardcoded as requested

def detect_gesture(hand_landmarks):
    # Tip vs Knuckle Y-coordinates
    index_up = hand_landmarks.landmark[8].y < hand_landmarks.landmark[6].y
    middle_up = hand_landmarks.landmark[12].y < hand_landmarks.landmark[10].y
    ring_up = hand_landmarks.landmark[16].y < hand_landmarks.landmark[14].y
    pinky_up = hand_landmarks.landmark[20].y < hand_landmarks.landmark[18].y
    
    if index_up and not middle_up and not ring_up and not pinky_up:
        return "DRAW"
    if index_up and pinky_up and not middle_up and not ring_up:
        return "ROCKON"
    if index_up and middle_up and ring_up and pinky_up:
        return "PALM"
    if not index_up and not middle_up and not ring_up and not pinky_up:
        return "FIST"
    return "NONE"

def get_palm_center(hand_landmarks, w, h):
    wrist = hand_landmarks.landmark[0]
    middle_mcp = hand_landmarks.landmark[9]
    cx = int((wrist.x + middle_mcp.x)/2 * w)
    cy = int((wrist.y + middle_mcp.y)/2 * h)
    return (cx, cy)

cap = cv2.VideoCapture(1) 
cap.set(3, 1280); cap.set(4, 720)

while cap.isOpened():
    success, frame = cap.read()
    if not success: break
    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape
    if canvas is None: canvas = np.zeros_like(frame)

    results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    current_gesture = "NONE"
    
    # Create the blended output first
    output = cv2.addWeighted(frame, 0.7, canvas, 0.3, 0)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            current_gesture = detect_gesture(hand_landmarks)
            palm_pt = get_palm_center(hand_landmarks, w, h)
            
            if current_gesture == "DRAW":
                idx = hand_landmarks.landmark[8]
                pos = (int(idx.x * w), int(idx.y * h))
                if last_point:
                    cv2.line(canvas, last_point, pos, colors[current_color_index], brush_size)
                last_point = pos; eraser_last_pos = None
                cv2.circle(output, pos, brush_size, colors[current_color_index], -1)

            elif current_gesture == "PALM":
                # Hard erase on canvas using 75px radius
                if eraser_last_pos:
                    # Drawing a thick black line to prevent gaps
                    cv2.line(canvas, eraser_last_pos, palm_pt, (0,0,0), ERASER_RADIUS * 2)
                cv2.circle(canvas, palm_pt, ERASER_RADIUS, (0,0,0), -1)
                
                # Visual Outline (White ring) drawn on the final output
                cv2.circle(output, palm_pt, ERASER_RADIUS, (255, 255, 255), 2)
                cv2.putText(output, "ERASER", (palm_pt[0]-40, palm_pt[1]-ERASER_RADIUS-10), 0, 0.6, (255,255,255), 2)
                
                eraser_last_pos = palm_pt; last_point = None

            elif current_gesture == "ROCKON":
                if time.time() - last_color_change_time > color_change_cooldown:
                    current_color_index = (current_color_index + 1) % len(colors)
                    last_color_change_time = time.time()
                last_point = None; eraser_last_pos = None

            elif current_gesture == "FIST":
                last_point = None; eraser_last_pos = None

    # UI Overlay
    cv2.putText(output, f"MODE: {current_gesture}", (40, 50), 0, 0.8, (255,255,255), 2)
    cv2.rectangle(output, (w-180, 20), (w-20, 70), colors[current_color_index], -1)
    cv2.putText(output, color_names[current_color_index], (w-130, 55), 0, 0.6, (0,0,0), 2)

    cv2.imshow('Virtual Board', output)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()