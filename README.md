# ✋ VoidGrip: Touchless Hand Gesture Control

A modular Python desktop application for controlling your computer using hand gestures. 

## 📋 Features

- **Full GUI Configuration**: Dynamically map any gesture to any system action without editing code. Mappings are saved instantly to a local JSON file.
- **Dynamic Auto-Scroll**: Proportional scrolling based on your hand's distance from the center of the screen, just like browser middle-clicking. Includes a custom visual scroll cursor indicator.
- **Intelligent Window Management**: Robust window maximization and minimization using direct native Win32 API calls. Features a 3-tier fallback mechanism to remember and restore applications even if they are completely sent to the taskbar.
- **Real-Time App Switching**: Seamless Alt+Tab cycling. Hold a gesture (like Sign of Horns) to keep the switcher open and step through applications; drop the gesture to commit and switch.
- **Cursor Smoothing**: Exponential Moving Average (EMA) applied to pointer coordinates to prevent jitter, adjustable in real-time via the GUI slider.

## 🤲 Supported Gestures

You can map any of these gestures to any action in the system via the configuration dialog:
- **Pinch**: Index and thumb tips touching.
- **Peace Sign**: Index and middle fingers extended.
- **Sign of Horns (🤘)**: Index and pinky extended, middle and ring folded, thumb folded.
- **ILY Sign (🤟)**: Index, pinky and thumb extended, middle and ring folded.
- **Four Fingers**: Index, middle, ring, pinky extended with thumb folded.
- **Open Palm**: All five fingers extended.
- **Fist**: All fingers folded.
- **Thumbs Up / Down**: Thumbs extended up or down with other fingers folded.

*(Cursor movement is persistently mapped to tracking the index fingertip)*

## ⚙️ Supported Actions

- **Mouse Controls**: Left, Right, Middle, Double Clicks, Auto-Scroll Mode
- **Window Operations**: Maximize, Minimize, Close, Toggle State
- **Application Switching**: Next App (Alt+Tab), Previous App (Alt+Shift+Tab), Task View
- **Media & Volume**: Play/Pause, Next/Prev Track, Volume Up/Down/Mute
- **Generic Keybinds**: Copy/Paste/Undo/Redo/Save/Screenshot/Show Desktop/Lock Computer

## 📁 Architecture Overview

#### **`config.py`**
Centralized configuration limits for camera dimensions, smoothing bounds, and gesture distance thresholds. 

#### **`modules/action_controller.py`**
The execution layer. Wraps `pyautogui` and raw `ctypes` Win32 APIs for precise OS-level control. Handles debouncing, background `EnumWindows` scanning, and stateful operations (like logically holding Alt down for the App Switcher until a gesture ceases).

#### **`modules/cursor_smoother.py`**
Provides fluid pointer traversal using mathematical moving average equations.

#### **`modules/gesture_recognizer.py`**
Converts MediaPipe landmark coordinate geometry into strict logical states. Uses a hierarchical cascade sequence to categorize poses while rigorously checking anti-finger states to prevent false positives (e.g. specifically verifying the thumb is tucked to separate the *Four Fingers* state from an *Open Palm*).

#### **`modules/hand_tracker.py`**
MediaPipe initialization and basic 21-point hand tracking wrapper.

#### **`modules/gesture_mapper.py` & `gui_mapper.py`**
Dynamic action binding matrix and the corresponding settings layout modal.

#### **`main.py`**
The PyQt5 frontend core. Showcases the live overlay video feed, status indicators, and spawns parallel daemon threads for purely non-blocking responsive camera loops. 

## 🚀 Getting Started

1. **Install requirements**: 
   ```bash
   pip install opencv-python mediapipe pyautogui PyQt5
   ```
2. **Launch the application**: 
   ```bash
   python main.py
   ```
3. **Configure**: Click the blue `⚙️ Configure Gestures` button on the right panel to set up your desired mapping schema. 
4. **Failsafe**: If you lose control of the mouse pointer, abruptly slam the physical mouse cursor into any corner of your monitor (the PyAutoGUI failsafe bounds) to instantly halt operations.
