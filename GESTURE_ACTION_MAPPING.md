# Gesture Control System - Gesture-Action Mapping Guide

## Overview

The upgraded system separates gesture detection from system actions. Users can now customize which action each gesture executes through a simple GUI.

## Architecture Flow

```
Hand Landmarks (MediaPipe)
    ↓
Gesture Recognition (gesture_recognizer.py)
    ↓ (Detected Gesture: e.g., "pinch")
Gesture Mapper (gesture_mapper.py)
    ↓ (Look up action: gesture_name → action_name)
Action Controller (action_controller.py)
    ↓ (Execute action)
System (mouse click, window minimize, volume, etc.)
```

## Module Breakdown

### 1. **GestureRecognizer** (`modules/gesture_recognizer.py`)
Detects gestures from hand landmarks and returns gesture names.

**Gestures Detected:**
- `pinch` - Thumb + Index fingers touching
- `double_pinch` - Two quick pinches
- `release` - Releasing from pinch
- `swipe_left` - Horizontal swipe left
- `swipe_right` - Horizontal swipe right
- `swipe_up` - Vertical swipe up
- `swipe_down` - Vertical swipe down
- `palm_open` - All fingers extended
- `thumbs_up` - Thumb up, fingers down
- `thumbs_down` - Thumb down, fingers up

### 2. **GestureMapper** (`modules/gesture_mapper.py`)
Maps gesture names to action names. Persists settings in JSON.

**Key Methods:**
```python
mapper = GestureMapper()
mapper.get_action("pinch")  # Returns "left_click"
mapper.set_mapping("pinch", "maximize_window")
mapper.get_all_mappings()  # Returns dict of all mappings
mapper.save_mappings()  # Save to JSON
```

**Default Mappings:**
```json
{
  "pinch": "left_click",
  "double_pinch": "right_click",
  "swipe_left": "switch_application",
  "swipe_right": "switch_application_reverse",
  "swipe_up": "maximize_window",
  "swipe_down": "minimize_window",
  "palm_open": "show_desktop",
  "thumbs_up": "volume_up",
  "thumbs_down": "volume_down"
}
```

### 3. **ActionController** (`modules/action_controller.py`)
Executes system actions by name.

**Available Actions:**

**Mouse:**
- `left_click` - Left mouse click
- `right_click` - Right mouse click
- `double_click` - Double click
- `middle_click` - Middle mouse click

**Window Management:**
- `minimize_window` - Minimize current window (Win+Down)
- `maximize_window` - Maximize current window (Win+Up)
- `close_window` - Close current window (Alt+F4)
- `toggle_window_state` - Toggle maximize/normal

**Application Control:**
- `switch_application` - Switch to next app (Alt+Tab)
- `switch_application_reverse` - Switch to previous app (Alt+Shift+Tab)
- `open_task_view` - Open Windows Task View (Win+Tab)

**Audio:**
- `volume_up` - Increase volume
- `volume_down` - Decrease volume
- `volume_mute` - Mute/unmute audio
- `media_play_pause` - Play/pause media
- `media_next` - Next track
- `media_previous` - Previous track

**Keyboard Shortcuts:**
- `undo` - Ctrl+Z
- `redo` - Ctrl+Y
- `copy` - Ctrl+C
- `paste` - Ctrl+V
- `cut` - Ctrl+X
- `select_all` - Ctrl+A
- `save` - Ctrl+S
- `screenshot` - Win+Shift+S

**System:**
- `do_nothing` - No action (disables gesture)
- `open_start_menu` - Open Windows Start Menu
- `open_run_dialog` - Open Run dialog (Win+R)
- `lock_computer` - Lock PC (Win+L)
- `show_desktop` - Show desktop (Win+D)

## How It Works

### Flow Diagram

```
User performs gesture
    ↓
GestureRecognizer.get_gesture() returns (gesture_type, metadata)
    ↓
GestureDetectionWorker._handle_gesture() is called
    ↓
gesture_name = gesture_type.value  # e.g., "pinch"
    ↓
action_name = gesture_mapper.get_action(gesture_name)  # e.g., "left_click"
    ↓
action_controller.execute_action(action_name)  # Execute the action
    ↓
System action performed
```

### Code Example

```python
from modules import GestureMapper, ActionController

# Initialize
mapper = GestureMapper()
controller = ActionController()

# When gesture is detected:
gesture_name = "pinch"

# Look up action
action_name = mapper.get_action(gesture_name)  # Returns "left_click"

# Execute action
controller.execute_action(action_name)
```

## Configuration GUI

### Opening Settings
Click the "⚙️ Configure Gestures" button in the main window.

