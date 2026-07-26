"""Gesture Recognizer - Detects gestures from hand landmarks.
Supports: Pinch for left click and cursor control.
"""

import math
from enum import Enum
from config import (
    PINCH_DISTANCE_THRESHOLD,
    LANDMARK_THUMB_TIP,
    LANDMARK_INDEX_TIP,
)


class GestureType(Enum):
    """Enumeration of supported gestures."""

    NONE = "none"
    PINCH = "pinch"


class GestureRecognizer:
    """
    Recognizes hand gestures from landmark positions.
    Detects pinch for left click and tracks cursor position.
    """

    def __init__(self, hand_tracker):
<<<<<<< HEAD
        """
        Initialize gesture recognizer.

        Args:
            hand_tracker (HandTracker): Hand tracker instance
        """
=======
        """Initialize gesture recognizer."""
        self.last_gesture_time = 0
        self.gesture_cooldown = 2.5   # Set to 2.5 - 3.0 seconds to prevent rapid-fire gestures

>>>>>>> 233998b (commit)
        self.hand_tracker = hand_tracker
        self.is_pinching = False
<<<<<<< HEAD
=======
        self.previous_gesture = GestureType.NONE
        self.gesture_frame_count = 0
        self.required_frames = 5
>>>>>>> 233998b (commit)

    @staticmethod
    def distance(p1, p2):
        """
        Calculate Euclidean distance between two points.

        Args:
            p1 (tuple): (x1, y1)
            p2 (tuple): (x2, y2)

        Returns:
            float: Distance between points
        """
        return math.hypot(p2[0] - p1[0], p2[1] - p1[1])

    def detect_pinch(self, landmarks, hand_label="Right"):
        """
        Detect if hand is in pinch gesture (thumb + index touching).
        Must NOT be a fist (middle, ring, pinky should not all be curled).
        """
        thumb_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_THUMB_TIP
        )
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        dist = self.distance(thumb_pos, index_pos)
<<<<<<< HEAD
        return dist < PINCH_DISTANCE_THRESHOLD
=======
        
        # 1. Check distance threshold
        if dist >= PINCH_DISTANCE_THRESHOLD:
            return False

        # 2. Check if remaining fingers are curled (which means it's a fist, NOT a pinch)
        states = self.get_finger_states(landmarks, hand_label)
        
        # If middle, ring, and pinky are all folded down, treat as a FIST, not a pinch
        if not states["middle"] and not states["ring"] and not states["pinky"]:
            return False

        return True
    
    def get_finger_states(self, landmarks, hand_label):
        """Returns whether each finger is extended."""
        # Fingertips
        thumb = self.hand_tracker.get_landmark_position(landmarks, 4)
        wrist = self.hand_tracker.get_landmark_position(landmarks, 0)
        index = self.hand_tracker.get_landmark_position(landmarks, 8)
        middle = self.hand_tracker.get_landmark_position(landmarks, 12)
        ring = self.hand_tracker.get_landmark_position(landmarks, 16)
        pinky = self.hand_tracker.get_landmark_position(landmarks, 20)
>>>>>>> 233998b (commit)

    def get_gesture(self, landmarks):
        """
        Recognize gesture from hand landmarks.

        Args:
            landmarks: Hand landmarks from MediaPipe
            hand_label (str): "Left" or "Right" hand

        Returns:
            tuple: (gesture_type, metadata)
                gesture_type (GestureType): Type of detected gesture
                metadata (dict): Additional gesture information
        """
<<<<<<< HEAD
        # Detect if currently pinching
        is_pinching_now = self.detect_pinch(landmarks)
=======
        gesture = GestureType.NONE
>>>>>>> 233998b (commit)

        # Get cursor position (index finger tip)
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # ============= PINCH DETECTION =============
        # Pass hand_label so detect_pinch can check if middle/ring/pinky are curled (a fist)
        is_pinching_now = self.detect_pinch(landmarks, hand_label)

        if is_pinching_now and not self.is_pinching:
            # Transition from not pinching to pinching (pinch start)
            self.is_pinching = True
            return GestureType.PINCH, {"position": index_pos}

        elif not is_pinching_now and self.is_pinching:
            # Transition from pinching to not pinching (release)
            self.is_pinching = False

<<<<<<< HEAD
        # Default: return cursor position for movement
=======
        # If currently pinching, don't trigger other gesture actions
        if self.is_pinching:
            return GestureType.PINCH, {"position": index_pos}

        # ============= OTHER GESTURES =============
        if self.is_thumbs_up(landmarks, hand_label):
            gesture = GestureType.THUMBS_UP
        
        elif self.is_thumbs_down(landmarks, hand_label):
            gesture = GestureType.THUMBS_DOWN

        elif self.is_peace_sign(landmarks, hand_label):
            gesture = GestureType.PEACE_SIGN
        
        elif self.is_open_palm(landmarks, hand_label):
            gesture = GestureType.OPEN_PALM
        
        elif self.is_fist(landmarks, hand_label):
            gesture = GestureType.FIST

        # Smooth out frame-by-frame gesture changes
        if gesture == self.previous_gesture:
            self.gesture_frame_count += 1
        else:
            self.previous_gesture = gesture
            self.gesture_frame_count = 1

        current_time = time.time()

        # Check cooldown timer
        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return GestureType.NONE, {"position": index_pos}

        # Require gesture to be held for required_frames before triggering
        if self.gesture_frame_count >= self.required_frames:
            self.last_gesture_time = current_time
            return gesture, {"position": index_pos}

>>>>>>> 233998b (commit)
        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False