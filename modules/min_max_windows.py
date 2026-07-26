import cv2
import mediapipe as mp
import pyautogui
import time

# Disable PyAutoGUI fail-safe pause delay for faster response
pyautogui.PAUSE = 0.05


class GestureWindowController:
    """
    Tracks hand gestures to minimize or maximize active system windows.
    - Fist Gesture: Minimizes window (Win + Down)
    - Open Palm Gesture: Maximizes window (Win + Up)
    """

    def __init__(self, cooldown_seconds=1.5):
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Cooldown management to prevent rapid repeated actions
        self.last_action_time = 0
        self.cooldown = cooldown_seconds

    # ============= ACTION EXECUTION =============

    def minimize_window(self):
        """Minimize the currently active window."""
        print("[ACTION] Minimizing Window...")
        pyautogui.hotkey('win', 'down')

    def maximize_window(self):
        """Maximize the currently active window."""
        print("[ACTION] Maximizing Window...")
        pyautogui.hotkey('win', 'up')

    # ============= GESTURE DETECTION =============

    def detect_gesture(self, hand_landmarks):
        """
        Classifies hand landmarks into 'fist', 'open_palm', or None.
        
        Logic: Checks if fingertip landmarks are above or below their 
        respective PIP (knuckle) joints in image Y-coordinates.
        """
        # Tip and PIP (Proximal Interphalangeal) landmark indices for fingers
        finger_tips = [8, 12, 16, 20]     # Index, Middle, Ring, Pinky Tips
        finger_pips = [6, 10, 14, 18]     # Index, Middle, Ring, Pinky Joints

        extended_fingers = 0

        # Check main 4 fingers (Y increases downwards in screen coordinates)
        for tip, pip in zip(finger_tips, finger_pips):
            if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[pip].y:
                extended_fingers += 1

        # Check thumb (tip 4 relative to IP joint 3)
        # Check horizontal distance or vertical depending on thumb angle
        thumb_tip = hand_landmarks.landmark[4]
        thumb_ip = hand_landmarks.landmark[3]
        if abs(thumb_tip.x - hand_landmarks.landmark[0].x) > abs(thumb_ip.x - hand_landmarks.landmark[0].x):
            extended_fingers += 1

        # Determine gesture based on extended finger count
        if extended_fingers >= 4:
            return "open_palm"
        elif extended_fingers <= 1:
            return "fist"
        
        return None

    # ============= MAIN CONTROLLER LOOP =============

    def run(self):
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("Error: Could not open webcam.")
            return

        print("--- Gesture Window Controller Active ---")
        print("Show a FIST to Minimize window.")
        print("Show an OPEN PALM to Maximize window.")
        print("Press 'q' to exit.\n")

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # Flip image horizontally for intuitive mirror view
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape

            # Convert BGR image to RGB for MediaPipe processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            detected_gesture = None

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Draw visual hand skeleton
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS
                    )

                    # Identify current gesture
                    detected_gesture = self.detect_gesture(hand_landmarks)

            # Process action with debouncing cooldown
            current_time = time.time()
            time_since_last_action = current_time - self.last_action_time

            status_text = "Status: Ready"

            if time_since_last_action < self.cooldown:
                status_text = f"Status: Cooldown ({self.cooldown - time_since_last_action:.1f}s)"
            elif detected_gesture == "fist":
                self.minimize_window()
                self.last_action_time = current_time
                status_text = "Action: Minimized!"
            elif detected_gesture == "open_palm":
                self.maximize_window()
                self.last_action_time = current_time
                status_text = "Action: Maximized!"

            # Render overlay on camera screen
            cv2.putText(frame, f"Gesture: {detected_gesture or 'None'}", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, status_text, (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            cv2.imshow('Gesture Window Controller', frame)

            if cv2.waitKey(5) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    controller = GestureWindowController(cooldown_seconds=1.5)
    controller.run()