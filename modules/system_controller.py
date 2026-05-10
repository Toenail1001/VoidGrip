"""
System Controller - Handles mouse and keyboard operations.
Provides a safe interface to PyAutoGUI functions with cooldown and validation.
"""

import time
import pyautogui
from config import CLICK_COOLDOWN, FAILSAFE_ENABLED, FAILSAFE_THRESHOLD


class SystemController:
    """
    Controls mouse and keyboard operations.
    Provides cooldown mechanisms to prevent accidental multiple clicks.
    """

    def __init__(self):
        """Initialize system controller."""
        pyautogui.FAILSAFE = FAILSAFE_ENABLED

        # Click tracking
        self.last_left_click_time = 0
        self.last_right_click_time = 0
        self.right_click_active = False

        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()

    def move_mouse(self, x, y):
        """
        Move mouse to position (with failsafe).

        Args:
            x (int): X coordinate
            y (int): Y coordinate
        """
        # Validate coordinates
        x = max(0, min(x, self.screen_width - 1))
        y = max(0, min(y, self.screen_height - 1))

        # Check failsafe condition (top-left corner)
        if x < FAILSAFE_THRESHOLD and y < FAILSAFE_THRESHOLD:
            self.emergency_stop()
            return

        pyautogui.moveTo(x, y)

    def left_click(self):
        """
        Perform left click with cooldown protection.

        Returns:
            bool: True if click was performed, False if on cooldown
        """
        current_time = time.time()

        if current_time - self.last_left_click_time < CLICK_COOLDOWN:
            return False  # Still in cooldown

        pyautogui.click()
        self.last_left_click_time = current_time
        return True

    def right_click_start(self):
        """
        Start holding right click (for drag operations).

        Returns:
            bool: True if started, False if already active
        """
        if self.right_click_active:
            return False

        current_time = time.time()
        if current_time - self.last_right_click_time < CLICK_COOLDOWN:
            return False

        pyautogui.mouseDown(button="right")
        self.right_click_active = True
        self.last_right_click_time = current_time
        return True

    def right_click_end(self):
        """
        Stop holding right click.

        Returns:
            bool: True if stopped, False if wasn't active
        """
        if not self.right_click_active:
            return False

        pyautogui.mouseUp(button="right")
        self.right_click_active = False
        return True

    def double_click(self):
        """
        Perform double click.

        Returns:
            bool: True if performed, False if on cooldown
        """
        current_time = time.time()

        if current_time - self.last_left_click_time < CLICK_COOLDOWN:
            return False

        pyautogui.click()
        time.sleep(0.05)  # Small delay between clicks
        pyautogui.click()
        self.last_left_click_time = current_time
        return True

    def type_text(self, text):
        """
        Type text using keyboard.

        Args:
            text (str): Text to type
        """
        pyautogui.typewrite(text, interval=0.05)

    def press_key(self, key):
        """
        Press a single key.

        Args:
            key (str): Key name (e.g., 'space', 'enter', 'alt')
        """
        pyautogui.press(key)

    def hotkey(self, *keys):
        """
        Perform keyboard hotkey combination.

        Args:
            *keys: Key names (e.g., 'ctrl', 'alt', 'del')
        """
        pyautogui.hotkey(*keys)

    def emergency_stop(self):
        """
        Emergency stop - releases any held keys/buttons.
        Triggered when mouse moves to top-left corner.
        """
        if self.right_click_active:
            pyautogui.mouseUp(button="right")
            self.right_click_active = False

    def reset(self):
        """Reset all state (useful on shutdown)."""
        if self.right_click_active:
            pyautogui.mouseUp(button="right")
            self.right_click_active = False

        self.last_left_click_time = 0
        self.last_right_click_time = 0
