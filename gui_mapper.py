"""
Gesture Mapper GUI - Allows users to configure gesture-to-action mappings.
Provides an interface with dropdowns for each gesture.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QScrollArea, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from modules import GestureMapper, ActionController


class GestureMappingDialog(QDialog):
    """
    Dialog window for configuring gesture-to-action mappings.
    Shows a dropdown for each gesture to select the associated action.
    """

    # Signal emitted when mappings are changed
    mappings_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        """
        Initialize gesture mapping dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("⚙️ Configure Gesture Mappings")
        self.setGeometry(200, 100, 600, 700)

        # Initialize mappers
        self.gesture_mapper = GestureMapper()
        self.action_controller = ActionController()

        # Store combo boxes for easy access
        self.combo_boxes = {}

        # Initialize UI
        self._init_ui()

    def _init_ui(self):
        """Initialize the user interface."""
        main_layout = QVBoxLayout()

        # Title
        title_label = QLabel("Gesture-Action Mappings")
        title_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        main_layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Select an action for each gesture.\n"
            "Changes are automatically saved."
        )
        desc_label.setStyleSheet("color: #666; font-size: 10pt;")
        main_layout.addWidget(desc_label)

        # Scrollable area for gesture mappings
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Get all supported gestures
        gestures = self.gesture_mapper.get_supported_gestures()
        all_actions = self.action_controller.get_all_actions()

        # Create a row for each gesture
        for gesture_name in gestures:
            gesture_layout = QHBoxLayout()

            # Gesture name label
            gesture_label = QLabel(gesture_name.replace("_", " ").title())
            gesture_label.setMinimumWidth(150)
            gesture_layout.addWidget(gesture_label)

            # Action dropdown
            combo = QComboBox()
            combo.setMinimumWidth(250)

            # Add actions to dropdown with display names
            for action in all_actions:
                display_name = self.action_controller.get_action_display_name(action)
                combo.addItem(display_name, action)

            # Connect change signal
            combo.currentIndexChanged.connect(
                lambda idx, g=gesture_name, c=combo: self._on_mapping_changed(g, c)
            )

            # Select current mapping (block signals during initialization)
            combo.blockSignals(True)
            current_action = self.gesture_mapper.get_action(gesture_name)
            index = combo.findData(current_action)
            if index >= 0:
                combo.setCurrentIndex(index)
            combo.blockSignals(False)

            # Store reference
            self.combo_boxes[gesture_name] = combo

            gesture_layout.addWidget(combo)
            gesture_layout.addStretch()

            scroll_layout.addLayout(gesture_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Button layout
        button_layout = QHBoxLayout()

        # Reset to defaults button
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        # Close button
        close_btn = QPushButton("✓ Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px; "
            "font-weight: bold; border-radius: 4px;"
        )
        button_layout.addWidget(close_btn)

        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def _on_mapping_changed(self, gesture_name, combo_box):
        """
        Handle gesture-action mapping change.

        Args:
            gesture_name (str): Name of the gesture
            combo_box (QComboBox): The combo box that changed
        """
        action_name = combo_box.currentData()
        if action_name:
            success = self.gesture_mapper.set_mapping(gesture_name, action_name)
            if success:
                # Emit signal for listeners
                self.mappings_changed.emit(self.gesture_mapper.get_all_mappings())
                print(f"[MAPPING UPDATED] {gesture_name} → {action_name}")
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to save mapping. Check permissions.",
                )

    def _on_reset_defaults(self):
        """Reset all mappings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure? This will reset all mappings to defaults.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.gesture_mapper.reset_to_defaults()
            self._refresh_ui()
            QMessageBox.information(self, "Success", "Mappings reset to defaults.")
            self.mappings_changed.emit(self.gesture_mapper.get_all_mappings())

    def _refresh_ui(self):
        """Refresh UI to show current mappings."""
        for gesture_name, combo_box in self.combo_boxes.items():
            current_action = self.gesture_mapper.get_action(gesture_name)
            index = combo_box.findData(current_action)
            if index >= 0:
                combo_box.blockSignals(True)
                combo_box.setCurrentIndex(index)
                combo_box.blockSignals(False)

    def get_mappings(self):
        """
        Get current gesture-action mappings.

        Returns:
            dict: Current mappings
        """
        return self.gesture_mapper.get_all_mappings()
