import cv2
import mediapipe as mp
import pyautogui
import time
import math

pyautogui.FAILSAFE = False

# Camera
cap = cv2.VideoCapture(1)
cap.set(3, 640)
cap.set(4, 480)

# Focus game window
print("Move mouse over the Dino game. Focusing in 3 seconds...")
time.sleep(3)
pyautogui.click()

# MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=1,
    model_complexity=0,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Settings
pinch_threshold = 50     # easier detection
jump_cooldown = 0.15     # time between jumps
last_jump = 0

prev_time = time.time()

while True:

    success, img = cap.read()
    if not success:
        continue

    img = cv2.flip(img,1)
    h, w, _ = img.shape

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    pinch_distance = None

    if results.multi_hand_landmarks:

        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img, hand, mp_hands.HAND_CONNECTIONS)

        lm = hand.landmark

        # Thumb
        tx = int(lm[4].x * w)
        ty = int(lm[4].y * h)

        # Index
        ix = int(lm[8].x * w)
        iy = int(lm[8].y * h)

        # Visual markers
        cv2.circle(img,(tx,ty),8,(255,0,0),-1)
        cv2.circle(img,(ix,iy),8,(0,0,255),-1)
        cv2.line(img,(tx,ty),(ix,iy),(0,255,255),2)

        pinch_distance = math.hypot(tx-ix, ty-iy)

        # Jump gesture
        if pinch_distance < pinch_threshold:

            now = time.time()

            if now - last_jump > jump_cooldown:

                pyautogui.press("space")
                last_jump = now
                print("JUMP")

    # FPS calculation
    now = time.time()
    fps = 1/(now-prev_time)
    prev_time = now

    # Display info
    cv2.putText(img,f"Pinch Distance: {int(pinch_distance) if pinch_distance else 0}",
                (10,40),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2)

    cv2.putText(img,f"FPS: {int(fps)}",
                (10,80),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,255),2)

    cv2.imshow("Gesture Dino Controller", img)

    key = cv2.waitKey(1) & 0xFF
    if key == 27 or key == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()