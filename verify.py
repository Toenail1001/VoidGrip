# -*- coding: utf-8 -*-
"""
VoidGrip System Verification & Diagnostic Tool
Verifies all components are working correctly before launching the application.
"""

import sys
import json
import os
import subprocess
from pathlib import Path
import io

# Handle encoding for all platforms
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class VerificationResult:
    """Store verification results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []
    
    def add_pass(self, name, message=""):
        self.passed += 1
        self.results.append(("✓", "PASS", name, message))
    
    def add_fail(self, name, message=""):
        self.failed += 1
        self.results.append(("✗", "FAIL", name, message))
    
    def add_warn(self, name, message=""):
        self.warnings += 1
        self.results.append(("⚠", "WARN", name, message))
    
    def print_results(self):
        """Print all results in formatted table."""
        print("\n" + "=" * 80)
        print(f"  {'Status':<8} {'Result':<8} {'Component':<25} {'Details'}")
        print("=" * 80)
        
        for symbol, status, name, message in self.results:
            msg_display = message[:40] if message else ""
            print(f"  {symbol:<8} {status:<8} {name:<25} {msg_display}")
        
        print("=" * 80)
        print(f"\n  Summary: {self.passed} passed, {self.failed} failed, {self.warnings} warnings")
        
        if self.failed == 0:
            print("  ✓ All critical systems verified!\n")
            return True
        else:
            print(f"  ✗ {self.failed} critical issue(s) found!\n")
            return False

def check_system():
    """Run all system verification checks."""
    results = VerificationResult()
    
    print("\n╔" + "=" * 78 + "╗")
    print("║" + " " * 15 + "VoidGrip System Verification" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝\n")
    
    # 1. Python Version
    print("  Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        results.add_pass("Python Version", f"{version.major}.{version.minor}.{version.micro}")
    else:
        results.add_fail("Python Version", f"Need 3.8+, have {version.major}.{version.minor}")
    
    # 2. Required Modules
    print("  Checking required modules...")
    modules_check = {
        "cv2": "OpenCV (Camera & Image Processing)",
        "PyQt5": "PyQt5 (GUI Framework)",
        "numpy": "NumPy (Numerical Computing)",
        "pyautogui": "PyAutoGUI (OS Control)",
        "mediapipe": "MediaPipe (Optional ML)",
    }
    
    for module_name, display_name in modules_check.items():
        try:
            __import__(module_name)
            results.add_pass(f"Module: {module_name}", display_name)
        except ImportError:
            if module_name == "mediapipe":
                results.add_warn(f"Module: {module_name}", f"{display_name} (optional)")
            else:
                results.add_fail(f"Module: {module_name}", f"{display_name} missing")
    
    # 3. Configuration Files
    print("  Checking configuration files...")
    if os.path.exists("gesture_action_mappings.json"):
        try:
            with open("gesture_action_mappings.json", "r") as f:
                config = json.load(f)
                gestures_count = len(config)
            results.add_pass("Config: Gesture Mappings", f"{gestures_count} gestures mapped")
        except json.JSONDecodeError:
            results.add_fail("Config: Gesture Mappings", "File corrupted")
    else:
        results.add_warn("Config: Gesture Mappings", "File not found (will be created)")
    
    if os.path.exists("config.py"):
        results.add_pass("Config: Main Config", "config.py found")
    else:
        results.add_warn("Config: Main Config", "config.py not found")
    
    # 4. Module Files
    print("  Checking application modules...")
    required_modules = [
        ("modules/hand_tracker.py", "Hand Detection"),
        ("modules/gesture_recognizer.py", "Gesture Recognition"),
        ("modules/action_controller.py", "OS Action Control"),
        ("modules/gesture_mapper.py", "Gesture Mapping"),
        ("modules/cursor_smoother.py", "Cursor Smoothing"),
    ]
    
    for module_file, display_name in required_modules:
        if os.path.exists(module_file):
            results.add_pass(f"Module: {Path(module_file).name}", display_name)
        else:
            results.add_fail(f"Module: {Path(module_file).name}", f"{display_name} missing")
    
    # 5. Application Entry Point
    print("  Checking application entry point...")
    if os.path.exists("main.py"):
        try:
            # Try importing to check for syntax errors
            import ast
            with open("main.py", "r", encoding="utf-8") as f:
                ast.parse(f.read())
            results.add_pass("Application: main.py", "Syntax valid")
        except SyntaxError as e:
            results.add_fail("Application: main.py", f"Syntax error: {str(e)[:30]}")
        except Exception as e:
            results.add_pass("Application: main.py", "File exists and readable")
    else:
        results.add_fail("Application: main.py", "Entry point missing")
    
    # 6. Setup Tools
    print("  Checking setup tools...")
    if os.path.exists("setup.py"):
        results.add_pass("Tool: setup.py", "Environment setup tool")
    else:
        results.add_warn("Tool: setup.py", "Setup tool not found")
    
    if os.path.exists("run.bat"):
        results.add_pass("Tool: run.bat", "Windows launcher")
    else:
        results.add_warn("Tool: run.bat", "Windows launcher not found")
    
    # 7. Documentation
    print("  Checking documentation...")
    doc_files = [
        ("README.md", "Main documentation"),
        ("QUICKSTART.md", "Quick start guide"),
        ("GESTURE_ACTION_MAPPING.md", "Gesture mapping reference"),
    ]
    
    for doc_file, display_name in doc_files:
        if os.path.exists(doc_file):
            results.add_pass(f"Docs: {doc_file}", display_name)
        else:
            results.add_warn(f"Docs: {doc_file}", f"{display_name} (optional)")
    
    # 8. Try importing main modules
    print("  Testing module imports...")
    try:
        from modules import HandTracker
        results.add_pass("Import: HandTracker", "Hand detection module")
    except Exception as e:
        results.add_fail("Import: HandTracker", str(e)[:40])
    
    try:
        from modules import GestureRecognizer
        results.add_pass("Import: GestureRecognizer", "Gesture recognition module")
    except Exception as e:
        results.add_fail("Import: GestureRecognizer", str(e)[:40])
    
    try:
        from modules import ActionController
        results.add_pass("Import: ActionController", "OS action controller")
    except Exception as e:
        results.add_fail("Import: ActionController", str(e)[:40])
    
    try:
        from modules import GestureMapper
        results.add_pass("Import: GestureMapper", "Gesture mapper")
    except Exception as e:
        results.add_fail("Import: GestureMapper", str(e)[:40])
    
    return results

def print_recommendations(results):
    """Print recommendations based on verification results."""
    if results.failed == 0:
        print("  RECOMMENDATIONS:")
        print("  " + "=" * 76)
        print("  1. Run 'python main.py' or double-click 'run.bat' to launch")
        print("  2. Position your hand with palm visible, face hidden")
        print("  3. Click 'Start' button to begin gesture detection")
        print("  4. Try different gestures: pinch, palm open, thumbs, swipes, fist")
        print("  5. Use 'Configure Gestures' to customize action mappings")
        print("\n  TIPS FOR BEST RESULTS:")
        print("  • Good lighting improves detection accuracy")
        print("  • Keep only your hand/palm visible (hide face)")
        print("  • Make smooth, deliberate gesture movements")
        print("  • If detection is poor, increase smoothing slider")
        print("  " + "=" * 76)
    else:
        print("  NEXT STEPS:")
        print("  " + "=" * 76)
        if results.failed > 0:
            print("  1. Fix the errors shown above")
            print("  2. Run 'python setup.py' to install missing dependencies")
            print("  3. Verify all files are in the correct locations")
            print("  4. Check Python version is 3.8 or higher")
            print("  5. Try running this verification script again")
        print("  " + "=" * 76)

def main():
    """Main verification routine."""
    try:
        results = check_system()
        success = results.print_results()
        print_recommendations(results)
        return 0 if success else 1
    except Exception as e:
        print(f"\n✗ Verification failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
