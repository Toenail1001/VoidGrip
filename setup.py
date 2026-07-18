"""
Setup script for VoidGrip Gesture Control System.
Initializes the development environment with all dependencies.
"""

import os
import sys
import subprocess
import platform

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_info(text):
    """Print info message."""
    print(f"  ✓ {text}")

def print_error(text):
    """Print error message."""
    print(f"  ✗ {text}")

def check_python_version():
    """Check if Python version is 3.8 or higher."""
    print_header("CHECKING PYTHON VERSION")
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error("Python 3.8+ required")
        return False
    
    print_info(f"Python version compatible")
    return True

def install_dependencies():
    """Install required packages."""
    print_header("INSTALLING DEPENDENCIES")
    
    requirements = [
        "opencv-python>=4.5.0",
        "PyQt5>=5.15.0",
        "numpy>=1.19.0",
        "pyautogui>=0.9.53",
        "mediapipe>=0.8.0",
    ]
    
    for package in requirements:
        try:
            print(f"  Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", package])
            print_info(f"{package} installed")
        except subprocess.CalledProcessError:
            print_error(f"Failed to install {package}")
            return False
    
    return True

def verify_imports():
    """Verify all required packages can be imported."""
    print_header("VERIFYING IMPORTS")
    
    modules = {
        "cv2": "OpenCV",
        "PyQt5": "PyQt5",
        "numpy": "NumPy",
        "pyautogui": "PyAutoGUI",
        "mediapipe": "MediaPipe",
    }
    
    for module_name, display_name in modules.items():
        try:
            __import__(module_name)
            print_info(f"{display_name} available")
        except ImportError:
            print_error(f"{display_name} not found")
            return False
    
    return True

def create_default_config():
    """Create default configuration if it doesn't exist."""
    print_header("CHECKING CONFIGURATION")
    
    if os.path.exists("gesture_action_mappings.json"):
        print_info("Configuration file exists")
        return True
    
    print("  Creating default gesture mappings...")
    try:
        from modules import GestureMapper
        mapper = GestureMapper()
        print_info("Default configuration created")
        return True
    except Exception as e:
        print_error(f"Failed to create configuration: {e}")
        return False

def print_usage():
    """Print usage instructions."""
    print_header("SETUP COMPLETE!")
    print("""
  Run the application with:
    python main.py
  
  Features enabled:
    ✓ Palm-only hand detection (optimized)
    ✓ Real-time gesture recognition
    ✓ OS-level action control
    ✓ Customizable gesture mapping
    ✓ Modern PyQt5 GUI
  
  Supported Gestures:
    👆 Point → Move cursor
    🤏 Pinch → Click/Actions
    👐 Palm Open → Show Desktop
    👍 Thumbs Up → Volume Up
    👎 Thumbs Down → Volume Down
    🎬 Two Fingers → Play/Pause
    👊 Fist → App Switch
    ⬅️/➡️/⬆️/⬇️ Swipe → Multiple actions
  
  Tips:
    • Hide your face - only palm should be visible
    • Ensure good lighting for better detection
    • Use "Configure Gestures" to customize actions
    • Move to top-left corner to emergency stop
""")

def main():
    """Main setup routine."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "VoidGrip - Gesture Control System" + " " * 19 + "║")
    print("║" + " " * 20 + "Environment Setup" + " " * 32 + "║")
    print("╚" + "=" * 68 + "╝")
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Verifying packages", verify_imports),
        ("Creating configuration", create_default_config),
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print_error(f"\n{step_name} failed!")
            return False
    
    print_usage()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
