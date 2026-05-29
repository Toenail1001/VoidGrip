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

        # Default: return cursor position for movement
        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False