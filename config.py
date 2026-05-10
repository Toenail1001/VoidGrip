"""
Configuration and constants for the Gesture Control System.
All tunable parameters are defined here for easy adjustment.
"""

# ============= HAND TRACKING SETTINGS =============
MAX_HANDS = 1  # Detect only 1 hand
MIN_DETECTION_CONFIDENCE = 0.7
MIN_TRACKING_CONFIDENCE = 0.5

# ============= GESTURE DETECTION SETTINGS =============
PINCH_DISTANCE_THRESHOLD = 50  # Pixels - distance between thumb and index for pinch (increased for reliability)
PINCH_TIMEOUT = 0.6  # Seconds - time window for detecting double pinch
CLICK_COOLDOWN = 0.5  # Seconds - minimum time between clicks (increased for stability)
SWIPE_DISTANCE_THRESHOLD = 150  # Pixels - minimum distance for swipe detection (increased for reliability)

# ============= ACTIVATION GESTURE SETTINGS =============
ACTIVATION_GESTURE = "fist"  # Gesture to toggle activation/pause - FIST (closed hand)
ACTIVATION_HOLD_TIME = 0.5  # Seconds - hold time to trigger activation (shorter since fist is intentional)
ACTIVATION_COOLDOWN = 1.0  # Seconds - cooldown after activation toggle (longer to prevent accidental re-toggles)
FIST_THRESHOLD = 60  # Max avg finger distance for fist (lower = stricter, requires tightly closed hand)
TWO_FINGERS_THRESHOLD = 80  # Distance for two-finger detection

# ============= SCREEN EDGE COMPENSATION =============
SCREEN_EDGE_MARGIN = 0.02  # 2% margin to ensure corners are reachable
SCREEN_CALIBRATION_SCALE = 1.0  # Scale factor for screen mapping (adjust if cursor doesn't reach edges)

# ============= CURSOR SMOOTHING =============
SMOOTHING_FACTOR = 5  # Higher = smoother but slower response. Range: 1-10
INITIAL_CURSOR_X = 0
INITIAL_CURSOR_Y = 0

# ============= GUI SETTINGS =============
WINDOW_WIDTH = 1200  # Increased for larger camera display
WINDOW_HEIGHT = 700
CAMERA_FEED_WIDTH = 800  # Increased for larger preview
CAMERA_FEED_HEIGHT = 600
UPDATE_INTERVAL_MS = 30  # Milliseconds between GUI updates

# ============= FAILSAFE SETTINGS =============
FAILSAFE_ENABLED = True
FAILSAFE_THRESHOLD = 50  # Pixels from top-left corner to trigger stop
DISPLAY_FAILSAFE_INFO = True

# ============= CAMERA SETTINGS =============
CAMERA_INDEX = 0  # 0 = default webcam
FLIP_CAMERA_HORIZONTAL = True  # Mirror the camera feed

# ============= HAND LANDMARK INDICES =============
# MediaPipe hand landmarks (0-20)
LANDMARK_THUMB_TIP = 4
LANDMARK_INDEX_TIP = 8
LANDMARK_MIDDLE_TIP = 12
LANDMARK_RING_TIP = 16
LANDMARK_PINKY_TIP = 20
LANDMARK_WRIST = 0
