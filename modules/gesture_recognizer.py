"""
Gesture Recognizer - Detects gestures from hand landmarks.
Supports: Pinch (single & double), swipes, palm open, thumbs up/down, and more.
Easily extensible for new gestures.
"""

import math
import time
from enum import Enum
from config import (
    PINCH_DISTANCE_THRESHOLD,
    PINCH_TIMEOUT,
    LANDMARK_THUMB_TIP,
    LANDMARK_INDEX_TIP,
    LANDMARK_MIDDLE_TIP,
    LANDMARK_RING_TIP,
    LANDMARK_PINKY_TIP,
    LANDMARK_WRIST,
    ACTIVATION_HOLD_TIME,
    ACTIVATION_COOLDOWN,
)


class GestureType(Enum):
    """Enumeration of supported gestures."""

    NONE = "none"
    PINCH = "pinch"
    DOUBLE_PINCH = "double_pinch"
    RELEASE = "release"
    FIST = "fist"  # New: closed hand gesture
    TWO_FINGERS = "two_fingers"  # New: index+middle extended
    PALM_OPEN = "palm_open"  # Reused as activation toggle
    # Deprecated/disabled by default: swipes, thumbs
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
    SWIPE_UP = "swipe_up"
    SWIPE_DOWN = "swipe_down"
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class GestureRecognizer:
    """
    Recognizes hand gestures from landmark positions.
    Maintains state for detecting complex gestures like double-pinch.
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
        self.pinch_count = 0
        self.last_pinch_time = 0
        self.right_click_mode = False

        # Swipe detection state
        self.last_index_position = None
        self.swipe_start_time = None

        # Gesture cooldown tracking - prevent repeated triggers
        self.last_gesture_time = {}
        self.GESTURE_COOLDOWN = 0.3  # Seconds between same gesture triggers
        
        # Activation state
        self.is_active = True  # System starts active
        self.last_activation_time = 0
        self.palm_open_start_time = None  # Track palm hold time for activation toggle

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

    def _should_trigger_gesture(self, gesture_name, current_time):
        """
        Check if enough time has passed to trigger this gesture again.
        Prevents accidental repeated triggers.

        Args:
            gesture_name (str): Name of the gesture
            current_time (float): Current timestamp

        Returns:
            bool: True if gesture can be triggered
        """
        last_time = self.last_gesture_time.get(gesture_name, 0)
        if current_time - last_time < self.GESTURE_COOLDOWN:
            return False
        
        self.last_gesture_time[gesture_name] = current_time
        return True

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
        current_time = time.time()

        # Detect if currently pinching
        is_pinching_now = self.detect_pinch(landmarks)

        # Get cursor position (index finger tip)
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # ============= ACTIVATION TOGGLE (Fist with hold) =============
        is_fist = self.detect_fist(landmarks)
        if is_fist:
            if self.palm_open_start_time is None:  # Reuse this var to track fist hold time
                self.palm_open_start_time = current_time
            elif current_time - self.palm_open_start_time >= ACTIVATION_HOLD_TIME:
                # Fist held for 0.5 sec → toggle activation
                if current_time - self.last_activation_time >= ACTIVATION_COOLDOWN:
                    self.is_active = not self.is_active
                    self.last_activation_time = current_time
                    self.palm_open_start_time = None
                    return GestureType.FIST, {"position": index_pos, "action": "activation_toggle", "is_active": self.is_active}
        else:
            self.palm_open_start_time = None

        # ============= FIST DETECTION (Freeze cursor) - DISABLED (now used for activation) =============
        # Fist is now reserved for activation toggle only
        # if self.detect_fist(landmarks) and self._should_trigger_gesture("fist", current_time):
        #     return GestureType.FIST, {"position": index_pos}

        # ============= TWO FINGERS DETECTION (Scroll mode) =============
        if self.detect_two_fingers(landmarks) and self._should_trigger_gesture("two_fingers", current_time):
            return GestureType.TWO_FINGERS, {"position": index_pos}

        # ============= PINCH DETECTION =============
        if is_pinching_now and not self.is_pinching:
            # Transition from not pinching to pinching (pinch start)
            self.is_pinching = True

            # Count pinches within timeout window
            if current_time - self.last_pinch_time < PINCH_TIMEOUT:
                self.pinch_count += 1
            else:
                self.pinch_count = 1

            self.last_pinch_time = current_time

            # Determine if this is single or double pinch
            if self.pinch_count == 1:
                self.right_click_mode = False
                return GestureType.PINCH, {"position": index_pos}

            elif self.pinch_count == 2:
                self.right_click_mode = True
                self.pinch_count = 0  # Reset counter
                return GestureType.DOUBLE_PINCH, {"position": index_pos}

        elif not is_pinching_now and self.is_pinching:
            # Transition from pinching to not pinching (release)
            self.is_pinching = False

            # Reset double-pinch counter if timeout has passed
            if current_time - self.last_pinch_time >= PINCH_TIMEOUT:
                self.pinch_count = 0

            if self.right_click_mode:
                self.right_click_mode = False
                return GestureType.RELEASE, {"position": index_pos}

        # ============= SWIPE DETECTION =============
        # Only detect swipes when not pinching
        if not is_pinching_now:
            swipe_direction, distance = self.detect_swipe(landmarks)
            if swipe_direction == "swipe_left" and self._should_trigger_gesture("swipe_left", current_time):
                return GestureType.SWIPE_LEFT, {"position": index_pos, "distance": distance}
            elif swipe_direction == "swipe_right" and self._should_trigger_gesture("swipe_right", current_time):
                return GestureType.SWIPE_RIGHT, {"position": index_pos, "distance": distance}
            elif swipe_direction == "swipe_up" and self._should_trigger_gesture("swipe_up", current_time):
                return GestureType.SWIPE_UP, {"position": index_pos, "distance": distance}
            elif swipe_direction == "swipe_down" and self._should_trigger_gesture("swipe_down", current_time):
                return GestureType.SWIPE_DOWN, {"position": index_pos, "distance": distance}

        # ============= THUMBS DETECTION =============
        if not is_pinching_now:
            if self.detect_thumbs_up(landmarks) and self._should_trigger_gesture("thumbs_up", current_time):
                return GestureType.THUMBS_UP, {"position": index_pos}
            elif self.detect_thumbs_down(landmarks) and self._should_trigger_gesture("thumbs_down", current_time):
                return GestureType.THUMBS_DOWN, {"position": index_pos}

        # Default: return cursor position for movement
        return GestureType.NONE, {"position": index_pos}


    def detect_fist(self, landmarks, threshold=None):
        """
        Detect closed fist (all fingers pulled in close to wrist).

        Args:
            landmarks: Hand landmarks
            threshold: Distance threshold (from config)

        Returns:
            bool: True if fist detected
        """
        if threshold is None:
            from config import FIST_THRESHOLD
            threshold = FIST_THRESHOLD
        
        wrist = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        finger_tips = [
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_THUMB_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_INDEX_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_MIDDLE_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_RING_TIP),
            self.hand_tracker.get_landmark_position(landmarks, LANDMARK_PINKY_TIP),
        ]
        
        avg_distance = sum(self.distance(wrist, tip) for tip in finger_tips) / len(finger_tips)
        return avg_distance < threshold

    def detect_two_fingers(self, landmarks, threshold=None):
        """
        Detect two fingers extended (index + middle).

        Args:
            landmarks: Hand landmarks
            threshold: Distance threshold (from config)

        Returns:
            bool: True if two fingers detected
        """
        if threshold is None:
            from config import TWO_FINGERS_THRESHOLD
            threshold = TWO_FINGERS_THRESHOLD
        
        index_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_INDEX_TIP)
        middle_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_MIDDLE_TIP)
        ring_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_RING_TIP)
        pinky_pos = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_PINKY_TIP)
        
        wrist = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        
        # Index and middle should be extended (far from wrist)
        index_extended = self.distance(wrist, index_pos) > threshold
        middle_extended = self.distance(wrist, middle_pos) > threshold
        
        # Ring and pinky should be curled (close to wrist)
        ring_curled = self.distance(wrist, ring_pos) < threshold
        pinky_curled = self.distance(wrist, pinky_pos) < threshold
        
        return index_extended and middle_extended and ring_curled and pinky_curled

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False
        self.pinch_count = 0
        self.last_pinch_time = 0
        self.right_click_mode = False
        self.last_gesture_time = {}
        self.last_index_position = None
        self.swipe_start_time = None
        self.palm_open_start_time = None
        # Note: is_active and last_activation_time preserved across resets

    # ============= NEW GESTURE DETECTIONS =============

    def detect_swipe(self, landmarks, threshold_distance=100):
        """
        Detect horizontal/vertical swipe gestures.

        Args:
            landmarks: Hand landmarks
            threshold_distance: Minimum pixels for swipe detection

        Returns:
            tuple: (direction, distance) or (None, 0) if no swipe
        """
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        if self.last_index_position is None:
            self.last_index_position = index_pos
            self.swipe_start_time = time.time()
            return None, 0

        # Calculate movement
        delta_x = index_pos[0] - self.last_index_position[0]
        delta_y = index_pos[1] - self.last_index_position[1]
        distance = math.hypot(delta_x, delta_y)

        # Check if movement exceeds threshold
        if distance > threshold_distance:
            # Determine direction based on which axis moved more
            if abs(delta_x) > abs(delta_y):
                direction = "swipe_right" if delta_x > 0 else "swipe_left"
            else:
                direction = "swipe_down" if delta_y > 0 else "swipe_up"

            # Reset tracking
            self.last_index_position = index_pos
            return direction, distance

        # Update position for next frame
        self.last_index_position = index_pos
        return None, 0

    def detect_palm_open(self, landmarks, open_threshold=150):
        """
        Detect open palm gesture (all fingers extended).

        Args:
            landmarks: Hand landmarks
            open_threshold: Minimum distance for open palm

        Returns:
            bool: True if palm is open
        """
        # Get positions of all finger tips
        wrist = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_THUMB_TIP
        )
        index = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )
        middle = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_MIDDLE_TIP
        )
        ring = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_RING_TIP)
        pinky = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_PINKY_TIP
        )

        # Calculate average distance of all finger tips from wrist
        distances = [
            self.distance(wrist, thumb),
            self.distance(wrist, index),
            self.distance(wrist, middle),
            self.distance(wrist, ring),
            self.distance(wrist, pinky),
        ]

        avg_distance = sum(distances) / len(distances)

        # If all fingers are far from wrist, palm is open
        return avg_distance > open_threshold

    def detect_thumbs_up(self, landmarks):
        """
        Detect thumbs up gesture (thumb up, other fingers down).

        Args:
            landmarks: Hand landmarks

        Returns:
            bool: True if thumbs up
        """
        wrist = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_THUMB_TIP
        )
        index = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # Thumb should be above wrist (lower y value)
        thumb_up = thumb[1] < wrist[1]

        # Index should be below wrist (higher y value)
        index_down = index[1] > wrist[1]

        # Thumb should be above index
        thumb_above_index = thumb[1] < index[1]

        return thumb_up and index_down and thumb_above_index

    def detect_thumbs_down(self, landmarks):
        """
        Detect thumbs down gesture (thumb down, other fingers up).

        Args:
            landmarks: Hand landmarks

        Returns:
            bool: True if thumbs down
        """
        wrist = self.hand_tracker.get_landmark_position(landmarks, LANDMARK_WRIST)
        thumb = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_THUMB_TIP
        )
        index = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )

        # Thumb should be below wrist (higher y value)
        thumb_down = thumb[1] > wrist[1]

        # Index should be above wrist (lower y value)
        index_up = index[1] < wrist[1]

        # Thumb should be below index
        thumb_below_index = thumb[1] > index[1]

        return thumb_down and index_up and thumb_below_index

