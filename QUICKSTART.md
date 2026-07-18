# VoidGrip - Gesture Control System

## Quick Start

### Windows Users
1. **Double-click** `run.bat` to start the application
   - Or run: `python main.py`

### All Users
1. Ensure Python 3.8+ is installed
2. Run: `python setup.py` to install dependencies
3. Run: `python main.py` to launch the application

---

## Features

### ✅ Supported Gestures

| Gesture | Action | Default Mapping |
|---------|--------|-----------------|
| 🤏 **Pinch** | Precise click/interaction | Left Click |
| 🤏🤏 **Double Pinch** | Quick screenshot | Screenshot |
| 👐 **Palm Open** | Show/hide desktop | Show Desktop |
| 👍 **Thumbs Up** | Increase volume/scroll up | Volume Up |
| 👎 **Thumbs Down** | Decrease volume/scroll down | Volume Down |
| ✌️ **Two Fingers** | Play/pause media | Media Play/Pause |
| 👊 **Fist** | Switch applications | Alt+Tab |
| ⬅️ **Swipe Left** | Previous/back | Switch App (Reverse) |
| ➡️ **Swipe Right** | Next/forward | Switch App |
| ⬆️ **Swipe Up** | Maximize window | Maximize Window |
| ⬇️ **Swipe Down** | Minimize window | Minimize Window |

---

## How to Use

### 1. **Starting the Application**
- Launch the app via `run.bat` or `python main.py`
- Wait for camera to initialize (2-3 seconds)
- You should see the camera feed with a cyan border

### 2. **Positioning Your Hand**
- **Important**: Keep only your **palm/hand visible**
- Hide your face - the app detects hands only, not faces
- Position hand in the lower portion of the camera frame (exclude head area)
- Ensure good lighting for optimal detection

### 3. **Using Gestures**
- Move your hand naturally to trigger gestures
- The app detects:
  - **Pinch gestures** (thumb touching index finger)
  - **Open palm** (all fingers extended)
  - **Fist** (fingers closed)
  - **Thumbs** (thumb up/down)
  - **Swipes** (horizontal/vertical hand movement)

### 4. **Monitoring Status**
- **Top-right corner shows**:
  - 🟢 **Green status** = System running
  - 🔴 **Red status** = System stopped
  - Last detected gesture with emoji

### 5. **Controlling the App**
- **Start Button** (🟢 Green): Begin hand tracking
- **Stop Button** (🔴 Red): Stop tracking
- **Configure Gestures** (⚙️ Cyan): Customize gesture→action mappings
- **Smoothing Slider**: Adjust hand tracking smoothness (0-10)

---

## Advanced Configuration

### Customizing Gesture Mappings

1. Click **"Configure Gestures"** button
2. Select a gesture from the dropdown
3. Choose desired action from the action dropdown
4. Click **"Map Gesture"** to save
5. Changes are saved automatically to `gesture_action_mappings.json`

### Available Actions
- **Volume**: volume_up, volume_down, volume_mute
- **Media**: media_play_pause, media_next, media_previous
- **Window**: minimize_window, maximize_window, show_desktop
- **Interaction**: left_click, right_click, double_click, screenshot
- **Navigation**: switch_application, switch_application_reverse
- **Keyboard**: undo, redo, copy, paste, cut, select_all

---

## Troubleshooting

### ❌ "No hand detected" or detection is poor
- **Solution**: 
  - Ensure your face is hidden (only palm visible)
  - Check lighting - make sure hands are well-lit
  - Increase smoothing slider value (7-10 recommended)
  - Move hand to center-lower portion of frame

### ❌ Application is slow/laggy
- **Solution**:
  - The app includes performance optimizations
  - If still slow, close other applications
  - Reduce camera resolution in advanced settings

### ❌ Gestures not triggering actions
- **Solution**:
  - Check gesture mappings in "Configure Gestures"
  - Ensure correct gesture is mapped to desired action
  - Make gesture slower and more deliberate
  - Verify OS can execute the action (test with keyboard)

### ❌ Camera feed not showing
- **Solution**:
  - Check if camera is plugged in and working
  - Close other applications using camera
  - Restart application
  - Check camera permissions in Windows settings

### ❌ Actions execute but gesture doesn't register
- **Solution**:
  - Action might execute from keyboard binding
  - Check Windows system hotkeys conflicting
  - Try different gesture
  - Verify OS isn't blocking the action

---

## Performance Tips

1. **Optimal Lighting**: Use bright, even lighting
2. **Clear Background**: Solid backgrounds work best
3. **Hand Visibility**: Keep palm fully in frame, face out
4. **Steady Movements**: Move gestures deliberately and smoothly
5. **Update Mappings**: Remove unused gestures to reduce confusion

---

## Technical Details

### System Requirements
- **OS**: Windows 7+
- **Python**: 3.8 or higher
- **Camera**: Any USB/built-in webcam
- **RAM**: 2GB minimum
- **CPU**: Dual-core processor

### Architecture
```
Camera Feed → Hand Detection (HSV) → Gesture Recognition → Action Mapping → OS Control
                    ↓
              Coordinate Scaling (for accuracy)
                    ↓
              Real-time Display
```

### Key Technologies
- **Hand Tracking**: OpenCV + HSV-based skin detection
- **Gesture Recognition**: Distance + position based algorithms
- **GUI**: PyQt5 with modern dark theme
- **OS Control**: PyAutoGUI keyboard/mouse simulation
- **Persistence**: JSON-based gesture mappings

---

## File Structure

```
VoidGrip/
├── main.py                          # Main application entry point
├── setup.py                         # Environment setup script
├── run.bat                          # Windows launcher
├── requirements.txt                 # Python dependencies
├── gesture_action_mappings.json     # User gesture configuration
├── config.py                        # Application settings
├── README.md                        # Full documentation
└── modules/
    ├── hand_tracker.py              # Hand detection (HSV-based)
    ├── gesture_recognizer.py        # Gesture identification
    ├── gesture_mapper.py            # Gesture→action mapping
    ├── action_controller.py         # OS action execution
    ├── cursor_smoother.py           # Hand position smoothing
    ├── system_controller.py         # System integration
    └── gesture_recognizer.py        # Alternative recognizer
```

---

## Settings (Advanced)

Edit `config.py` to customize:
- `DEBUG_MODE`: Enable logging (default: False)
- `FPS_TARGET`: Target frame rate (default: 30)
- `CONFIDENCE_THRESHOLD`: Gesture confidence requirement (default: 0.5)

---

## Known Limitations

- Currently optimized for **single hand** detection
- **Best with hands in lower 60% of frame** (excludes head/face area)
- Requires **well-lit environment** (>500 lux recommended)
- **One gesture at a time** (no multi-hand gestures)

---

## Future Enhancements

- [ ] Two-hand gesture support
- [ ] Machine learning gesture training
- [ ] Cloud gesture sync
- [ ] Advanced pose recognition
- [ ] Mobile app integration

---

## Support & Debugging

### Get Debug Information
Run with debug mode:
```bash
python main.py --debug
```

### Check Logs
Look at console output for gesture detection values and timing info.

### Report Issues
Include:
- Screenshot of hand position
- Console output/error messages
- Windows version
- Camera model (if known)
- Steps to reproduce

---

## Credits

**VoidGrip** - Advanced Gesture Control for Windows

Built with:
- OpenCV for computer vision
- PyQt5 for modern GUI
- PyAutoGUI for system control

---

*Last Updated: 2024*
*Version: 2.0 (GUI Redesign + Palm-Only Detection)*
