"""Gesture Recognizer - Detects gestures from hand landmarks.
Supports: Pinch for left click and cursor control.
"""
import time
import math
from enum import Enum
from operator import index
from config import (
    PINCH_DISTANCE_THRESHOLD,
    LANDMARK_THUMB_TIP,
    LANDMARK_INDEX_TIP,
)

# Gesture detection thresholds
THUMB_EXTENSION_THRESHOLD = 20
PINCH_THRESHOLD = PINCH_DISTANCE_THRESHOLD
GESTURE_CONFIRM_FRAMES = 6
# Gesture thresholds
FINGER_EXTENSION_MARGIN = 20
THUMB_EXTENSION_MARGIN = 18

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
        self.last_gesture_time = 0
        self.gesture_cooldown = 0.5   # seconds

        self.hand_tracker = hand_tracker

        # Pinch detection state
        self.is_pinching = False

        self.previous_gesture = GestureType.NONE
        self.gesture_frame_count = 0
        self.required_frames = 5

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
    
    def get_finger_states(self, landmarks, hand_label):
        """Returns whether each finger is extended."""
        # Fingertips
        thumb = self.hand_tracker.get_landmark_position(landmarks, 4)
        wrist = self.hand_tracker.get_landmark_position(landmarks, 0)
        index = self.hand_tracker.get_landmark_position(landmarks, 8)
        middle = self.hand_tracker.get_landmark_position(landmarks, 12)
        ring = self.hand_tracker.get_landmark_position(landmarks, 16)
        pinky = self.hand_tracker.get_landmark_position(landmarks, 20)

        # Finger joints
        thumb_joint = self.hand_tracker.get_landmark_position(landmarks, 3)

        thumb_base = self.hand_tracker.get_landmark_position(landmarks, 2)

        index_joint = self.hand_tracker.get_landmark_position(landmarks, 6)
        middle_joint = self.hand_tracker.get_landmark_position(landmarks, 10)
        ring_joint = self.hand_tracker.get_landmark_position(landmarks, 14)
        pinky_joint = self.hand_tracker.get_landmark_position(landmarks, 18)

        # Determine if fingers are extended
        if hand_label == "Right":
            thumb_extended = (
                thumb[0] < thumb_joint[0] < thumb_base[0]
            )
        else:
            thumb_extended = (
                thumb[0] > thumb_joint[0] > thumb_base[0]
            )
        index_up = index[1] < (index_joint[1] - FINGER_EXTENSION_MARGIN)
        middle_up = middle[1] < (middle_joint[1] - FINGER_EXTENSION_MARGIN)
        ring_up = ring[1] < (ring_joint[1] - FINGER_EXTENSION_MARGIN)
        pinky_up = pinky[1] < (pinky_joint[1] - FINGER_EXTENSION_MARGIN)
            
        
        if thumb[1] < wrist[1] - THUMB_EXTENSION_MARGIN:
            thumb_direction = "up"
        elif thumb[1] > wrist[1] + THUMB_EXTENSION_MARGIN:
            thumb_direction = "down"
        else:
            thumb_direction = "side"

        return {
            "thumb": thumb_extended,
            "thumb_direction": thumb_direction,
            "index": index_up,
            "middle": middle_up,
            "ring": ring_up,
            "pinky": pinky_up
        }

    def is_open_palm(self, landmarks, hand_label):
       states = self.get_finger_states(landmarks, hand_label)
       thumb = self.hand_tracker.get_landmark_position(landmarks, 4)
       index = self.hand_tracker.get_landmark_position(landmarks, 8)
       
       thumb_index_distance = self.distance(thumb, index)

       return (
            states["thumb"] and
            states["index"] and
            states["middle"] and
            states["ring"] and
            states["pinky"] and
            thumb_index_distance > PINCH_DISTANCE_THRESHOLD
        )
    
    def is_fist(self, landmarks, hand_label):
        states = self.get_finger_states(landmarks, hand_label)

        return (
            not states["thumb"] and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )
    
    def is_thumbs_up(self, landmarks, hand_label):
        states = self.get_finger_states(landmarks, hand_label)

        return (
            states["thumb"] and
            states["thumb_direction"] == "up" and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )
    
    def is_thumbs_down(self, landmarks, hand_label):
        states = self.get_finger_states(landmarks, hand_label)

        return (
            states["thumb"] and
            states["thumb_direction"] == "down" and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )

    def get_gesture(self, landmarks, hand_label):
        """
        Recognize gesture from hand landmarks.

        Args:
            landmarks: Hand landmarks from MediaPipe

        Returns:
            tuple: (gesture_type, metadata)
                gesture_type (GestureType): Type of detected gesture
                metadata (dict): Additional gesture information
        """
        gesture = GestureType.NONE

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

        # ============= OTHER GESTURES =============
        if self.is_thumbs_up(landmarks, hand_label):
            gesture = GestureType.THUMBS_UP
        
        elif self.is_thumbs_down(landmarks, hand_label):
            gesture = GestureType.THUMBS_DOWN
        
        elif self.is_open_palm(landmarks, hand_label):
            gesture = GestureType.OPEN_PALM
        
        elif self.is_fist(landmarks, hand_label):
            gesture = GestureType.FIST


        if gesture == self.previous_gesture:
            self.gesture_frame_count += 1
        else:
            self.previous_gesture = gesture
            self.gesture_frame_count = 1

        current_time = time.time()

        if current_time - self.last_gesture_time < self.gesture_cooldown:
            return GestureType.NONE, {"position": index_pos}

        self.last_gesture_time = current_time

        if self.gesture_frame_count >= self.required_frames:
            current_time = time.time()
                
            if current_time - self.last_gesture_time >= self.gesture_cooldown:
                self.last_gesture_time = current_time
            return gesture, {"position": index_pos}

        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False