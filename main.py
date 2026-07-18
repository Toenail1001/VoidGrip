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

                            # Handle gesture (mouse/keyboard control)
                            self._handle_gesture(gesture_type, metadata)

                        # Move cursor
                        screen_w, screen_h = self.system_controller.screen_width, self.system_controller.screen_height
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
                    "Pinch: Left Click | Move hand to move cursor",
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
        self.setWindowTitle("✋ VoidGrip - Gesture Control System")
        self.setGeometry(100, 100, WINDOW_WIDTH, WINDOW_HEIGHT)
        
        # Set modern stylesheet
        self.setStyleSheet(self._get_stylesheet())

        # Create worker and thread
        self.worker = GestureDetectionWorker()
        self.worker_thread = threading.Thread(target=self.worker.run, daemon=True)

        # Connect worker signals
        self.worker.frame_ready.connect(self._on_frame_ready)
        self.worker.status_changed.connect(self._on_status_changed)
        self.worker.gesture_detected.connect(self._on_gesture_detected)

        # Initialize UI
        self._init_ui()
    
    def _get_stylesheet(self):
        """Return modern stylesheet for the entire application."""
        return """
            QMainWindow {
                background-color: #1a1a1a;
            }
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QPushButton {
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 11pt;
                border: none;
                transition: all 0.3s;
            }
            QPushButton:hover {
                transform: translateY(-2px);
            }
            QPushButton:pressed {
                transform: translateY(0px);
            }
            QLabel {
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #333333;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                width: 18px;
                margin: -5px 0;
                background: #00d4ff;
                border-radius: 9px;
            }
        """

    def _init_ui(self):
        """Initialize user interface components."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout with margins
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(30)

        # Left side: Camera feed
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)

        # Camera frame label
        camera_frame_label = QLabel("Live Hand Detection")
        camera_frame_label.setFont(self._create_font("Segoe UI", 12, bold=True))
        camera_frame_label.setStyleSheet("color: #00d4ff; margin-bottom: 8px;")
        left_layout.addWidget(camera_frame_label)

        # Camera display label
        self.camera_label = QLabel()
        self.camera_label.setStyleSheet(
            "border: 3px solid #00d4ff; background-color: #0a0a0a; border-radius: 8px;"
        )
        self.camera_label.setFixedSize(CAMERA_FEED_WIDTH, CAMERA_FEED_HEIGHT)
        self.camera_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.camera_label)

        # Right side: Controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(20)

        # Title label
        title_label = QLabel("⚙️ GESTURE CONTROL")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #00d4ff;")
        right_layout.addWidget(title_label)
        
        # Divider line
        divider = QLabel()
        divider.setStyleSheet("background-color: #333333; height: 2px; margin: 5px 0px;")
        divider.setFixedHeight(2)
        right_layout.addWidget(divider)

        # Status indicator
        self.status_label = QLabel("🔴 Status: Stopped")
        self.status_label.setFont(self._create_font("Segoe UI", 11, bold=True))
        self.status_label.setStyleSheet("color: #ff4444; padding: 8px; border-radius: 5px; background-color: #2a1a1a;")
        right_layout.addWidget(self.status_label)

        # Gesture info
        self.gesture_label = QLabel("👆 Last Gesture: None")
        self.gesture_label.setFont(self._create_font("Segoe UI", 10))
        self.gesture_label.setStyleSheet("color: #00d4ff; padding: 8px; border-radius: 5px; background-color: #1a2a2a;")
        right_layout.addWidget(self.gesture_label)

        # Control buttons
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        
        # Start button
        self.start_button = QPushButton("▶ START DETECTION")
        self.start_button.setFont(self._create_font("Segoe UI", 11, bold=True))
        self.start_button.setStyleSheet(
            "background-color: #00d400; color: #000000; padding: 14px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self._on_start_clicked)
        button_layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("⏹ STOP DETECTION")
        self.stop_button.setFont(self._create_font("Segoe UI", 11, bold=True))
        self.stop_button.setStyleSheet(
            "background-color: #d40000; color: #ffffff; padding: 14px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.stop_button.setCursor(Qt.PointingHandCursor)
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        # Settings button
        self.settings_button = QPushButton("⚙️ CONFIGURE GESTURES")
        self.settings_button.setFont(self._create_font("Segoe UI", 11, bold=True))
        self.settings_button.setStyleSheet(
            "background-color: #00a4ff; color: #000000; padding: 14px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.clicked.connect(self._on_settings_clicked)
        button_layout.addWidget(self.settings_button)
        
        right_layout.addLayout(button_layout)
        right_layout.addSpacing(10)

        # Smoothing control section
        smooth_label = QLabel("📊 CURSOR SMOOTHING")
        smooth_label.setFont(self._create_font("Segoe UI", 11, bold=True))
        smooth_label.setStyleSheet("color: #00d4ff;")
        right_layout.addWidget(smooth_label)

        self.smoothing_slider = QSlider(Qt.Horizontal)
        self.smoothing_slider.setMinimum(1)
        self.smoothing_slider.setMaximum(10)
        self.smoothing_slider.setValue(SMOOTHING_FACTOR)
        self.smoothing_slider.sliderMoved.connect(self._on_smoothing_changed)
        self.smoothing_slider.setStyleSheet(
            "QSlider::groove:horizontal { background: #333333; height: 6px; border-radius: 3px; } "
            "QSlider::handle:horizontal { background: #00d4ff; width: 18px; margin: -6px 0; border-radius: 9px; }"
        )
        right_layout.addWidget(self.smoothing_slider)

        self.smoothing_value_label = QLabel(f"Value: {SMOOTHING_FACTOR}/10")
        self.smoothing_value_label.setFont(self._create_font("Segoe UI", 10))
        self.smoothing_value_label.setStyleSheet("color: #cccccc;")
        self.smoothing_value_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.smoothing_value_label)

        # Failsafe info
        if DISPLAY_FAILSAFE_INFO:
            failsafe_label = QLabel("⚠️ Emergency Stop: Top-left corner")
            failsafe_label.setFont(self._create_font("Segoe UI", 9))
            failsafe_label.setStyleSheet(
                "color: #ffaa00; background-color: #2a1a00; padding: 8px; border-radius: 5px; border-left: 3px solid #ffaa00;"
            )
            right_layout.addWidget(failsafe_label)

        # Stretch to fill remaining space
        right_layout.addStretch()

        # Info section
        info_text = ("📋 SUPPORTED GESTURES\n\n"
                     "👆 Point → Move cursor\n"
                     "🤏 Pinch → Click/Actions\n"
                     "👐 Palm Open → Show Desktop\n"
                     "👍 Thumbs Up → Volume Up\n"
                     "👎 Thumbs Down → Volume Down\n"
                     "🎬 Two Fingers → Play/Pause\n"
                     "👊 Fist → App Switch\n\n"
                     "Configure mappings for more!")
        info_label = QLabel(info_text)
        info_label.setFont(self._create_font("Segoe UI", 9))
        info_label.setStyleSheet(
            "color: #ffffff; background-color: #1a2a3a; padding: 12px; border-radius: 6px; "
            "border-left: 3px solid #00d4ff; line-height: 1.6;"
        )
        right_layout.addWidget(info_label)

        # Add layouts to main
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)
    
    def _create_font(self, family="Segoe UI", size=10, bold=False):
        """Create a consistent font across the application."""
        font = QFont(family, size)
        font.setBold(bold)
        return font

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
        """Update status label with modern styling."""
        if "Running" in status:
            self.status_label.setText("🟢 Status: Running")
            self.status_label.setStyleSheet(
                "color: #00ff00; padding: 8px; border-radius: 5px; background-color: #1a2a1a; font-weight: bold;"
            )
        else:
            self.status_label.setText("🔴 Status: Stopped")
            self.status_label.setStyleSheet(
                "color: #ff4444; padding: 8px; border-radius: 5px; background-color: #2a1a1a; font-weight: bold;"
            )

    def _on_gesture_detected(self, gesture_type, metadata):
        """Update gesture indicator with emoji."""
        gesture_emojis = {
            "pinch": "📌",
            "double_pinch": "📌📌",
            "palm_open": "👐",
            "thumbs_up": "👍",
            "thumbs_down": "👎",
            "fist": "👊",
            "two_fingers": "✌️",
            "swipe_left": "⬅️",
            "swipe_right": "➡️",
            "swipe_up": "⬆️",
            "swipe_down": "⬇️",
            "volume_up": "🔊",
            "volume_down": "🔉",
        }
        gesture_text = gesture_type.replace("_", " ").title()
        emoji = gesture_emojis.get(gesture_type, "👆")
        self.gesture_label.setText(f"{emoji} Last Gesture: {gesture_text}")

    def _on_smoothing_changed(self, value):
        """Handle smoothing slider change."""
        self.smoothing_value_label.setText(f"Value: {value}/10")
        if self.worker:
            self.worker.set_smoothing_factor(value)

    def closeEvent(self, event):
        """Handle window close."""
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
