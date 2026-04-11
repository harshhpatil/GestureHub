import cv2
import mediapipe as mp
import random
import time

cap = cv2.VideoCapture(1)
cap.set(3,1280)
cap.set(4,720)

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1)
mp_draw = mp.solutions.drawing_utils

score = 0
high_score = 0
lives = 3

basket_x = 600
basket_y = 650
smooth = 0.3

fruits = []
spawn_timer = time.time()

game_running = False
gesture_delay = 1.2
last_gesture = 0


class Fruit:
    def __init__(self):
        self.x = random.randint(50,1200)
        self.y = 0
        self.speed = random.randint(6,10)
        self.size = 30
        self.color = random.choice([(0,0,255),(0,255,0),(0,255,255),(255,0,255)])

    def move(self):
        self.y += self.speed

    def draw(self,img):
        cv2.circle(img,(self.x,self.y),self.size,self.color,-1)


while True:

    ret,img = cap.read()
    img = cv2.flip(img,1)
    h,w,_ = img.shape

    rgb = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
    results = hands.process(rgb)

    if results.multi_hand_landmarks:

        hand = results.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(img,hand,mp_hands.HAND_CONNECTIONS)

        lm = hand.landmark

        index_x = int(lm[8].x * w)

        # basket movement
        target = index_x * 1.5
        basket_x = int(basket_x + (target-basket_x)*smooth)
        basket_x = max(90,min(basket_x,w-90))

        # thumbs up detection
        thumb = lm[4].y < lm[3].y
        index_down = lm[8].y > lm[6].y
        middle_down = lm[12].y > lm[10].y
        ring_down = lm[16].y > lm[14].y
        pinky_down = lm[20].y > lm[18].y

        if thumb and index_down and middle_down and ring_down and pinky_down:

            if time.time()-last_gesture > gesture_delay:

                game_running = not game_running
                last_gesture = time.time()

                if game_running:
                    score = 0
                    lives = 3
                    fruits.clear()
                    print("START")

                else:
                    print("STOP")


    # UI top bar
    cv2.rectangle(img,(0,0),(w,80),(0,0,0),-1)

    cv2.putText(img,"GESTURE CATCH GAME",(430,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),3)

    cv2.putText(img,f"Score: {score}",(20,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(255,255,255),2)

    cv2.putText(img,f"High Score: {high_score}",(900,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)

    cv2.putText(img,f"Lives: {lives}",(650,50),
                cv2.FONT_HERSHEY_SIMPLEX,1,(0,0,255),2)


    # GAME RUNNING STATE
    if game_running:

        if time.time()-spawn_timer > 1:
            fruits.append(Fruit())
            spawn_timer = time.time()

        for fruit in fruits[:]:

            fruit.move()
            fruit.draw(img)

            if abs(fruit.x-basket_x) < 80 and abs(fruit.y-basket_y) < 40:

                score += 1
                high_score = max(high_score,score)
                fruits.remove(fruit)

            elif fruit.y > 720:

                lives -= 1
                fruits.remove(fruit)


    # basket
    cv2.rectangle(img,(basket_x-80,basket_y),
                  (basket_x+80,basket_y+40),(19,69,139),-1)

    cv2.rectangle(img,(basket_x-90,basket_y-10),
                  (basket_x+90,basket_y),(42,42,165),-1)

    for i in range(-60,80,20):
        cv2.line(img,(basket_x+i,basket_y),
                 (basket_x+i,basket_y+40),(255,255,255),2)


    # STOP SCREEN
    if not game_running:

        cv2.putText(img,"THUMBS UP TO START",(430,350),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0),3)

        cv2.putText(img,f"HIGHEST SCORE: {high_score}",(450,420),
                    cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),3)


    cv2.imshow("Gesture Catch Game",img)

    if cv2.waitKey(1) & 0xFF == 27:
        break


cap.release()
cv2.destroyAllWindows()