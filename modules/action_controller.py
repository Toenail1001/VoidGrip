"""
Action Controller - Executes system actions like clicks, window operations, and keyboard shortcuts.
This is the execution layer for all gesture-triggered system operations.
"""

import pyautogui
import time
import subprocess
import sys
from config import CLICK_COOLDOWN


class ActionController:
    """
    Executes system actions with proper timing and safety.
    All system operations go through this class for centralized control.
    """

    def __init__(self):
        """Initialize action controller."""
        self.last_action_time = time.time()
        # Per-action cooldown tracking for debouncing
        self.action_cooldowns = {
            'left_click': 0.1,  # 100ms between clicks
            'right_click': 0.1,
            'double_click': 0.2,
            'middle_click': 0.1,
            'scroll_up': 0.05,
            'scroll_down': 0.05,
        }
        self.last_action_time_per_action = {}

    # ============= MOUSE ACTIONS =============

    def left_click(self):
        """Perform left mouse click."""
        pyautogui.click()
        return True

    def right_click(self):
        """Perform right mouse click."""
        pyautogui.click(button='right')
        return True

    def double_click(self):
        """Perform double click."""
        pyautogui.click()
        time.sleep(0.05)
        pyautogui.click()
        return True

    def middle_click(self):
        """Perform middle mouse click."""
        pyautogui.click(button='middle')
        return True

    def scroll_up(self):
        """Scroll up."""
        pyautogui.scroll(3)  # Scroll up 3 clicks
        return True

    def scroll_down(self):
        """Scroll down."""
        pyautogui.scroll(-3)  # Scroll down 3 clicks
        return True

    # ============= WINDOW OPERATIONS =============

    def minimize_window(self):
        """Minimize current window."""
        # Windows: Win + Down minimizes window
        pyautogui.hotkey('win', 'down')
        return True

    def maximize_window(self):
        """Maximize current window."""
        # Windows: Win + Up maximizes window
        pyautogui.hotkey('win', 'up')
        return True

    def close_window(self):
        """Close current window."""
        pyautogui.hotkey('alt', 'F4')
        return True

    def toggle_window_state(self):
        """Toggle between maximized and normal state."""
        # This simulates double-clicking title bar or using Win+Up twice
        pyautogui.hotkey('win', 'up')
        return True

    # ============= APPLICATION SWITCHING =============

    def switch_application(self):
        """Switch to next application (Alt+Tab)."""
        pyautogui.hotkey('alt', 'tab')
        return True

    def switch_application_reverse(self):
        """Switch to previous application (Alt+Shift+Tab)."""
        pyautogui.hotkey('alt', 'shift', 'tab')
        return True

    def open_task_view(self):
        """Open Windows Task View (Win+Tab)."""
        pyautogui.hotkey('win', 'tab')
        return True

    # ============= VOLUME CONTROL =============

    def volume_up(self):
        """Increase system volume."""
        # Windows media key for volume up
        pyautogui.press('volumeup')
        return True

    def volume_down(self):
        """Decrease system volume."""
        # Windows media key for volume down
        pyautogui.press('volumedown')
        return True

    def volume_mute(self):
        """Mute/unmute system volume."""
        pyautogui.press('volumemute')
        return True

    # ============= MEDIA CONTROLS =============

    def media_play_pause(self):
        """Play or pause media."""
        pyautogui.press('playpause')
        return True

    def media_next(self):
        """Play next track."""
        pyautogui.press('nexttrack')
        return True

    def media_previous(self):
        """Play previous track."""
        pyautogui.press('prevtrack')
        return True

    # ============= KEYBOARD SHORTCUTS =============

    def undo(self):
        """Undo action (Ctrl+Z)."""
        pyautogui.hotkey('ctrl', 'z')
        return True

    def redo(self):
        """Redo action (Ctrl+Y)."""
        pyautogui.hotkey('ctrl', 'y')
        return True

    def copy(self):
        """Copy (Ctrl+C)."""
        pyautogui.hotkey('ctrl', 'c')
        return True

    def paste(self):
        """Paste (Ctrl+V)."""
        pyautogui.hotkey('ctrl', 'v')
        return True

    def cut(self):
        """Cut (Ctrl+X)."""
        pyautogui.hotkey('ctrl', 'x')
        return True

    def select_all(self):
        """Select all (Ctrl+A)."""
        pyautogui.hotkey('ctrl', 'a')
        return True

    def save(self):
        """Save (Ctrl+S)."""
        pyautogui.hotkey('ctrl', 's')
        return True

    def screenshot(self):
        """Take screenshot (Windows key + Print Screen)."""
        pyautogui.hotkey('win', 'shift', 's')
        return True

    # ============= UTILITY ACTIONS =============

    def do_nothing(self):
        """No operation - useful for disabled gestures."""
        return False

    def open_start_menu(self):
        """Open Windows Start Menu."""
        pyautogui.press('win')
        return True

    def open_run_dialog(self):
        """Open Run dialog (Win+R)."""
        pyautogui.hotkey('win', 'r')
        return True

    def lock_computer(self):
        """Lock computer (Win+L)."""
        pyautogui.hotkey('win', 'l')
        return True

    def show_desktop(self):
        """Show desktop (Win+D)."""
        pyautogui.hotkey('win', 'd')
        return True

    # ============= GENERIC KEYBOARD ACTIONS =============

    def press_key(self, key):
        """
        Press a single key.

        Args:
            key (str): Key name (e.g., 'space', 'enter', 'esc')
        """
        pyautogui.press(key)
        return True

    def hotkey(self, *keys):
        """
        Perform keyboard hotkey combination.

        Args:
            *keys: Key names (e.g., 'ctrl', 'alt', 'del')
        """
        pyautogui.hotkey(*keys)
        return True

    def type_text(self, text):
        """
        Type text.

        Args:
            text (str): Text to type
        """
        pyautogui.typewrite(text, interval=0.05)
        return True

    # ============= ACTION EXECUTION =============

    def execute_action(self, action_name):
        """
        Execute an action by name with debouncing.

        Args:
            action_name (str): Name of the action to execute

        Returns:
            bool: True if action was executed, False otherwise
        """
        # Check debounce/cooldown for this specific action
        current_time = time.time()
        last_time = self.last_action_time_per_action.get(action_name, 0)
        cooldown = self.action_cooldowns.get(action_name, 0.1)  # Default 100ms cooldown
        
        if current_time - last_time < cooldown:
            return False  # Still in cooldown period
        
        # Map action names to methods
        actions = {
            # Mouse actions
            'left_click': self.left_click,
            'right_click': self.right_click,
            'double_click': self.double_click,
            'middle_click': self.middle_click,
            'scroll_up': self.scroll_up,
            'scroll_down': self.scroll_down,

            # Window operations
            'minimize_window': self.minimize_window,
            'maximize_window': self.maximize_window,
            'close_window': self.close_window,
            'toggle_window_state': self.toggle_window_state,

            # Application switching
            'switch_application': self.switch_application,
            'switch_application_reverse': self.switch_application_reverse,
            'open_task_view': self.open_task_view,

            # Volume control
            'volume_up': self.volume_up,
            'volume_down': self.volume_down,
            'volume_mute': self.volume_mute,

            # Media controls
            'media_play_pause': self.media_play_pause,
            'media_next': self.media_next,
            'media_previous': self.media_previous,

            # Keyboard shortcuts
            'undo': self.undo,
            'redo': self.redo,
            'copy': self.copy,
            'paste': self.paste,
            'cut': self.cut,
            'select_all': self.select_all,
            'save': self.save,
            'screenshot': self.screenshot,

            # Utility
            'do_nothing': self.do_nothing,
            'open_start_menu': self.open_start_menu,
            'open_run_dialog': self.open_run_dialog,
            'lock_computer': self.lock_computer,
            'show_desktop': self.show_desktop,
        }

        # Execute the action if it exists
        if action_name in actions:
            try:
                actions[action_name]()
                self.last_action_time_per_action[action_name] = current_time  # Record cooldown
                return True
            except Exception as e:
                print(f"Error executing action '{action_name}': {e}")
                return False
        else:
            print(f"Unknown action: {action_name}")
            return False

    def get_all_actions(self):
        """
        Get list of all available actions.

        Returns:
            list: List of action names
        """
        return [
            'left_click',
            'right_click',
            'double_click',
            'middle_click',
            'scroll_up',
            'scroll_down',
            'minimize_window',
            'maximize_window',
            'close_window',
            'toggle_window_state',
            'switch_application',
            'switch_application_reverse',
            'open_task_view',
            'volume_up',
            'volume_down',
            'volume_mute',
            'media_play_pause',
            'media_next',
            'media_previous',
            'undo',
            'redo',
            'copy',
            'paste',
            'cut',
            'select_all',
            'save',
            'screenshot',
            'do_nothing',
            'open_start_menu',
            'open_run_dialog',
            'lock_computer',
            'show_desktop',
        ]

    def get_action_display_name(self, action_name):
        """
        Get human-readable name for action.

        Args:
            action_name (str): Internal action name

        Returns:
            str: Display name
        """
        display_names = {
            'left_click': 'Left Click',
            'right_click': 'Right Click',
            'double_click': 'Double Click',
            'middle_click': 'Middle Click',
            'scroll_up': 'Scroll Up',
            'scroll_down': 'Scroll Down',
            'minimize_window': 'Minimize Window',
            'maximize_window': 'Maximize Window',
            'close_window': 'Close Window',
            'toggle_window_state': 'Toggle Window State',
            'switch_application': 'Switch Application',
            'switch_application_reverse': 'Switch Application (Reverse)',
            'open_task_view': 'Open Task View',
            'volume_up': 'Volume Up',
            'volume_down': 'Volume Down',
            'volume_mute': 'Mute/Unmute',
            'media_play_pause': 'Play/Pause Media',
            'media_next': 'Next Track',
            'media_previous': 'Previous Track',
            'undo': 'Undo',
            'redo': 'Redo',
            'copy': 'Copy',
            'paste': 'Paste',
            'cut': 'Cut',
            'select_all': 'Select All',
            'save': 'Save',
            'screenshot': 'Take Screenshot',
            'do_nothing': '(No Action)',
            'open_start_menu': 'Open Start Menu',
            'open_run_dialog': 'Open Run Dialog',
            'lock_computer': 'Lock Computer',
            'show_desktop': 'Show Desktop',
        }
        return display_names.get(action_name, action_name.replace('_', ' ').title())
