# ✋ VoidGrip: Touchless Hand Gesture Control

A modular Python desktop application for controlling your computer using hand gestures. This project is currently a **Work In Progress (WIP)**. We are focusing on reliability and developer experience.

## ⚠️ Developer Notice: Work In Progress
This repository is the "Development" version. You will find several experimental features and known bugs. See the [Known Issues](#-known-issues) section below.

## 📋 Features

- **Activation Gate (Fist Hold)**: System only tracks/clicks when active. Hold a **Fist** for 0.5s to toggle status.
- **Improved Cursor Reach**: Calibration math ensures you can reach all corners of the screen.
- **Action Debouncing**: Per-action cooldowns to prevent accidental spam (clicks/scrolls).
- **Movement vs Action Modes**:
  - **Index Point**: Move cursor.
  - **Pinch**: Left click.
  - **Two Fingers**: Scroll mode.
  - **Fist**: Pause/Resume system.

## 📁 Project Structure
... (existing structure) ...

## 🚀 Getting Started
... (existing installation steps) ...

## 🎮 How to Use
1. **Launch**: `python main.py`
2. **Activate**: The system starts **Active**. To pause, hold a **Fist** for 0.5s.
3. **Controls**:
   - **Point**: Move cursor.
   - **Pinch**: Left click.
   - **Two Fingers**: Scroll (configure in settings).
   - **Double Pinch**: Right click.

## 🛠️ Contribution Guide (For the Squad)
We use a **Feature Branch** workflow to keep the main code stable:
1. **Pull the latest**: `git pull origin main`
2. **Create a branch**: `git checkout -b fix-your-feature-name`
3. **Commit your work**: `git commit -m "WIP: Added better filtering for jitter"`
4. **Push & PR**: `git push origin fix-your-feature-name`, then open a Pull Request on GitHub.

## 🐛 Known Issues
- [ ] **Jitter**: High smoothing (8+) causes input lag.
- [ ] **False Clicks**: Pinch detection can trigger during fast hand movement.
- [ ] **Static Thresholds**: Hand size variation might require manual config tuning in `config.py`.
- [ ] **Documentation**: Module docstrings need updating to match new activation logic.

## ⚙️ Configuration
All tunable parameters are in `config.py`. Adjust `PINCH_DISTANCE_THRESHOLD` or `FIST_THRESHOLD` if detection is too sensitive for your camera/lighting.
```

## 📚 Architecture & Design

### Module Overview

#### **config.py**
Centralized configuration. Modify here to tune system behavior without editing code logic.

#### **modules/cursor_smoother.py**
`CursorSmoother` class provides smooth cursor movement using exponential moving average (EMA). Prevents jittery cursor movement.

```python
smoother = CursorSmoother(smoothing_factor=5)
smoother.move_to(x, y)  # Moves to smoothed position
```

#### **modules/hand_tracker.py**
`HandTracker` class wraps MediaPipe hand detection. Handles frame processing and landmark extraction.

```python
tracker = HandTracker()
results, frame_with_landmarks = tracker.process_frame(frame)
x, y = tracker.get_landmark_position(results.multi_hand_landmarks[0], 8)  # Index tip
```

#### **modules/gesture_recognizer.py**
`GestureRecognizer` detects gestures from hand landmarks. Maintains state for complex gestures like double-pinch.

```python
recognizer = GestureRecognizer(tracker)
gesture_type, metadata = recognizer.get_gesture(hand_landmarks)
# Returns: (GestureType.PINCH, {"position": (x, y)})
```

#### **modules/system_controller.py**
`SystemController` handles mouse and keyboard operations via PyAutoGUI with cooldown protection.

```python
controller = SystemController()
controller.move_mouse(x, y)
controller.left_click()
controller.right_click_start()
controller.right_click_end()
```

#### **main.py**
PyQt5 GUI with two main classes:
- `GestureDetectionWorker`: Runs gesture detection in background thread
- `GestureControlGUI`: Main application window with controls

## 🔧 Extending with New Gestures

Adding a new gesture is straightforward. Here's how to add a **swipe gesture**:

### Step 1: Add to GestureType Enum
Edit `modules/gesture_recognizer.py`:

```python
class GestureType(Enum):
    # ... existing gestures ...
    SWIPE_LEFT = "swipe_left"
    SWIPE_RIGHT = "swipe_right"
```

### Step 2: Implement Detection Method
Add to `GestureRecognizer` class:

```python
def detect_swipe(self, landmarks):
    """
    Detect horizontal swipe gesture.
    Returns: ("left"/"right", distance)
    """
    wrist = self.hand_tracker.get_landmark_position(landmarks, 0)
    index = self.hand_tracker.get_landmark_position(landmarks, 8)
    
    horizontal_distance = index[0] - wrist[0]
    
    if abs(horizontal_distance) > SWIPE_DISTANCE_THRESHOLD:
        direction = "left" if horizontal_distance < 0 else "right"
        return direction
    return None
```

### Step 3: Integrate into get_gesture()
Modify the main `get_gesture()` method:

```python
def get_gesture(self, landmarks):
    # ... existing pinch detection ...
    
    # Add swipe detection
    swipe_direction = self.detect_swipe(landmarks)
    if swipe_direction == "left":
        return GestureType.SWIPE_LEFT, {"position": index_pos}
    elif swipe_direction == "right":
        return GestureType.SWIPE_RIGHT, {"position": index_pos}
```

### Step 4: Handle in Worker
Edit `main.py` `_handle_gesture()` method:

```python
def _handle_gesture(self, gesture_type, metadata):
    # ... existing code ...
    elif gesture_type == GestureType.SWIPE_LEFT:
        self.system_controller.hotkey('alt', 'left')  # Back navigation
    elif gesture_type == GestureType.SWIPE_RIGHT:
        self.system_controller.hotkey('alt', 'right')  # Forward navigation
```

## 📊 Hand Landmark Reference

MediaPipe identifies 21 landmarks per hand (0-20):

```
0:  Wrist
1-4: Thumb (1=CMC, 2=MCP, 3=IP, 4=Tip)
5-8: Index finger (5=MCP, 6=PIP, 7=DIP, 8=Tip)
9-12: Middle finger (9=MCP, 10=PIP, 11=DIP, 12=Tip)
13-16: Ring finger (13=MCP, 14=PIP, 15=DIP, 16=Tip)
17-20: Pinky finger (17=MCP, 18=PIP, 19=DIP, 20=Tip)
```

## 🐛 Troubleshooting

### Camera not opening
- Ensure webcam is connected and not in use by another application
- Try a different camera index in `config.py`: `CAMERA_INDEX = 1`

### Jittery cursor
- Increase `SMOOTHING_FACTOR` in `config.py` (1-10)
- Use the GUI slider to adjust in real-time

### Multiple clicks detected
- Increase `CLICK_COOLDOWN` in `config.py` (default: 0.4 seconds)

### Pinch detection not working
- Reduce `PINCH_DISTANCE_THRESHOLD` in `config.py`
- Ensure better lighting conditions

### GUI window too small
- Adjust `WINDOW_WIDTH` and `WINDOW_HEIGHT` in `config.py`

## 📝 Code Quality Notes

- **Type Hints**: Used sparingly for student project simplicity
- **Docstrings**: All classes and public methods documented
- **Comments**: Key algorithmic sections explained
- **Modularity**: Separated concerns make code testable and maintainable
- **Thread Safety**: GUI remains responsive during gesture detection

## 🎓 Academic Notes

This project demonstrates:
- **Computer Vision**: Hand detection and landmark tracking
- **State Machines**: Gesture recognition with state transitions
- **GUI Development**: PyQt5 widgets and signals/slots
- **Multi-threading**: Background processing without blocking UI
- **Object-Oriented Design**: Modular, extensible architecture
- **Software Engineering**: Clean code, configuration management, documentation

## 📄 License

This is an academic project. Feel free to use, modify, and extend.

## 🤝 Contributing

Ideas for extensions:
- Voice feedback on detected gestures
- Gesture recording and playback
- Custom gesture training with ML
- Support for two-handed gestures
- Gesture history/logging
- Performance optimization for low-end systems
- Integration with specific applications (Excel, Photoshop, etc.)
