"""Gesture Recognizer - Detects gestures from hand landmarks.
Supports pinch-based cursor control and OS-level command gestures.
"""

import math
import time
from enum import Enum
from config import (
    FIST_THRESHOLD,
    LANDMARK_INDEX_TIP,
    LANDMARK_MIDDLE_TIP,
    LANDMARK_PINKY_TIP,
    LANDMARK_RING_TIP,
    LANDMARK_THUMB_TIP,
    LANDMARK_WRIST,
    PINCH_DISTANCE_THRESHOLD,
    PINCH_TIMEOUT,
    SWIPE_DISTANCE_THRESHOLD,
    TWO_FINGERS_THRESHOLD,
)


class GestureType(Enum):
    """Enumeration of supported gestures."""

    NONE = "none"
    PINCH = "pinch"
    DOUBLE_PINCH = "double_pinch"
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    PALM_OPEN = "palm_open"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"
    FIST = "fist"
    TWO_FINGERS = "two_fingers"
    VOLUME_UP = "volume_up"
    VOLUME_DOWN = "volume_down"


class GestureRecognizer:
    """
    Recognizes hand gestures from landmark positions.
    Detects pinch for cursor control and command gestures for OS actions.
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
        self.last_pinch_time = 0.0

        # One-shot gesture states
        self.is_palm_open = False
        self.is_thumbs_up = False
        self.is_thumbs_down = False
        self.is_fist = False
        self.is_two_fingers = False

        # Swipe tracking
        self.last_center = None
        self.last_swipe_time = 0.0

        # Distance-based volume control
        self.last_pinch_distance = None
        self.last_volume_time = 0.0

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

    def _get_finger_positions(self, landmarks):
        """Return fingertip positions for thumb/index/middle/ring/pinky."""
        return (
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_THUMB_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_INDEX_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_MIDDLE_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_RING_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_PINKY_TIP),
        )

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

    def detect_fist(self, landmarks):
        """Detect a closed fist using fingertip proximity to the wrist."""
        wrist_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        finger_positions = self._get_finger_positions(landmarks)
        return all(self.distance(pos, wrist_pos) < FIST_THRESHOLD for pos in finger_positions)

    def detect_palm_open(self, landmarks):
        """Detect an open palm with fingers spread apart."""
        wrist_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb_pos, index_pos, middle_pos, ring_pos, pinky_pos = self._get_finger_positions(landmarks)
        finger_span = self.distance(index_pos, pinky_pos)
        if finger_span < TWO_FINGERS_THRESHOLD:
            return False

        return (
            self.distance(thumb_pos, wrist_pos) > FIST_THRESHOLD * 1.2
            and self.distance(index_pos, wrist_pos) > FIST_THRESHOLD * 1.2
            and self.distance(middle_pos, wrist_pos) > FIST_THRESHOLD * 1.2
            and self.distance(ring_pos, wrist_pos) > FIST_THRESHOLD * 1.2
            and self.distance(pinky_pos, wrist_pos) > FIST_THRESHOLD * 1.2
        )

    def detect_thumbs_up(self, landmarks):
        """Detect a thumbs-up gesture."""
        wrist_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_THUMB_TIP)
        index_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_INDEX_TIP)
        return thumb_pos[1] < wrist_pos[1] - 30 and index_pos[1] > wrist_pos[1] + 15

    def detect_thumbs_down(self, landmarks):
        """Detect a thumbs-down gesture."""
        wrist_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_THUMB_TIP)
        index_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_INDEX_TIP)
        return thumb_pos[1] > wrist_pos[1] + 30 and index_pos[1] < wrist_pos[1] + 15

    def detect_two_fingers(self, landmarks):
        """Detect a two-finger pose for media playback."""
        thumb_pos, index_pos, middle_pos, ring_pos, pinky_pos = self._get_finger_positions(landmarks)
        wrist_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        fingers_extended = [
            self.distance(index_pos, wrist_pos) > FIST_THRESHOLD * 1.2,
            self.distance(middle_pos, wrist_pos) > FIST_THRESHOLD * 1.2,
            self.distance(ring_pos, wrist_pos) < FIST_THRESHOLD,
            self.distance(pinky_pos, wrist_pos) < FIST_THRESHOLD,
            self.distance(thumb_pos, wrist_pos) > FIST_THRESHOLD * 1.1,
        ]
        return sum(fingers_extended) >= 4

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
        now = time.time()
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # ============= PINCH DETECTION =============
        is_pinching_now = self.detect_pinch(landmarks)
        thumb_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_THUMB_TIP)
        pinch_distance = self.distance(thumb_pos, index_pos)

        if is_pinching_now and not self.is_pinching:
            self.is_pinching = True
            self.last_pinch_time = now
            self.last_pinch_distance = pinch_distance
            return GestureType.PINCH, {"position": index_pos, "pinch_distance": pinch_distance}

        if is_pinching_now and self.is_pinching:
            if now - self.last_volume_time > 0.2 and self.last_pinch_distance is not None:
                distance_delta = pinch_distance - self.last_pinch_distance
                if abs(distance_delta) > 12:
                    self.last_pinch_distance = pinch_distance
                    self.last_volume_time = now
                    if distance_delta < 0:
                        return GestureType.VOLUME_UP, {"position": index_pos, "pinch_distance": pinch_distance}
                    return GestureType.VOLUME_DOWN, {"position": index_pos, "pinch_distance": pinch_distance}
            self.last_pinch_distance = pinch_distance
            return GestureType.NONE, {"position": index_pos, "pinch_distance": pinch_distance}

        if not is_pinching_now and self.is_pinching:
            if now - self.last_pinch_time < PINCH_TIMEOUT:
                self.is_pinching = False
                self.last_pinch_time = 0.0
                self.last_pinch_distance = None
                return GestureType.DOUBLE_PINCH, {"position": index_pos, "pinch_distance": pinch_distance}
            self.is_pinching = False
            self.last_pinch_time = 0.0
            self.last_pinch_distance = None

        # ============= COMMAND GESTURES =============
        if self.detect_palm_open(landmarks):
            if not self.is_palm_open:
                self.is_palm_open = True
                return GestureType.PALM_OPEN, {"position": index_pos}
        else:
            self.is_palm_open = False

        if self.detect_thumbs_up(landmarks):
            if not self.is_thumbs_up:
                self.is_thumbs_up = True
                return GestureType.THUMBS_UP, {"position": index_pos}
        else:
            self.is_thumbs_up = False

        if self.detect_thumbs_down(landmarks):
            if not self.is_thumbs_down:
                self.is_thumbs_down = True
                return GestureType.THUMBS_DOWN, {"position": index_pos}
        else:
            self.is_thumbs_down = False

        if self.detect_fist(landmarks):
            if not self.is_fist:
                self.is_fist = True
                return GestureType.FIST, {"position": index_pos}
        else:
            self.is_fist = False

        if self.detect_two_fingers(landmarks):
            if not self.is_two_fingers:
                self.is_two_fingers = True
                return GestureType.TWO_FINGERS, {"position": index_pos}
        else:
            self.is_two_fingers = False

        # ============= SWIPE DETECTION =============
        if self.last_center is None:
            self.last_center = index_pos
            return GestureType.NONE, {"position": index_pos}

        dx = index_pos[0] - self.last_center[0]
        dy = index_pos[1] - self.last_center[1]
        if now - self.last_swipe_time > 0.25:
            if abs(dx) > SWIPE_DISTANCE_THRESHOLD and abs(dx) > abs(dy) * 1.2:
                self.last_swipe_time = now
                self.last_center = index_pos
                if dx < 0:
                    return GestureType.SWIPE_LEFT, {"position": index_pos}
                return GestureType.SWIPE_RIGHT, {"position": index_pos}

            if abs(dy) > SWIPE_DISTANCE_THRESHOLD and abs(dy) > abs(dx) * 1.2:
                self.last_swipe_time = now
                self.last_center = index_pos
                if dy < 0:
                    return GestureType.SWIPE_UP, {"position": index_pos}
                return GestureType.SWIPE_DOWN, {"position": index_pos}

        self.last_center = index_pos
        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False
        self.is_palm_open = False
        self.is_thumbs_up = False
        self.is_thumbs_down = False
        self.is_fist = False
        self.is_two_fingers = False
        self.last_center = None
        self.last_swipe_time = 0.0
        self.last_pinch_time = 0.0
        self.last_pinch_distance = None
        self.last_volume_time = 0.0