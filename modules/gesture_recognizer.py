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
    PEACE_SIGN = "peace_sign"
    SIGN_OF_HORNS = "sign_of_horns"
    FOUR_FINGERS = "four_fingers"
    ILY_SIGN = "ily_sign"

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

        # Dedicated counter for peace sign (used for continuous auto-scroll)
        self.peace_sign_frames = 0
        self.peace_sign_required = 3  # Fewer frames needed for scroll activation

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

    def is_peace_sign(self, landmarks, hand_label):
        """
        Detect peace sign gesture (✌️).
        Index and middle fingers extended, ring/pinky/thumb folded.
        Spread check ensures the two fingers are visibly separated
        (prevents confusion with cursor pointing or pinch states).
        """
        states = self.get_finger_states(landmarks, hand_label)

        # Primary condition: only index and middle are up
        fingers_correct = (
            states["index"] and
            states["middle"] and
            not states["ring"] and
            not states["pinky"] and
            not states["thumb"]
        )

        if not fingers_correct:
            return False

        # Spread check: index and middle tips should be visibly apart
        # (prevents false positives when fingers are pressed together)
        index_tip = self.hand_tracker.get_landmark_position(landmarks, 8)
        middle_tip = self.hand_tracker.get_landmark_position(landmarks, 12)
        spread = self.distance(index_tip, middle_tip)

        # Must be spread apart by at least 15px (finger-width separation)
        return spread > 15

    def is_sign_of_horns(self, landmarks, hand_label):
        """
        Detect Sign of Horns gesture (🤘).
        Index and pinky extended, middle/ring/thumb folded.

        Conflict check vs other gestures:
          - Peace sign:  index + MIDDLE up  →  middle must be DOWN here ✓
          - Open palm:   all fingers up      →  middle/ring must be DOWN here ✓
          - Thumbs up/down: thumb extended   →  thumb must be DOWN here ✓
        """
        states = self.get_finger_states(landmarks, hand_label)

        fingers_correct = (
            states["index"]  and      # index up
            not states["middle"] and  # middle folded  (key: not peace sign)
            not states["ring"]   and  # ring folded
            states["pinky"]  and      # pinky up
            not states["thumb"]       # thumb folded   (key: not thumbs gesture)
        )

        if not fingers_correct:
            return False

        # Spread check: index tip and pinky tip should be noticeably separated
        index_tip = self.hand_tracker.get_landmark_position(landmarks, 8)
        pinky_tip = self.hand_tracker.get_landmark_position(landmarks, 20)
        spread = self.distance(index_tip, pinky_tip)

        # Natural horn spread is large; require at least 20px separation
        return spread > 20

    def is_ily_sign(self, landmarks, hand_label):
        """
        Detect ILY sign (🤟): index + pinky + thumb extended, middle + ring folded.
        Like sign of horns but with the thumb also out.

        Conflict checks:
          - Sign of horns: thumb must be DOWN → here thumb is UP ✓
          - Open palm:     middle + ring must be UP → here they are DOWN ✓
          - Thumbs up/down: index + pinky must be DOWN → here they are UP ✓
        """
        states = self.get_finger_states(landmarks, hand_label)
        return (
            states["index"]      and   # index up
            not states["middle"] and   # middle folded
            not states["ring"]   and   # ring folded
            states["pinky"]      and   # pinky up
            states["thumb"]            # thumb also up  (key: distinct from sign_of_horns)
        )

    def is_four_fingers(self, landmarks, hand_label):
        """
        Detect four-finger gesture: index, middle, ring, pinky extended;
        thumb folded into palm.

        Conflict checks:
          - Open palm:    thumb must also be UP  → here thumb is DOWN ✓
          - Sign of horns: middle + ring must be DOWN → here they are UP ✓
          - Peace sign:   ring + pinky must be DOWN → here they are UP ✓
        """
        states = self.get_finger_states(landmarks, hand_label)
        return (
            states["index"]  and
            states["middle"] and
            states["ring"]   and
            states["pinky"]  and
            not states["thumb"]      # thumb folded  (key distinction from open_palm)
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

        elif self.is_peace_sign(landmarks, hand_label):
            gesture = GestureType.PEACE_SIGN

        elif self.is_sign_of_horns(landmarks, hand_label):
            gesture = GestureType.SIGN_OF_HORNS

        elif self.is_ily_sign(landmarks, hand_label):
            gesture = GestureType.ILY_SIGN

        elif self.is_four_fingers(landmarks, hand_label):
            gesture = GestureType.FOUR_FINGERS

        elif self.is_open_palm(landmarks, hand_label):
            gesture = GestureType.OPEN_PALM
        
        elif self.is_fist(landmarks, hand_label):
            gesture = GestureType.FIST


        if gesture == self.previous_gesture:
            self.gesture_frame_count += 1
        else:
            self.previous_gesture = gesture
            self.gesture_frame_count = 1

        # Update dedicated peace sign counter
        if gesture == GestureType.PEACE_SIGN:
            self.peace_sign_frames += 1
        else:
            self.peace_sign_frames = 0

        current_time = time.time()

        # Peace sign is used for continuous auto-scroll — bypass cooldown so it
        # fires every frame. All other gestures still debounce normally.
        if gesture == GestureType.PEACE_SIGN:
            if self.peace_sign_frames >= self.peace_sign_required:
                return gesture, {"position": index_pos}
            return GestureType.NONE, {"position": index_pos}

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
        self.peace_sign_frames = 0