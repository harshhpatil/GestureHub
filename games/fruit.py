import cv2
import mediapipe as mp
import random
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = ROOT_DIR / "assets"


def load_fruit_image(filename):
    img = cv2.imread(str(ASSETS_DIR / filename), cv2.IMREAD_UNCHANGED)
    if img is None:
        print(f"[WARN] Could not load image: {ASSETS_DIR / filename}")
    return img


apple = load_fruit_image("apple.png")
orange = load_fruit_image("orange.png")
banana = load_fruit_image("banana.png")
watermelon = load_fruit_image("watermelon.png")

fruit_images = [apple, orange, banana, watermelon]


def overlay_png(frame, png, center_x, center_y, target_size):
    if png is None:
        return

    resized = cv2.resize(png, (target_size * 2, target_size * 2), interpolation=cv2.INTER_AREA)
    h, w = resized.shape[:2]

    x1 = max(0, center_x - w // 2)
    y1 = max(0, center_y - h // 2)
    x2 = min(frame.shape[1], x1 + w)
    y2 = min(frame.shape[0], y1 + h)

    if x1 >= x2 or y1 >= y2:
        return

    overlay_crop = resized[: y2 - y1, : x2 - x1]

    if overlay_crop.shape[2] == 4:
        alpha = overlay_crop[:, :, 3] / 255.0
        alpha = alpha[:, :, None]
        frame[y1:y2, x1:x2] = (alpha * overlay_crop[:, :, :3] + (1 - alpha) * frame[y1:y2, x1:x2]).astype("uint8")
    else:
        frame[y1:y2, x1:x2] = overlay_crop[:, :, :3]


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)

mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(1)

width = 1280
height = 720

cap.set(3,width)
cap.set(4,height)

tip_ids = [4,8,12,16,20]

fruits = []
score = 0
high_score = 0
game_started = False

prev_x = 0
prev_y = 0

class Fruit:
    def __init__(self):
        self.x = random.randint(100,width-100)
        self.y = -50
        self.speed = random.randint(6,10)
        self.size = 40
        self.cut = False
        self.image = random.choice(fruit_images)
        self.color = random.choice([
            (0,0,255),
            (0,255,255),
            (0,255,0),
            (255,0,255)
        ])

    def move(self):
        self.y += self.speed

    def draw(self,img):

        if not self.cut:
            if self.image is not None:
                overlay_png(img, self.image, self.x, self.y, self.size)
            else:
                cv2.circle(img,(self.x,self.y),self.size,self.color,-1)
                cv2.circle(img,(self.x-10,self.y-10),10,(255,255,255),-1)

def fingers_up(lm_list):

    fingers=[]

    if lm_list[4][1] < lm_list[3][1]:
        fingers.append(1)
    else:
        fingers.append(0)

    for i in range(1,5):

        if lm_list[tip_ids[i]][2] < lm_list[tip_ids[i]-2][2]:
            fingers.append(1)
        else:
            fingers.append(0)

    return fingers

spawn_time = time.time()

while True:

    success,img = cap.read()
    img = cv2.flip(img,1)

    img_rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    results = hands.process(img_rgb)

    lm_list=[]

    if results.multi_hand_landmarks:

        for handLms in results.multi_hand_landmarks:

            mp_draw.draw_landmarks(img,handLms,mp_hands.HAND_CONNECTIONS)

            for id,lm in enumerate(handLms.landmark):

                cx=int(lm.x*width)
                cy=int(lm.y*height)

                lm_list.append([id,cx,cy])

    if lm_list:

        fingers = fingers_up(lm_list)

        x = lm_list[8][1]
        y = lm_list[8][2]

        # slicing pointer
        if fingers == [0,1,0,0,0]:

            cv2.circle(img,(x,y),8,(0,255,0),-1)
            cv2.line(img,(prev_x,prev_y),(x,y),(0,255,0),4)

            prev_x,prev_y = x,y

            for fruit in fruits:

                if not fruit.cut:

                    if abs(x-fruit.x) < fruit.size and abs(y-fruit.y) < fruit.size:

                        fruit.cut = True
                        score += 1

        # start game
        if fingers == [1,0,0,0,0]:

            game_started = True
            score = 0
            fruits.clear()

        # stop game
        if fingers[1]==1 and fingers[2]==1 and fingers[3]==0:

            game_started = False

            if score > high_score:
                high_score = score

    # spawn fruits
    if game_started:

        if time.time() - spawn_time > 1:

            fruits.append(Fruit())
            spawn_time = time.time()

        for fruit in fruits:

            fruit.move()
            fruit.draw(img)

        fruits = [f for f in fruits if f.y < height+100 and not f.cut]

    # UI lines
    cv2.line(img,(0,100),(width,100),(255,255,255),2)

    # score display
    cv2.putText(img,f"Score: {score}",(30,70),
                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),3)

    cv2.putText(img,f"High Score: {high_score}",(400,70),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),3)

    if not game_started:

        cv2.putText(img,"SHOW THUMBS UP TO START",(350,350),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),3)

    cv2.imshow("Gesture Fruit Cutter",img)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()