### How to Customize
1. For each gesture, select an action from the dropdown
2. Changes are saved automatically to `gesture_action_mappings.json`
3. Click "🔄 Reset to Defaults" to restore original settings

### Screenshot Example
```
┌─────────────────────────────────────────┐
│ Gesture-Action Mappings                 │
├─────────────────────────────────────────┤
│ Pinch              [Left Click ▼]       │
│ Double Pinch       [Right Click ▼]      │
│ Swipe Left         [Switch App ▼]       │
│ Swipe Right        [Switch App Rev ▼]   │
│ Swipe Up           [Maximize ▼]         │
│ Swipe Down         [Minimize ▼]         │
│ Palm Open          [Show Desktop ▼]     │
│ Thumbs Up          [Volume Up ▼]        │
│ Thumbs Down        [Volume Down ▼]      │
│                                         │
│   [🔄 Reset]             [✓ Close]     │
└─────────────────────────────────────────┘
```

## Persistence

### gesture_action_mappings.json
Stored in the project root directory. Example:

```json
{
  "pinch": "left_click",
  "double_pinch": "right_click",
  "swipe_left": "switch_application",
  "swipe_right": "switch_application_reverse",
  "swipe_up": "maximize_window",
  "swipe_down": "minimize_window",
  "palm_open": "show_desktop",
  "thumbs_up": "volume_up",
  "thumbs_down": "volume_down"
}
```

**When is it saved?**
- On first run (creates file with defaults)
- Every time a user changes a mapping via GUI
- When user clicks "Reset to Defaults"

**When is it loaded?**
- When the application starts
- Loaded by `GestureMapper` class automatically

## Adding New Actions

To add a new system action:

1. **Add method to ActionController** (`modules/action_controller.py`):
```python
def my_new_action(self):
    """Description of what this action does."""
    # Implementation here
    return True
```

2. **Register in execute_action()** method:
```python
actions = {
    # ... existing actions ...
    'my_new_action': self.my_new_action,
}
```

3. **Add display name** in get_action_display_name():
```python
display_names = {
    # ... existing ...
    'my_new_action': 'My New Action',
}
```

4. **Use in mappings**:
The action will automatically appear in the GUI dropdowns!

## Adding New Gestures

To add a new gesture type:

1. **Add to GestureType enum** (`modules/gesture_recognizer.py`):
```python
class GestureType(Enum):
    # ... existing ...
    MY_GESTURE = "my_gesture"
```

2. **Implement detection method**:
```python
def detect_my_gesture(self, landmarks):
    """Detect my gesture."""
    # Landmark analysis
    return True  # or False
```

3. **Integrate into get_gesture()**:
```python
if self.detect_my_gesture(landmarks):
    return GestureType.MY_GESTURE, {"position": index_pos}
```

4. **Register in GestureMapper** (optional for first run):
```python
# Default mapping for new gesture
mapper.add_gesture("my_gesture", "do_nothing")
```

5. **Gesture automatically appears in GUI dropdowns!**

## File Structure

```
jarvis/
├── main.py                          # Main GUI + worker thread
├── gui_mapper.py                    # Gesture mapping configuration GUI
├── config.py                        # Configuration parameters
├── gesture_action_mappings.json     # Persistent gesture→action mappings
├── requirements.txt
├── README.md
└── modules/
    ├── __init__.py
    ├── hand_tracker.py              # MediaPipe hand detection
    ├── gesture_recognizer.py        # Gesture detection (NEW: swipes, palm, etc.)
    ├── action_controller.py         # System actions (NEW)
    ├── gesture_mapper.py            # Gesture→action mapping (NEW)
    ├── system_controller.py         # Legacy (kept for reference)
    └── cursor_smoother.py           # Cursor smoothing
```

## Troubleshooting

### Mappings not saving
- Check file permissions in the jarvis folder
- Ensure `gesture_action_mappings.json` is writable
- Try resetting to defaults

### Action not executing
- Verify action name is in `ActionController.execute_action()`
- Check system permissions (some actions need elevation)
- Check gesture is being detected (watch camera feed)

### New gesture not working
- Verify gesture is added to `GestureType` enum
- Check detection method returns correct gesture name
- Ensure gesture detection is integrated in `get_gesture()`

## Design Principles

1. **Separation of Concerns**: Gesture detection is separate from action execution
2. **Extensibility**: Easy to add new gestures and actions without modifying core logic
3. **User Customization**: Non-technical users can remap gestures via GUI
4. **Persistence**: Settings survive application restart
5. **Safety**: Actions can be disabled by mapping to "do_nothing"

## Performance Considerations

- Gesture detection runs in background thread (non-blocking)
- JSON parsing happens once at startup
- Mappings cached in memory during runtime
- Action execution is <10ms per gesture
