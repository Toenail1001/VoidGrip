"""Integration test for gesture mapping flow."""

import json
import threading
import time
from modules import GestureMapper, ActionController, GestureRecognizer
from modules import GestureType

def test_complete_flow():
    """Test the complete flow from mapping change to gesture execution."""
    
    print("=" * 70)
    print("COMPLETE GESTURE MAPPING FLOW TEST")
    print("=" * 70)
    
    # Step 1: Initialize components (like worker does)
    print("\n[STEP 1] Worker initializes gesture mapper at startup...")
    worker_mapper = GestureMapper()
    print(f"  Worker loaded: {worker_mapper.get_all_mappings()}")
    
    # Step 2: Gesture detected - check initial action
    print("\n[STEP 2] Gesture 'pinch' detected, looking up action...")
    initial_action = worker_mapper.get_action("pinch")
    print(f"  Initial action for 'pinch': {initial_action}")
    
    # Step 3: Dialog opens and creates its own mapper
    print("\n[STEP 3] User opens Configure Gestures dialog...")
    dialog_mapper = GestureMapper()
    print(f"  Dialog loaded: {dialog_mapper.get_all_mappings()}")
    
    # Step 4: User changes a mapping in the dialog
    print("\n[STEP 4] User changes 'pinch' mapping from 'left_click' to 'screenshot'...")
    dialog_mapper.set_mapping("pinch", "screenshot")
    print(f"  Dialog saved change to JSON")
    
    # Step 5: Dialog emits signal (gets all current mappings)
    print("\n[STEP 5] Dialog emits mappings_changed signal...")
    updated_mappings = dialog_mapper.get_all_mappings()
    print(f"  Signal contains: pinch = {updated_mappings['pinch']}")
    
    # Step 6: Worker receives signal and updates
    print("\n[STEP 6] Worker receives signal and updates its mapper...")
    worker_mapper.set_all_mappings(updated_mappings)
    print(f"  Worker mapper updated")
    
    # Step 7: Next gesture detected uses new mapping
    print("\n[STEP 7] Next gesture 'pinch' detected, looking up action...")
    new_action = worker_mapper.get_action("pinch")
    print(f"  Updated action for 'pinch': {new_action}")
    
    # Step 8: Verify the action exists in ActionController
    print("\n[STEP 8] Verifying action can be executed...")
    controller = ActionController()
    all_actions = controller.get_all_actions()
    if new_action in all_actions:
        print(f"  ✓ Action '{new_action}' is valid and can be executed")
    else:
        print(f"  ✗ ERROR: Action '{new_action}' is NOT in valid actions list!")
        print(f"  Valid actions: {all_actions}")
        return False
    
    # Step 9: Verify JSON was actually updated
    print("\n[STEP 9] Verify JSON file was updated...")
    with open("gesture_action_mappings.json", "r") as f:
        json_mappings = json.load(f)
    if json_mappings["pinch"] == "screenshot":
        print(f"  ✓ JSON file shows: pinch = {json_mappings['pinch']}")
    else:
        print(f"  ✗ ERROR: JSON shows pinch = {json_mappings['pinch']}, expected 'screenshot'!")
        return False
    
    # Step 10: Reset to defaults for next test
    print("\n[STEP 10] Resetting to defaults...")
    worker_mapper.reset_to_defaults()
    print(f"  Reset: {worker_mapper.get_all_mappings()}")
    
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED - Gesture mapping system is working correctly!")
    print("=" * 70)
    return True

if __name__ == "__main__":
    success = test_complete_flow()
    exit(0 if success else 1)
