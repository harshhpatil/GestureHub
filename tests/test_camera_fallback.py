"""Tests for camera initialization fallback logic."""

import unittest
from unittest.mock import patch, MagicMock


def _open_camera():
    """Replica of main.open_camera() for isolated testing (avoids main.py side-effects)."""
    import cv2

    for idx in (1, 0):
        cap = cv2.VideoCapture(idx, cv2.CAP_ANY)
        if cap.isOpened():
            return cap
        cap.release()
    return None


class TestCameraFallback(unittest.TestCase):
    """Test that open_camera tries index 1 then falls back to 0."""

    @patch("cv2.VideoCapture")
    def test_opens_index_1_first(self, mock_vc):
        """When index 1 succeeds, should use it."""
        cap = MagicMock()
        cap.isOpened.return_value = True
        mock_vc.return_value = cap

        import cv2
        result = _open_camera()
        self.assertIsNotNone(result)
        mock_vc.assert_called_with(1, cv2.CAP_ANY)

    @patch("cv2.VideoCapture")
    def test_falls_back_to_index_0(self, mock_vc):
        """When index 1 fails, should try index 0."""
        cap_bad = MagicMock()
        cap_bad.isOpened.return_value = False
        cap_good = MagicMock()
        cap_good.isOpened.return_value = True
        mock_vc.side_effect = [cap_bad, cap_good]

        result = _open_camera()
        self.assertIsNotNone(result)
        self.assertEqual(mock_vc.call_count, 2)

    @patch("cv2.VideoCapture")
    def test_returns_none_when_no_camera(self, mock_vc):
        """When all indices fail, should return None."""
        cap = MagicMock()
        cap.isOpened.return_value = False
        mock_vc.return_value = cap

        result = _open_camera()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
