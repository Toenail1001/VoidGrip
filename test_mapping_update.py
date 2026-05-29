"""Test script to verify gesture mapping updates work correctly."""

import json
import threading
import time
from modules import GestureMapper, ActionController

def test_mapping_update():
    """Test that mapping updates work end-to-end."""
    
    print("=" * 60)
    print("Testing Gesture Mapping Update System")
    print("=" * 60)
    
    # Create mappers
    print("\n1. Creating gesture mapper and action controller...")
    mapper = GestureMapper()
    controller = ActionController()
    
    # Check initial state
    initial_action = mapper.get_action("pinch")
    print(f"   Initial 'pinch' mapping: {initial_action}")
    
    # Simulate what happens when dialog changes a mapping
    print("\n2. Changing 'pinch' mapping to 'middle_click'...")
    mapper.set_mapping("pinch", "middle_click")
    
    # Verify change was saved
    new_action = mapper.get_action("pinch")
    print(f"   New 'pinch' mapping: {new_action}")
    
    # Verify JSON file was updated
    print("\n3. Checking JSON file...")
    with open("gesture_action_mappings.json", "r") as f:
        saved_mappings = json.load(f)
    print(f"   JSON file shows: pinch = {saved_mappings['pinch']}")
    
    # Test set_all_mappings (what worker receives from signal)
    print("\n4. Testing set_all_mappings (like worker update)...")
    new_mappings = mapper.get_all_mappings()
    new_mappings["pinch"] = "double_click"
    print(f"   Setting pinch to: {new_mappings['pinch']}")
    
    mapper.set_all_mappings(new_mappings)
    current = mapper.get_action("pinch")
    print(f"   Current mapping after set_all_mappings: {current}")
    
    # Verify JSON was updated again
    with open("gesture_action_mappings.json", "r") as f:
        saved_mappings = json.load(f)
    print(f"   JSON file now shows: pinch = {saved_mappings['pinch']}")
    
    # Test action execution
    print("\n5. Testing action execution...")
    result = controller.execute_action("left_click")
    print(f"   execute_action('left_click') returned: {result}")
    
    result = controller.execute_action("do_nothing")
    print(f"   execute_action('do_nothing') returned: {result}")
    
    # Reset to defaults
    print("\n6. Resetting to defaults...")
    mapper.reset_to_defaults()
    reset_action = mapper.get_action("pinch")
    print(f"   After reset, 'pinch' mapping: {reset_action}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_mapping_update()
