"""
Gesture Mapper - Maps gestures to actions and handles persistence.
Allows users to customize what action each gesture triggers.
"""

import json
import os
from pathlib import Path


class GestureMapper:
    """
    Maps gesture names to action names with JSON persistence.
    Users can customize which action each gesture executes.
    """

    # Default gesture mappings (provided at first run)
    DEFAULT_MAPPINGS = {
        # Core gestures - high quality, reliable
        "pinch": "left_click",
        "double_pinch": "right_click",
        "fist": "do_nothing",  # Reserved for activation toggle (hold 0.5s to pause/resume)
        "palm_open": "do_nothing",  # Previously used for activation, now available for other uses
        "two_fingers": "do_nothing",  # Scroll mode - special handling in worker
        # Deprecated/disabled by default - low quality
        "swipe_left": "do_nothing",
        "swipe_right": "do_nothing",
        "swipe_up": "do_nothing",
        "swipe_down": "do_nothing",
        "thumbs_up": "do_nothing",
        "thumbs_down": "do_nothing",
    }

    def __init__(self, mappings_file="gesture_action_mappings.json"):
        """
        Initialize gesture mapper.

        Args:
            mappings_file (str): Path to JSON file for storing mappings
        """
        self.mappings_file = mappings_file
        self.mappings = {}
        self.load_mappings()

    def load_mappings(self):
        """
        Load gesture mappings from JSON file.
        If file doesn't exist, create it with default mappings.
        """
        if os.path.exists(self.mappings_file):
            try:
                with open(self.mappings_file, 'r') as f:
                    self.mappings = json.load(f)
                print(f"Loaded gesture mappings from {self.mappings_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading mappings file: {e}")
                print("Using default mappings")
                self.mappings = self.DEFAULT_MAPPINGS.copy()
                self.save_mappings()
        else:
            # First run - create file with defaults
            self.mappings = self.DEFAULT_MAPPINGS.copy()
            self.save_mappings()
            print(f"Created new mappings file: {self.mappings_file}")

    def save_mappings(self):
        """Save current gesture mappings to JSON file."""
        try:
            with open(self.mappings_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            print(f"Saved gesture mappings to {self.mappings_file}")
            return True
        except IOError as e:
            print(f"Error saving mappings file: {e}")
            return False

    def set_mapping(self, gesture_name, action_name):
        """
        Set the action for a specific gesture.

        Args:
            gesture_name (str): Name of the gesture
            action_name (str): Name of the action to execute

        Returns:
            bool: True if mapping was set successfully
        """
        self.mappings[gesture_name] = action_name
        return self.save_mappings()

    def get_action(self, gesture_name):
        """
        Get the action assigned to a gesture.

        Args:
            gesture_name (str): Name of the detected gesture

        Returns:
            str: Action name, or 'do_nothing' if gesture not mapped
        """
        return self.mappings.get(gesture_name, "do_nothing")

    def get_all_mappings(self):
        """
        Get all gesture→action mappings.

        Returns:
            dict: Dictionary of all mappings
        """
        return self.mappings.copy()

    def set_all_mappings(self, new_mappings):
        """
        Replace all mappings at once.

        Args:
            new_mappings (dict): New gesture→action mappings

        Returns:
            bool: True if saved successfully
        """
        self.mappings = new_mappings
        return self.save_mappings()

    def reset_to_defaults(self):
        """
        Reset all mappings to defaults.

        Returns:
            bool: True if reset successfully
        """
        self.mappings = self.DEFAULT_MAPPINGS.copy()
        return self.save_mappings()

    def get_supported_gestures(self):
        """
        Get list of all gesture names that can be mapped.

        Returns:
            list: List of gesture names
        """
        return list(self.DEFAULT_MAPPINGS.keys())

    def add_gesture(self, gesture_name, default_action="do_nothing"):
        """
        Add a new gesture to the mapper (for new gesture types).

        Args:
            gesture_name (str): Name of the new gesture
            default_action (str): Default action for this gesture

        Returns:
            bool: True if added successfully
        """
        if gesture_name not in self.mappings:
            self.mappings[gesture_name] = default_action
            return self.save_mappings()
        return True

    def gesture_exists(self, gesture_name):
        """
        Check if a gesture is mapped.

        Args:
            gesture_name (str): Name of the gesture

        Returns:
            bool: True if gesture has a mapping
        """
        return gesture_name in self.mappings

    def export_mappings(self, filename):
        """
        Export current mappings to a file (for backup/sharing).

        Args:
            filename (str): Path to export file

        Returns:
            bool: True if exported successfully
        """
        try:
            with open(filename, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            return True
        except IOError as e:
            print(f"Error exporting mappings: {e}")
            return False

    def import_mappings(self, filename):
        """
        Import mappings from a file.

        Args:
            filename (str): Path to import file

        Returns:
            bool: True if imported successfully
        """
        try:
            with open(filename, 'r') as f:
                imported_mappings = json.load(f)
            self.mappings = imported_mappings
            return self.save_mappings()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing mappings: {e}")
            return False
