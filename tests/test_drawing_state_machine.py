"""Tests for DrawingBoardController state machine, interpolation, and gesture handling."""

import math
import numpy as np
from unittest.mock import MagicMock
from controllers.drawing_controller import (
    DrawingBoardController,
    STATE_NEUTRAL,
    STATE_DRAW,
    STATE_ERASE,
    STATE_COLOR_SWITCH,
)


# ── Helpers ────────────────────────────────────────────────

class _FakeLandmark:
    def __init__(self, x=0.5, y=0.5):
        self.x = x
        self.y = y


def _make_landmarks(index_up=False, middle_up=False, ring_up=False, pinky_up=False):
    """Build a mock hand_landmarks object with controllable finger states."""
    # Create 21 landmarks (MediaPipe hand has indices 0-20)
    marks = [_FakeLandmark() for _ in range(21)]

    # For each finger pair (tip, pip): tip.y < pip.y  ⇒ finger is UP
    for tip_idx, pip_idx, is_up in [
        (8, 6, index_up),
        (12, 10, middle_up),
        (16, 14, ring_up),
        (20, 18, pinky_up),
    ]:
        marks[tip_idx].y = 0.3 if is_up else 0.7
        marks[pip_idx].y = 0.5

    # Wrist & middle MCP for palm center
    marks[0].x = 0.5
    marks[0].y = 0.8
    marks[9].x = 0.5
    marks[9].y = 0.5

    # Index tip position for drawing
    marks[8].x = 0.4

    lm = MagicMock()
    lm.landmark = marks
    return lm


# ── Gesture classification ─────────────────────────────────

class TestDetectGesture:
    def test_draw_gesture(self):
        ctrl = DrawingBoardController()
        lm = _make_landmarks(index_up=True)
        assert ctrl.detect_gesture(lm) == STATE_DRAW

    def test_erase_gesture(self):
        ctrl = DrawingBoardController()
        lm = _make_landmarks(index_up=True, middle_up=True, ring_up=True, pinky_up=True)
        assert ctrl.detect_gesture(lm) == STATE_ERASE

    def test_color_switch_gesture(self):
        ctrl = DrawingBoardController()
        lm = _make_landmarks(index_up=True, pinky_up=True)
        assert ctrl.detect_gesture(lm) == STATE_COLOR_SWITCH

    def test_fist_gesture(self):
        ctrl = DrawingBoardController()
        lm = _make_landmarks()  # all down
        assert ctrl.detect_gesture(lm) == STATE_NEUTRAL

    def test_ambiguous_falls_to_neutral(self):
        ctrl = DrawingBoardController()
        # middle only → not a recognized pattern → NEUTRAL
        lm = _make_landmarks(middle_up=True)
        assert ctrl.detect_gesture(lm) == STATE_NEUTRAL


# ── State machine hysteresis ───────────────────────────────

class TestStateMachineTransition:
    def test_stays_neutral_on_init(self):
        ctrl = DrawingBoardController()
        assert ctrl._state == STATE_NEUTRAL

    def test_single_frame_does_not_transition(self):
        ctrl = DrawingBoardController()
        ctrl._transition(STATE_DRAW)
        # One frame isn't enough — needs _CONFIRM_FRAMES (2)
        assert ctrl._state == STATE_NEUTRAL

    def test_two_frames_transitions(self):
        ctrl = DrawingBoardController()
        ctrl._transition(STATE_DRAW)
        ctrl._transition(STATE_DRAW)
        assert ctrl._state == STATE_DRAW

    def test_flickering_input_blocked(self):
        ctrl = DrawingBoardController()
        # Alternate between DRAW and ERASE every frame → should stay NEUTRAL
        for _ in range(10):
            ctrl._transition(STATE_DRAW)
            ctrl._transition(STATE_ERASE)
        assert ctrl._state == STATE_NEUTRAL

    def test_transition_resets_tracking(self):
        ctrl = DrawingBoardController()
        ctrl.last_point = (100, 100)
        ctrl.eraser_last_pos = (200, 200)
        # Transition to ERASE
        ctrl._transition(STATE_ERASE)
        ctrl._transition(STATE_ERASE)
        assert ctrl._state == STATE_ERASE
        # last_point should be cleared (old state was not DRAW→ERASE)
        assert ctrl.last_point is None

    def test_staying_in_state_keeps_counter_reset(self):
        ctrl = DrawingBoardController()
        ctrl._transition(STATE_DRAW)
        ctrl._transition(STATE_DRAW)
        assert ctrl._state == STATE_DRAW
        # Repeat DRAW → counter stays reset, no candidate
        ctrl._transition(STATE_DRAW)
        assert ctrl._candidate_state is None


# ── Interpolation ──────────────────────────────────────────

class TestInterpolation:
    def test_nearby_points_yield_single(self):
        pts = list(DrawingBoardController._interpolate((0, 0), (1, 1), step=4))
        assert len(pts) == 1
        assert pts[0] == (1, 1)

    def test_distant_points_yield_multiple(self):
        pts = list(DrawingBoardController._interpolate((0, 0), (100, 0), step=10))
        assert len(pts) >= 10
        # End point should be last
        assert pts[-1] == (100, 0)

    def test_diagonal_interpolation(self):
        pts = list(DrawingBoardController._interpolate((0, 0), (30, 40), step=5))
        dist = math.hypot(30, 40)  # 50
        assert len(pts) >= int(dist / 5)

    def test_all_points_between_endpoints(self):
        pts = list(DrawingBoardController._interpolate((10, 10), (50, 10), step=5))
        for x, y in pts:
            assert 10 <= x <= 50
            assert y == 10


# ── Hard erase with interpolation ──────────────────────────

class TestHardErase:
    def test_erase_clears_canvas_area(self):
        ctrl = DrawingBoardController()
        ctrl.canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
        ctrl.hard_erase((320, 240))
        # Centre of erase should be black
        assert ctrl.canvas[240, 320].sum() == 0

    def test_erase_interpolates_between_positions(self):
        ctrl = DrawingBoardController()
        ctrl.canvas = np.ones((480, 640, 3), dtype=np.uint8) * 255
        ctrl.eraser_last_pos = (100, 240)
        ctrl.hard_erase((300, 240))
        # Midpoint (200, 240) should also be erased
        assert ctrl.canvas[240, 200].sum() == 0


# ── Canvas lifecycle ───────────────────────────────────────

class TestLifecycle:
    def test_on_enter_resets_state(self):
        ctrl = DrawingBoardController()
        ctrl._state = STATE_DRAW
        ctrl.last_point = (10, 10)
        ctrl.on_enter()
        assert ctrl._state == STATE_NEUTRAL
        assert ctrl.last_point is None
        assert ctrl.canvas is None

    def test_clear_canvas(self):
        ctrl = DrawingBoardController()
        ctrl.canvas = np.ones((480, 640, 3), dtype=np.uint8) * 128
        ctrl.clear_canvas()
        assert ctrl.canvas.sum() == 0
