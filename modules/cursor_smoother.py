"""
Cursor Smoother - Provides smooth cursor movement by averaging positions over time.
Prevents jittery mouse movements. Handles edge clamping to reach screen corners.
Uses Win32 SetCursorPos via ctypes for zero-latency cursor movement
(pyautogui.moveTo has a 100ms minimum duration which kills framerate).
"""

import ctypes
from config import SMOOTHING_FACTOR, INITIAL_CURSOR_X, INITIAL_CURSOR_Y, SCREEN_EDGE_MARGIN

# Win32 API — zero-latency cursor positioning
_user32 = ctypes.windll.user32


def _get_screen_size():
    """Return (width, height) of the primary monitor via Win32."""
    return _user32.GetSystemMetrics(0), _user32.GetSystemMetrics(1)


class CursorSmoother:
    """
    Smooths cursor movement to prevent jitter.
    Uses exponential moving average (EMA) for smoothing.
    Ensures cursor can reach all screen edges and corners.
    Uses Win32 SetCursorPos directly to avoid pyautogui's 100ms minimum delay.
    """

    def __init__(self, smoothing_factor=SMOOTHING_FACTOR):
        """
        Initialize cursor smoother.

        Args:
            smoothing_factor (int): Higher = smoother but slower. Recommended: 3-8
        """
        self.current_x = INITIAL_CURSOR_X
        self.current_y = INITIAL_CURSOR_Y
        self.smoothing_factor = max(1, smoothing_factor)  # Ensure at least 1

        # Get screen size via Win32 (no import of pyautogui needed here)
        self.screen_width, self.screen_height = _get_screen_size()

        # Apply edge margin to ensure corners are reachable
        self.min_x = int(self.screen_width * SCREEN_EDGE_MARGIN)
        self.max_x = int(self.screen_width * (1.0 - SCREEN_EDGE_MARGIN)) - 1
        self.min_y = int(self.screen_height * SCREEN_EDGE_MARGIN)
        self.max_y = int(self.screen_height * (1.0 - SCREEN_EDGE_MARGIN)) - 1

    def smooth_position(self, target_x, target_y):
        """
        Apply smoothing to cursor position with edge clamping.

        Args:
            target_x (float): Target X coordinate (0 to screen_width)
            target_y (float): Target Y coordinate (0 to screen_height)

        Returns:
            tuple: (smoothed_x, smoothed_y) clamped to screen bounds
        """
        # Clamp target to screen bounds before smoothing
        clamped_x = max(0, min(target_x, self.screen_width - 1))
        clamped_y = max(0, min(target_y, self.screen_height - 1))

        # Exponential moving average formula
        self.current_x = self.current_x + (clamped_x - self.current_x) / self.smoothing_factor
        self.current_y = self.current_y + (clamped_y - self.current_y) / self.smoothing_factor

        # Final clamp to screen bounds
        smoothed_x = max(0, min(int(self.current_x), self.screen_width - 1))
        smoothed_y = max(0, min(int(self.current_y), self.screen_height - 1))

        return smoothed_x, smoothed_y

    def move_to(self, x, y):
        """
        Move mouse to smoothed position using Win32 SetCursorPos.
        Zero blocking delay vs pyautogui.moveTo()'s 100ms minimum.

        Args:
            x (float): Target X coordinate
            y (float): Target Y coordinate
        """
        smooth_x, smooth_y = self.smooth_position(x, y)
        _user32.SetCursorPos(smooth_x, smooth_y)

    def reset(self):
        """Reset smoother to origin."""
        self.current_x = INITIAL_CURSOR_X
        self.current_y = INITIAL_CURSOR_Y
