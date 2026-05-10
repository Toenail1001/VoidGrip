"""
Main GUI for Gesture Control System using PyQt5.
Provides UI for starting/stopping gesture detection, status display, and camera feed preview.
Integrates gesture detection with configurable action mapping.
"""

import sys
import cv2
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSlider, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, CAMERA_FEED_WIDTH, CAMERA_FEED_HEIGHT,
    UPDATE_INTERVAL_MS, SMOOTHING_FACTOR, DISPLAY_FAILSAFE_INFO
)
from modules import (
    HandTracker, GestureRecognizer, SystemController, GestureType,
    CursorSmoother, ActionController, GestureMapper
)
from gui_mapper import GestureMappingDialog


class GestureDetectionWorker(QObject):
    """
    Worker thread for gesture detection.
    Runs camera processing in background without freezing GUI.
    """

    # Signal emitted when frame is ready for display
    frame_ready = pyqtSignal(QImage)
    # Signal emitted when gesture is detected
    gesture_detected = pyqtSignal(str, dict)
    # Signal emitted for status updates
    status_changed = pyqtSignal(str)

    def __init__(self):
        """Initialize gesture detection worker."""
        super().__init__()
        self.running = False
        self.paused = False

        # Initialize components
        self.hand_tracker = HandTracker()
        self.gesture_recognizer = None
        self.system_controller = SystemController()
        self.cursor_smoother = None
        
        # Initialize gesture mapper and action controller
        self.gesture_mapper = GestureMapper()
        self.action_controller = ActionController()
        
        # Thread lock for safe gesture_mapper access
        self.mapper_lock = threading.Lock()

    def set_smoothing_factor(self, factor):
        """Update smoothing factor."""
        if self.cursor_smoother:
            self.cursor_smoother.smoothing_factor = factor

    def update_mappings(self, new_mappings):
        """
        Update gesture-action mappings.

        Args:
            new_mappings (dict): New gesture→action mappings
        """
        with self.mapper_lock:
            self.gesture_mapper.set_all_mappings(new_mappings)
            print(f"[MAPPINGS UPDATED] Gesture mappings changed via GUI")

    def run(self):
        """Main gesture detection loop (runs in separate thread)."""
        try:
            # Initialize on first run
            self.gesture_recognizer = GestureRecognizer(self.hand_tracker)
            self.cursor_smoother = CursorSmoother(SMOOTHING_FACTOR)

            # Open camera
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                self.status_changed.emit("ERROR: Could not open camera!")
                return

            self.running = True
            self.status_changed.emit("✓ Running")

            while self.running:
                if self.paused:
                    continue

                success, frame = cap.read()
                if not success:
                    self.status_changed.emit("ERROR: Could not read frame!")
                    break

                # Flip frame horizontally
                frame = cv2.flip(frame, 1)

                # Process frame with hand detection
                results, frame_with_landmarks = self.hand_tracker.process_frame(frame)

                # Handle detected hands
                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        # Recognize gesture
                        gesture_type, metadata = self.gesture_recognizer.get_gesture(
                            hand_landmarks
                        )

                        # Get hand measurements for visualization
                        thumb_pos = self.hand_tracker.get_landmark_position(
                            hand_landmarks, 4
                        )
                        index_pos = self.hand_tracker.get_landmark_position(
                            hand_landmarks, 8
                        )

                        # Calculate pinch distance
                        pinch_dist = self.gesture_recognizer.distance(thumb_pos, index_pos)

                        # Draw line between thumb and index (pinch indicator)
                        cv2.line(
                            frame_with_landmarks,
                            thumb_pos,
                            index_pos,
                            (0, 255, 0),
                            2
                        )

                        # Draw cursor indicator (index finger)
                        if self.gesture_recognizer.is_pinching:
                            # Larger circle when pinching
                            cv2.circle(
                                frame_with_landmarks,
                                index_pos,
                                20,
                                (0, 255, 0),
                                3
                            )
                            cv2.circle(
                                frame_with_landmarks,
                                index_pos,
                                15,
                                (0, 255, 0),
                                1
                            )
                        else:
                            # Normal cursor indicator
                            cv2.circle(
                                frame_with_landmarks,
                                index_pos,
                                10,
                                (255, 0, 0),
                                2
                            )

                        # Add pinch distance text
                        cv2.putText(
                            frame_with_landmarks,
                            f"Distance: {int(pinch_dist)}px",
                            (10, 60),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (255, 255, 255),
                            1
                        )

                        # Emit gesture signal
                        if gesture_type != GestureType.NONE:
                            self.gesture_detected.emit(
                                gesture_type.value,
                                metadata
                            )

                            # Handle gesture (mouse/keyboard control) - only if ACTIVE
                            # Skip fist activation toggle (handled internally)
                            if self.gesture_recognizer.is_active and gesture_type != GestureType.FIST:
                                self._handle_gesture(gesture_type, metadata)

                        # Move cursor - only if ACTIVE and not in FIST/TWO_FINGERS (freeze/scroll modes)
                        if self.gesture_recognizer.is_active and gesture_type not in (GestureType.RELEASE, GestureType.FIST, GestureType.TWO_FINGERS):
                            screen_w, screen_h = self.system_controller.screen_width, self.system_controller.screen_height
                            # Proper calibration: scale hand frame to screen resolution
                            target_x = (screen_w / self.hand_tracker.frame_width) * index_pos[0]
                            target_y = (screen_h / self.hand_tracker.frame_height) * index_pos[1]
                            self.cursor_smoother.move_to(target_x, target_y)

                # Add background bar for text readability
                cv2.rectangle(frame_with_landmarks, (0, 0), (640, 95), (0, 0, 0), -1)
                cv2.rectangle(frame_with_landmarks, (0, 0), (640, 95), (100, 100, 100), 1)

                # Add UI text to frame
                cv2.putText(
                    frame_with_landmarks,
                    "Gesture Control System - Live Camera Feed",
                    (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2
                )

                # Add instructions
                cv2.putText(
                    frame_with_landmarks,
                    "Pinch: Left Click | Double Pinch: Right Click | Move hand to move cursor",
                    (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (200, 200, 200),
                    1
                )

                # Add gesture indicator with better styling
                if self.gesture_recognizer.is_pinching:
                    # Draw indicator box
                    cv2.rectangle(
                        frame_with_landmarks,
                        (10, 80),
                        (200, 100),
                        (0, 255, 0),
                        -1
                    )
                    cv2.putText(
                        frame_with_landmarks,
                        "● PINCH DETECTED",
                        (15, 95),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 0, 0),
                        1
                    )
                else:
                    # Normal indicator
                    cv2.rectangle(
                        frame_with_landmarks,
                        (10, 80),
                        (200, 100),
                        (50, 50, 50),
                        -1
                    )
                    cv2.putText(
                        frame_with_landmarks,
                        "○ Ready",
                        (15, 95),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (200, 200, 200),
                        1
                    )
                
                # Add activation status indicator
                status_color = (0, 255, 0) if self.gesture_recognizer.is_active else (255, 0, 0)
                status_text = "✓ ACTIVE" if self.gesture_recognizer.is_active else "✗ PAUSED"
                cv2.rectangle(
                    frame_with_landmarks,
                    (400, 80),
                    (630, 100),
                    status_color,
                    -1
                )
                cv2.putText(
                    frame_with_landmarks,
                    status_text,
                    (410, 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0) if self.gesture_recognizer.is_active else (255, 255, 255),
                    1
                )

                # Convert frame for Qt display
                qt_image = self._convert_cv_to_qt(frame_with_landmarks)
                self.frame_ready.emit(qt_image)

        except Exception as e:
            self.status_changed.emit(f"ERROR: {str(e)}")
        finally:
            cap.release()
            self.running = False
            self.status_changed.emit("✗ Stopped")

    def _handle_gesture(self, gesture_type, metadata):
        """
        Execute system action for detected gesture using gesture-action mapping.

        Args:
            gesture_type (GestureType): Type of gesture detected
            metadata (dict): Gesture metadata
        """
        # Get gesture name from enum
        gesture_name = gesture_type.value
        
        # Look up the action for this gesture in the mapping (thread-safe)
        with self.mapper_lock:
            action_name = self.gesture_mapper.get_action(gesture_name)
        
        # Execute the action
        self.action_controller.execute_action(action_name)

    def _convert_cv_to_qt(self, cv_img):
        """Convert OpenCV image to Qt format."""
        h, w, ch = cv_img.shape
        bytes_per_line = 3 * w
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        qt_image = QImage(
            rgb_image.data,
            w,
            h,
            bytes_per_line,
            QImage.Format_RGB888
        )
        return qt_image

    def stop(self):
        """Stop gesture detection gracefully."""
        self.running = False
        if self.gesture_recognizer:
            self.gesture_recognizer.reset()
        if self.system_controller:
            self.system_controller.reset()


class GestureControlGUI(QMainWindow):
    """
    Main application window.
    """

    def __init__(self):
        """Initialize GUI window."""
        super().__init__()
        self.setWindowTitle("✋ Touchless Hand Gesture Control System")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Create worker and thread
        self.worker = GestureDetectionWorker()
        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)

        # Connect worker signals
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.status_changed.connect(self._on_status_changed)
        self.worker.gesture_detected.connect(self._on_gesture_detected)
        
        # Timer to update activation status
        self.activation_timer = QTimer()
        self.activation_timer.timeout.connect(self._update_activation_status)
        self.activation_timer.start(100)  # Update every 100ms

        # Initialize UI
        self._init_ui()

    def _init_ui(self):
        """Initialize user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Left side: Camera feed
        left_layout = QVBoxLayout()

        # Camera display label
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet("border: 2px solid #ccc; background-color: #000;")
        self.camera_label.setFixedSize(CAMERA_FEED_WIDTH, CAMERA_FEED_HEIGHT)
        self.camera_label.setAlignment(Qt.AlignCenter)  # Center the image
        left_layout.addWidget(self.camera_label)

        # Right side: Controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        # Title label
        title_label = QLabel("Gesture Controls")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        right_layout.addWidget(title_label)

        # Status indicator
        self.status_label = QLabel("Status: ✗ Stopped")
        self.status_label.setStyleSheet("color: red; font-weight: bold; font-size: 12pt;")
        right_layout.addWidget(self.status_label)

        # Gesture info
        self.gesture_label = QLabel("Last Gesture: None")
        self.gesture_label.setStyleSheet("color: #333; font-size: 10pt;")
        right_layout.addWidget(self.gesture_label)
        
        # Activation status
        self.activation_label = QLabel("System: ✓ ACTIVE")
        self.activation_label.setStyleSheet("color: green; font-weight: bold; font-size: 11pt;")
        right_layout.addWidget(self.activation_label)

        right_layout.addSpacing(20)

        # Start button
        self.start_button = QPushButton("▶ Start Detection")
        self.start_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; "
            "padding: 12px; font-size: 12pt; border-radius: 5px;"
        )
        self.start_button.clicked.connect(self._on_start_clicked)
        right_layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("⏹ Stop Detection")
        self.stop_button.setStyleSheet(
            "background-color: #f44336; color: white; font-weight: bold; "
            "padding: 12px; font-size: 12pt; border-radius: 5px;"
        )
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        right_layout.addWidget(self.stop_button)

        # Settings button
        self.settings_button = QPushButton("⚙️ Configure Gestures")
        self.settings_button.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold; "
            "padding: 10px; font-size: 11pt; border-radius: 5px;"
        )
        self.settings_button.clicked.connect(self._on_settings_clicked)
        right_layout.addWidget(self.settings_button)

        right_layout.addSpacing(20)

        # Smoothing control
        smooth_label = QLabel("Cursor Smoothing:")
        right_layout.addWidget(smooth_label)

        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setMinimum(1)
        self.smoothing_slider.setMaximum(10)
        self.smoothing_slider.setValue(SMOOTHING_FACTOR)
        self.smoothing_slider.sliderMoved.connect(self._on_smoothing_changed)
        right_layout.addWidget(self.smoothing_slider)

        self.smoothing_value_label = QLabel(f"Value: {SMOOTHING_FACTOR}")
        right_layout.addWidget(self.smoothing_value_label)

        right_layout.addSpacing(20)

        # Failsafe info
        if DISPLAY_FAILSAFE_INFO:
            failsafe_label = QLabel("💡 Failsafe: Move to top-left corner to stop")
            failsafe_label.setStyleSheet("color: #FF9800; font-size: 10pt;")
            right_layout.addWidget(failsafe_label)

        # Stretch to fill remaining space
        right_layout.addStretch()

        # Info section
        info_text = ("Supported Gestures:\n"
                     "• Point → Move cursor\n"
                     "• Pinch → Configured action\n"
                     "• Double pinch → Configured action\n"
                     "• Swipe up/down/left/right\n"
                     "• Palm open\n"
                     "• Thumbs up/down\n\n"
                     "Click 'Configure Gestures' to customize actions!")
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #666; font-size: 9pt; background-color: #f5f5f5; padding: 10px; border-radius: 5px;")
        right_layout.addWidget(info_label)

        # Add layouts to main
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

    def _on_start_clicked(self):
        """Handle start button click."""
        if not self.worker_thread.is_alive():
            self.worker = GestureDetectionWorker()
            self.worker.frame_ready.connect(self._on_frame_ready)
            self.worker.status_changed.connect(self._on_status_changed)
            self.worker.gesture_detected.connect(self._on_gesture_detected)
            self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)
            self.worker_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def _on_stop_clicked(self):
        """Handle stop button click."""
        if self.worker:
            self.worker.stop()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_settings_clicked(self):
        """Handle settings button click - opens gesture mapping configuration."""
        dialog = GestureMappingDialog(self)
        # Connect signal to update worker when mappings change
        dialog.mappings_changed.connect(self._on_mappings_updated)
        dialog.exec_()

    def _on_mappings_updated(self, mappings):
        """
        Handle gesture-action mapping updates.

        Args:
            mappings (dict): New gesture→action mappings
        """
        if self.worker:
            self.worker.update_mappings(mappings)

    def _on_frame_ready(self, qt_image):
        """Update camera display with new frame, preserving aspect ratio."""
        # Scale the image to fit the label while maintaining aspect ratio
        label_width = self.camera_label.width()
        label_height = self.camera_label.height()
        
        # Create pixmap from the Qt image
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit label while preserving aspect ratio
        scaled_pixmap = pixmap.scaled(label_width, label_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        # Set the scaled pixmap
        self.camera_label.setPixmap(scaled_pixmap)

    def _on_status_changed(self, status):
        """Update status label."""
        color = "green" if "Running" in status else "red"
        self.status_label.setText(f"Status: {status}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12pt;")
    
    def _update_activation_status(self):
        """Update activation status display from worker."""
        if self.worker and hasattr(self.worker, 'gesture_recognizer') and self.worker.gesture_recognizer:
            is_active = self.worker.gesture_recognizer.is_active
            status_text = "✓ ACTIVE" if is_active else "✗ PAUSED"
            color = "green" if is_active else "red"
            self.activation_label.setText(f"System: {status_text}")
            self.activation_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11pt;")

    def _on_gesture_detected(self, gesture_type, metadata):
        """Update gesture indicator."""
        gesture_text = gesture_type.replace("_", " ").title()
        self.gesture_label.setText(f"Last Gesture: {gesture_text}")

    def _on_smoothing_changed(self, value):
        """Handle smoothing slider change."""
        self.smoothing_value_label.setText(f"Value: {value}")
        if self.worker:
            self.worker.set_smoothing_factor(value)

    def closeEvent(self, event):
        """Handle window close."""
        if self.activation_timer:
            self.activation_timer.stop()
        if self.worker:
            self.worker.stop()
        event.accept()


def main():
    """Launch the application."""
    app = __import__('PyQt5.QtWidgets', fromlist=['QApplication']).QApplication(sys.argv)
    window = GestureControlGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
