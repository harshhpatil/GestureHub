import cv2
import numpy as np


class DrawingBoardController:
    """Virtual gesture-controlled drawing board."""
    
    def __init__(self):
        self.canvas = None
        self.last_point = None
        self.eraser_last_pos = None
        self.last_color_change_time = 0
        self.color_change_cooldown = 0.5
        self.current_color_index = 0
        self.brush_size = 5
        self.eraser_radius = 75
        
        self.colors = [
            (0, 255, 255),    # Yellow
            (0, 255, 0),      # Green
            (0, 0, 255),      # Red
            (255, 0, 0),      # Blue
            (255, 0, 255),    # Magenta
            (0, 165, 255),    # Orange
            (255, 255, 0),    # Cyan
        ]
        self.color_names = ["Yellow", "Green", "Red", "Blue", "Magenta", "Orange", "Cyan"]
    
    def detect_gesture(self, hand_landmarks):
        """Detect hand gestures from MediaPipe landmarks."""
        # Tip vs Knuckle Y-coordinates (MediaPipe landmark indices)
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
    
    def get_palm_center(self, hand_landmarks, w, h):
        """Calculate palm center from wrist and middle MCP."""
        wrist = hand_landmarks.landmark[0]
        middle_mcp = hand_landmarks.landmark[9]
        cx = int((wrist.x + middle_mcp.x) / 2 * w)
        cy = int((wrist.y + middle_mcp.y) / 2 * h)
        return (cx, cy)
    
    def get_index_pos(self, hand_landmarks, w, h):
        """Get index finger position."""
        idx = hand_landmarks.landmark[8]
        return (int(idx.x * w), int(idx.y * h))
    
    def hard_erase(self, palm_pos):
        """Hard erase on canvas at palm position."""
        if self.canvas is None:
            return
        
        # Draw black circle to erase
        cv2.circle(self.canvas, palm_pos, self.eraser_radius, (0, 0, 0), -1)
        
        # If there's a previous position, draw line between them
        if self.eraser_last_pos:
            cv2.line(self.canvas, self.eraser_last_pos, palm_pos, (0, 0, 0), self.eraser_radius * 2)
    
    def update(self, frame, hand_landmarks=None):
        """
        Update drawing board with hand gestures.
        Returns modified frame with drawing overlay.
        """
        h, w = frame.shape[:2]
        
        # Initialize canvas if needed
        if self.canvas is None:
            self.canvas = np.zeros_like(frame)
        
        # Create output (blend canvas with frame)
        output = cv2.addWeighted(frame, 0.7, self.canvas, 0.3, 0)
        
        if hand_landmarks is not None:
            gesture = self.detect_gesture(hand_landmarks)
            palm_pos = self.get_palm_center(hand_landmarks, w, h)
            
            if gesture == "DRAW":
                # Draw with index finger
                pos = self.get_index_pos(hand_landmarks, w, h)
                if self.last_point:
                    cv2.line(self.canvas, self.last_point, pos, 
                            self.colors[self.current_color_index], self.brush_size)
                self.last_point = pos
                self.eraser_last_pos = None
                cv2.circle(output, pos, self.brush_size, 
                          self.colors[self.current_color_index], -1)
            
            elif gesture == "PALM":
                # Hard erase with palm
                self.hard_erase(palm_pos)
                
                # Visual outline (white ring)
                cv2.circle(output, palm_pos, self.eraser_radius, (255, 255, 255), 2)
                cv2.putText(output, "ERASER", (palm_pos[0] - 40, palm_pos[1] - self.eraser_radius - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                self.eraser_last_pos = palm_pos
                self.last_point = None
            
            elif gesture == "ROCKON":
                # Change color
                import time
                if time.time() - self.last_color_change_time > self.color_change_cooldown:
                    self.current_color_index = (self.current_color_index + 1) % len(self.colors)
                    self.last_color_change_time = time.time()
                self.last_point = None
                self.eraser_last_pos = None
            
            elif gesture == "FIST":
                # Reset state
                self.last_point = None
                self.eraser_last_pos = None
        
        # UI Overlay
        cv2.putText(output, f"DRAWING BOARD", (40, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.rectangle(output, (w - 180, 20), (w - 20, 70), 
                     self.colors[self.current_color_index], -1)
        cv2.putText(output, self.color_names[self.current_color_index], 
                   (w - 130, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        # Instructions
        cv2.putText(output, "INDEX: Draw | ROCKON: Color | PALM: Erase | FIST: Reset",
                   (w//2 - 250, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)
        
        return output
    
    def clear_canvas(self):
        """Clear drawing canvas."""
        if self.canvas is not None:
            self.canvas = np.zeros_like(self.canvas)
        self.last_point = None
        self.eraser_last_pos = None
    
    def on_enter(self):
        """Called when drawing board mode is activated."""
        self.canvas = None  # Reset canvas
        self.last_point = None
        self.eraser_last_pos = None
        print("🎨 Drawing Board Activated")
    
    def on_exit(self):
        """Called when drawing board mode is deactivated."""
        print("🎨 Drawing Board Deactivated")
    
    def handle_command(self, command):
        """Handle commands (e.g., from gesture controller or menu)."""
        if command == "CLEAR":
            self.clear_canvas()
            print("Canvas cleared")
