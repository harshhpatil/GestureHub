import time

class MotionGestureDetector:

    def __init__(self):

        self.positions = []

        self.buffer_size = 7
        self.swipe_threshold = 80

        self.last_swipe_time = 0
        self.cooldown = 0.8


    def update(self, x):

        self.positions.append(x)

        if len(self.positions) > self.buffer_size:
            self.positions.pop(0)


    def detect_swipe(self):

        if len(self.positions) < self.buffer_size:
            return None

        current_time = time.time()

        if current_time - self.last_swipe_time < self.cooldown:
            return None

        start = self.positions[0]
        end = self.positions[-1]

        movement = end - start

        if movement > self.swipe_threshold:

            self.positions.clear()
            self.last_swipe_time = current_time

            return "SWIPE_RIGHT"


        if movement < -self.swipe_threshold:

            self.positions.clear()
            self.last_swipe_time = current_time

            return "SWIPE_LEFT"


        return None