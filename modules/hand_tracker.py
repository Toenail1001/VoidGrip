import cv2
import numpy as np
from config import (
    MAX_HANDS,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    LANDMARK_THUMB_TIP,
    LANDMARK_INDEX_TIP,
)


class SimpleLandmark:
    """Simple landmark wrapper."""
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z


class SimpleHandLandmarks:
    """Simple hand landmarks wrapper."""
    def __init__(self):
        self.landmark = [SimpleLandmark(0, 0) for _ in range(21)]


class HandTracker:
    """
    Detects hands using skin color detection and contour analysis.
    Handles frame processing and landmark extraction.
    """

    def __init__(self):
        """Initialize hand detector."""
        self.frame_width = 0
        self.frame_height = 0
        self.original_width = 0
        self.original_height = 0
        
        # Hand detection constraints - PALM ONLY
        self.MIN_HAND_AREA = 2000       # Increased - only obvious hands
        self.MAX_HAND_AREA = 20000      # Smaller - palms only, no face parts
        self.HAND_ASPECT_RATIO_MIN = 0.6  # Less elongated = palm-shaped
        self.HAND_ASPECT_RATIO_MAX = 1.8  # Compact = palm shape
        self.HEAD_EXCLUSION_RATIO = 0.4   # Exclude top 60% (aggressive)
        
        # Define hand connections (same as MediaPipe)
        self.HAND_CONNECTIONS = [
            (0, 1), (1, 2), (2, 3), (3, 4),  # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),  # Index
            (0, 9), (9, 10), (10, 11), (11, 12),  # Middle
            (0, 13), (13, 14), (14, 15), (15, 16),  # Ring
            (0, 17), (17, 18), (18, 19), (19, 20),  # Pinky
        ]

    def process_frame(self, frame):
        """
        Process a frame and detect hand landmarks.

        Args:
            frame (np.ndarray): Input frame (BGR format)

        Returns:
            tuple: (results, frame_with_landmarks)
                - results: Detected hand landmarks
                - frame_with_landmarks: Frame with drawn landmarks
        """
        self.frame_height, self.frame_width = frame.shape[:2]
        self.original_width = self.frame_width
        self.original_height = self.frame_height
        
        # DOWNSCALE FRAME FOR SPEED (50% = 4x faster processing)
        scale_factor = 0.5
        frame_small = cv2.resize(frame, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_LINEAR)
        self.frame_height, self.frame_width = frame_small.shape[:2]
        
        # EXTREME color detection - ONLY warm hand tones (exclude face/ears/neck completely)
        hsv = cv2.cvtColor(frame_small, cv2.COLOR_BGR2HSV)
        
        # TIGHT range: Only yellow-orange (hand-specific, not face-like)
        # Hands have higher saturation and warmer hue than face
        lower_hand = np.array([8, 80, 120], dtype=np.uint8)      # Warm, saturated, bright
        upper_hand = np.array([18, 255, 255], dtype=np.uint8)
        
        mask = cv2.inRange(hsv, lower_hand, upper_hand)
        
        # Minimal morphology (speed first)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)


        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create results object
        class Results:
            pass
        
        results = Results()
        results.multi_hand_landmarks = []
        
        if contours:
            # Filter contours by size, shape, AND position to find hands (exclude face/head/ears)
            hand_candidates = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area (hands are smaller than faces)
                if area < self.MIN_HAND_AREA or area > self.MAX_HAND_AREA:
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                if w == 0 or h == 0:
                    continue
                
                # STRICT POSITION FILTER: Only bottom area (hands, not face)
                center_y = y + h // 2
                if center_y < self.frame_height * self.HEAD_EXCLUSION_RATIO:
                    continue  # Top 60% = no detection (face area)
                
                # STRICT SHAPE: Palms are more compact/round
                aspect_ratio = max(w, h) / min(w, h)
                if aspect_ratio < self.HAND_ASPECT_RATIO_MIN or aspect_ratio > self.HAND_ASPECT_RATIO_MAX:
                    continue
                
                hand_candidates.append((area, contour))
            
            # Use the largest valid hand candidate (should be an actual hand, not face)
            if hand_candidates:
                hand_candidates.sort(key=lambda x: x[0], reverse=True)
                largest_contour = hand_candidates[0][1]
            else:
                # No valid hands detected
                frame_with_landmarks = frame.copy()
                return results, frame_with_landmarks
            
            hull = cv2.convexHull(largest_contour)
            
            # Create landmarks
            landmarks_obj = SimpleHandLandmarks()
            
            # Scale factor for converting downscaled coordinates back to original
            scale_up = 1.0 / 0.5  # Inverse of downscaling
            
            # Centroid as landmark 0
            M = cv2.moments(largest_contour)
            if M["m00"] > 0:
                cx = int(M["m10"] / M["m00"]) * scale_up
                cy = int(M["m01"] / M["m00"]) * scale_up
                landmarks_obj.landmark[0] = SimpleLandmark(cx / self.original_width, cy / self.original_height)
            
            # Hull points as landmarks (scale back to original frame)
            for i, point in enumerate(hull[:20]):
                x, y = point[0]
                x_orig = x * scale_up
                y_orig = y * scale_up
                landmarks_obj.landmark[i + 1] = SimpleLandmark(x_orig / self.original_width, y_orig / self.original_height)
            
            results.multi_hand_landmarks.append(landmarks_obj)

        # Draw on frame
        frame_with_landmarks = frame.copy()
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                self._draw_hand_landmarks(frame_with_landmarks, hand_landmarks)

        return results, frame_with_landmarks
    
    def _draw_hand_landmarks(self, frame, hand_landmarks):
        """Draw hand landmarks on frame."""
        h, w, _ = frame.shape
        
        # Draw connections
        for connection in self.HAND_CONNECTIONS:
            start_idx, end_idx = connection
            if start_idx < len(hand_landmarks.landmark) and end_idx < len(hand_landmarks.landmark):
                start = hand_landmarks.landmark[start_idx]
                end = hand_landmarks.landmark[end_idx]
                
                start_pos = (int(start.x * w), int(start.y * h))
                end_pos = (int(end.x * w), int(end.y * h))
                
                cv2.line(frame, start_pos, end_pos, (0, 255, 0), 2)
        
        # Draw landmarks
        for landmark in hand_landmarks.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            cv2.circle(frame, (x, y), 2, (0, 0, 255), 2)

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
        # Use original dimensions if available, otherwise use current frame dimensions
        w = self.original_width if self.original_width > 0 else self.frame_width
        h = self.original_height if self.original_height > 0 else self.frame_height
        x = int(lm.x * w)
        y = int(lm.y * h)
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
        # The new mediapipe API doesn't require manual cleanup
        pass
