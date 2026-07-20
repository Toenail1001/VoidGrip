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
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    OPEN_PALM = "open_palm"
    FIST = "fist"

class GestureRecognizer:
    """
    Recognizes hand gestures from landmark positions.
    Detects pinch for left click and tracks cursor position.
    """

    def __init__(self, hand_tracker):
        """
        Initialize gesture recognizer.

        Args:
            hand_tracker (HandTracker): Hand tracker instance
        """
        self.hand_tracker = hand_tracker

        # Pinch detection state
        self.is_pinching = False

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

    def detect_pinch(self, landmarks):
        """
        Detect if hand is in pinch gesture (thumb + index touching).

        Args:
            landmarks: Hand landmarks from MediaPipe

        Returns:
            bool: True if pinching, False otherwise
        """
        thumb_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_THUMB_TIP
        )
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        dist = self.distance(thumb_pos, index_pos)
        return dist < PINCH_DISTANCE_THRESHOLD
    
    def is_open_palm(self, landmarks):
        #Get fingertip positions
        thumb = self.hand_tracker.get_landmark_position(landmarks, 4)
        index = self.hand_tracker.get_landmark_position(landmarks, 8)
        middle = self.hand_tracker.get_landmark_position(landmarks, 12)
        ring = self.hand_tracker.get_landmark_position(landmarks, 16)
        pinky = self.hand_tracker.get_landmark_position(landmarks, 20)

        #Get the finger joints
        index_joint = self.hand_tracker.get_landmark_position(landmarks, 6)
        middle_joint = self.hand_tracker.get_landmark_position(landmarks, 10)
        ring_joint = self.hand_tracker.get_landmark_position(landmarks, 14)
        pinky_joint = self.hand_tracker.get_landmark_position(landmarks, 18)

        #Check whether each finger is extended
        index_up = index[1] < index_joint[1]
        middle_up = middle[1] < middle_joint[1]
        ring_up = ring[1] < ring_joint[1]
        pinky_up = pinky[1] < pinky_joint[1]

        return index_up and middle_up and ring_up and pinky_up
    
    def get_gesture(self, landmarks):
        """
        Recognize gesture from hand landmarks.

        Args:
            landmarks: Hand landmarks from MediaPipe

        Returns:
            tuple: (gesture_type, metadata)
                gesture_type (GestureType): Type of detected gesture
                metadata (dict): Additional gesture information
        """
        # Detect if currently pinching
        is_pinching_now = self.detect_pinch(landmarks)

        # Get cursor position (index finger tip)
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # ============= PINCH DETECTION =============
        if is_pinching_now and not self.is_pinching:
            # Transition from not pinching to pinching (pinch start)
            self.is_pinching = True
            return GestureType.PINCH, {"position": index_pos}

        elif not is_pinching_now and self.is_pinching:
            # Transition from pinching to not pinching (release)
            self.is_pinching = False

        if self.is_open_palm(landmarks):
            return GestureType.OPEN_PALM, {"position": index_pos}
        
        # Default: return cursor position for movement
        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False