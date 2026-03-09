import time

class MotionGestureDetector:
    def __init__(self):
        self.positions = []
        self.buffer_size = 3  # Minimum frames for swipe detection
        self.swipe_threshold = 45  # Lower threshold for easier swipe detection
        self.last_swipe_time = 0
        self.cooldown = 0.25  # Faster cooldown for better responsiveness

    def update(self, position):
        # position can be int (X only) or tuple (X,Y)
        self.positions.append(position)
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

        # Horizontal swipe (X movement) for both X-only and (X,Y) inputs.
        if isinstance(start, tuple) and len(start) == 2:
            movement = end[0] - start[0]
        elif isinstance(start, (int, float)):
            movement = end - start
        else:
            return None

        if movement > self.swipe_threshold:
            self.positions.clear()
            self.last_swipe_time = current_time
            return "SWIPE_RIGHT"
        elif movement < -self.swipe_threshold:
            self.positions.clear()
            self.last_swipe_time = current_time
            return "SWIPE_LEFT"
        return None

    def detect_scroll(self):
        if len(self.positions) < self.buffer_size:
            return None
        
        current_time = time.time()
        if current_time - self.last_swipe_time < self.cooldown:
            return None
        
        start = self.positions[0]
        end = self.positions[-1]
        
        # Vertical scroll (Y movement) - requires 2D positions
        if isinstance(start, tuple) and len(start) == 2:
            y_start, y_end = start[1], end[1]
            scroll_dist = y_start - y_end  # Positive = scroll up
            
            if scroll_dist > self.swipe_threshold:
                self.last_swipe_time = current_time
                self.positions.clear()
                return "SCROLL_UP"
            elif scroll_dist < -self.swipe_threshold:
                self.last_swipe_time = current_time
                self.positions.clear()
                return "SCROLL_DOWN"
        
        return None

    def clear_buffer(self):
        """Clear position buffer when gesture changes"""
        self.positions.clear()
