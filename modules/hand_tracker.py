"""
Hand Tracker - Uses MediaPipe to detect and track hand landmarks.
Provides normalized and pixel-based coordinates of hand joints.
"""

import cv2
import mediapipe as mp
from config import (
    MAX_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    LANDMARK_THUMB_TIP,
    LANDMARK_INDEX_TIP,
)


class HandTracker:
    """
    Detects and tracks hands using MediaPipe.
    Handles frame processing and landmark extraction.
    """

    def __init__(self):
        """Initialize MediaPipe hand detector."""
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=MAX_HANDS,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )

        self.frame_width = 0
        self.frame_height = 0

    def process_frame(self, frame):
        """
        Process a frame and detect hand landmarks.

        Args:
            frame (np.ndarray): Input frame (BGR format)

        Returns:
            tuple: (results, frame_with_landmarks)
                - results: MediaPipe hand landmarks
                - frame_with_landmarks: Frame with drawn landmarks
        """
        self.frame_height, self.frame_width = frame.shape[:2]

        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect hands
        results = self.hands.process(rgb_frame)

        # Draw landmarks on frame
        frame_with_landmarks = frame.copy()
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame_with_landmarks,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        return results, frame_with_landmarks

    def get_landmark_position(self, landmarks, landmark_index):
        """
        Get pixel coordinates of a specific landmark.

        Args:
            landmarks: Hand landmarks object from MediaPipe
            landmark_index (int): Index of the landmark (0-20)

        Returns:
            tuple: (x, y) in pixel coordinates
        """
        lm = landmarks.landmark[landmark_index]
        x = int(lm.x * self.frame_width)
        y = int(lm.y * self.frame_height)
        return x, y

    def get_normalized_position(self, landmarks, landmark_index):
        """
        Get normalized coordinates (0.0 to 1.0) of a landmark.

        Args:
            landmarks: Hand landmarks object from MediaPipe
            landmark_index (int): Index of the landmark (0-20)

        Returns:
            tuple: (x_norm, y_norm) normalized coordinates
        """
        lm = landmarks.landmark[landmark_index]
        return lm.x, lm.y

    def close(self):
        """Release resources."""
        self.hands.close()
