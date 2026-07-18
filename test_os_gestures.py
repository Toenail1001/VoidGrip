"""Regression tests for OS-level gesture actions."""

from types import SimpleNamespace

from modules import ActionController, GestureMapper, GestureRecognizer, GestureType


class FakeHandTracker:
    def get_landmark_position(self, landmarks, landmark_index):
        return landmarks.landmark[landmark_index]


class FakeLandmarks:
    def __init__(self, landmark_positions):
        self.landmark = landmark_positions


def test_default_os_gesture_mappings_exist():
    mapper = GestureMapper()
    expected = {
        "thumbs_up": "volume_up",
        "thumbs_down": "volume_down",
        "palm_open": "show_desktop",
        "swipe_left": "switch_application",
        "swipe_right": "switch_application_reverse",
        "swipe_up": "maximize_window",
        "swipe_down": "minimize_window",
    }
    for gesture, action in expected.items():
        assert mapper.get_action(gesture) == action


def test_action_controller_supports_os_actions():
    controller = ActionController()
    for action_name in [
        "volume_up",
        "volume_down",
        "media_play_pause",
        "screenshot",
        "show_desktop",
        "minimize_window",
        "maximize_window",
        "switch_application",
    ]:
        assert action_name in controller.get_all_actions()


def test_palm_open_gesture_is_recognized():
    tracker = FakeHandTracker()
    recognizer = GestureRecognizer(tracker)
    landmarks = FakeLandmarks([
        (0, 0),
        (80, 120),
        (100, 140),
        (120, 160),
        (140, 180),
        (60, 80),
        (90, 90),
        (120, 110),
        (150, 130),
        (180, 150),
        (70, 110),
        (90, 130),
        (120, 150),
        (150, 170),
        (80, 140),
        (100, 160),
        (120, 180),
        (140, 200),
        (90, 170),
        (110, 190),
        (130, 210),
    ])

    gesture_type, _ = recognizer.get_gesture(landmarks)
    assert gesture_type == GestureType.PALM_OPEN


if __name__ == "__main__":
    test_default_os_gesture_mappings_exist()
    test_action_controller_supports_os_actions()
    test_palm_open_gesture_is_recognized()
    print("OS gesture action tests passed")
