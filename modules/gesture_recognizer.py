"""Gesture Recognizer - Detects gestures from hand landmarks.
Supports: Pinch for left click and cursor control.
"""

import math
from enum import Enum
from operator import index
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
    
    def get_finger_states(self, landmarks):
        """Returns whether each finger is extended."""
        # Fingertips
        thumb = self.hand_tracker.get_landmark_position(landmarks, 4)
        index = self.hand_tracker.get_landmark_position(landmarks, 8)
        middle = self.hand_tracker.get_landmark_position(landmarks, 12)
        ring = self.hand_tracker.get_landmark_position(landmarks, 16)
        pinky = self.hand_tracker.get_landmark_position(landmarks, 20)

        # Finger joints
        thumb_joint = self.hand_tracker.get_landmark_position(landmarks, 3)
        index_joint = self.hand_tracker.get_landmark_position(landmarks, 6)
        middle_joint = self.hand_tracker.get_landmark_position(landmarks, 10)
        ring_joint = self.hand_tracker.get_landmark_position(landmarks, 14)
        pinky_joint = self.hand_tracker.get_landmark_position(landmarks, 18)

        # Determine if fingers are extended
        thumb_up = thumb[1] < thumb_joint[1]
        index_up = index[1] < index_joint[1]
        middle_up = middle[1] < middle_joint[1]
        ring_up = ring[1] < ring_joint[1]
        pinky_up = pinky[1] < pinky_joint[1]
        
        thumb_direction = "up" if thumb[1] < thumb_joint[1] else "down"

        return {
            "thumb": thumb_up,
            "thumb_direction": thumb_direction,
            "index": index_up,
            "middle": middle_up,
            "ring": ring_up,
            "pinky": pinky_up
        }

    def is_open_palm(self, landmarks):
       states = self.get_finger_states(landmarks)
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
    
    def is_fist(self, landmarks):
        states = self.get_finger_states(landmarks)

        return (
            not states["thumb"] and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )
    
    def is_thumbs_up(self, landmarks):
        states = self.get_finger_states(landmarks)

        return (
            states["thumb"] and
            states["thumb_direction"] == "up" and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )
    
    def is_thumbs_down(self, landmarks):
        states = self.get_finger_states(landmarks)

        return (
            states["thumb"] and
            states["thumb_direction"] == "down" and
            not states["index"] and
            not states["middle"] and
            not states["ring"] and
            not states["pinky"]
        )

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
        gesture = GestureType.NONE

        # Detect if currently pinching
        is_pinching_now = self.detect_pinch(landmarks)

        # Get cursor position (index finger tip)
        index_pos = self.hand_tracker.get_landmark_position(
            landmarks, LANDMARK_INDEX_TIP
        )
        states = self.get_finger_states(landmarks)
        print(states)
        # ============= PINCH DETECTION =============
        if is_pinching_now and not self.is_pinching:
            # Transition from not pinching to pinching (pinch start)
            self.is_pinching = True
            return GestureType.PINCH, {"position": index_pos}

        elif not is_pinching_now and self.is_pinching:
            # Transition from pinching to not pinching (release)
            self.is_pinching = False

        if self.is_thumbs_up(landmarks):
            gesture = GestureType.THUMBS_UP
        
        if self.is_thumbs_down(landmarks):
            gesture = GestureType.THUMBS_DOWN
        
        if self.is_open_palm(landmarks):
            gesture = GestureType.OPEN_PALM
        
        if self.is_fist(landmarks):
            gesture = GestureType.FIST

        if gesture == self.previous_gesture:
            self.gesture_frame_count += 1
        else:
            self.previous_gesture = gesture
            self.gesture_frame_count = 1

        if self.gesture_frame_count >= self.required_frames:
            return gesture, {"position": index_pos}

        return GestureType.NONE, {"position": index_pos}

    def reset(self):
        """Reset gesture state (useful when stopping detection)."""
        self.is_pinching = False