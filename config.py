# ============================================================================
# CENTRAL CONFIGURATION CODE FOR GESTURE CONTROL
# ===========================================================================

# CAMERA CONFIGURATION
CAMERA_INDEX = 1
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

# HAND DETECTION CONFIGURATION
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5
MAX_NUM_HANDS = 1
MODEL_COMPLEXITY = 1

# GESTURE RECOGNITION CONFIGURATION
GESTURE_THRESHOLD = 0.8
GESTURE_COOLDOWN = 0.5
MOTION_SMOOTHING_FRAMES = 5
STABILITY_FRAMES = 3  # Frames needed for gesture stabilization
FINGER_DETECTION_THRESHOLD = 15  # Pixel difference for finger up/down detection 

# FINGER TIP INDICES CONFIGURATION
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_DIP = 7
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_DIP = 11
MIDDLE_TIP = 12
RING_MCP = 13
RING_PIP = 14
RING_DIP = 15
RING_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

# STATIC GESTURES CONFIGURATION
STATIC_GESTURES = {
    'THUMBS_UP': {'fingers': [1,0,0,0,0], 'thumb_up': True},
    'PEACE': {'fingers': [0,1,1,0,0]},
    'FIST': {'fingers': [0,0,0,0,0]},
    'OPEN_PALM': {'fingers': [1,1,1,1,1]}
}

# MUSIC GESTURES CONFIGURATION
MUSIC_GESTURES = {
    'FIST': 'play_pause',
    'SWIPE_RIGHT': 'next_track',
    'SWIPE_LEFT': 'prev_track',
    'SWIPE_UP': 'volume_up',
    'SWIPE_DOWN': 'volume_down'
}

# SYSTEM PATHS & CONSTANTS
LOG_DIR = 'logs'
ASSETS_DIR = 'assets'
DEBUG_MODE = True                
ENABLE_LOGGING = True

# NETWORKING CONFIGURATION
SERVER_HOST = "localhost"
SERVER_PORT = 8000
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}/command"
REQUEST_TIMEOUT = 2  # Timeout for server requests in seconds

# MUSIC CONTROLLER CONFIGURATION
DEFAULT_SONGS = [
    "assets/song-1.mp3",
    "assets/song-2.mp3",
    "assets/song-3.mp3"
]
SCROLL_AMOUNT = 300  # Pixels to scroll for system controller

# DISTANCE THRESHOLDS (for pinch, click detection)
PINCH_THRESHOLD = 0.05  # Distance between thumb and index for pinch
CLICK_THRESHOLD = 0.04

# MOTION GESTURE THRESHOLDS
SWIPE_THRESHOLD = 80  # Minimum pixel movement for swipe (used in motion_gesture.py)
SWIPE_VELOCITY_THRESHOLD = 5  # Minimum speed (currently unused)
MOTION_BUFFER_SIZE = 7  # Number of positions to track for motion detection
MOTION_COOLDOWN = 0.8  # Cooldown between motion gestures in seconds

# DRAWING COLORS (BGR format for OpenCV)
COLOR_HAND_CONNECTIONS = (0, 255, 0)  # Green
COLOR_LANDMARKS = (0, 0, 255)  # Red
COLOR_TEXT = (255, 255, 255)  # White
COLOR_BACKGROUND = (0, 0, 0)  # Black