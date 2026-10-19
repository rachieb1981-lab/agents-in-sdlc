import unittest
from unittest.mock import Mock

# Import the get_shape_position function from convert-pptx.py
import sys
from pathlib import Path

# Add script directory to sys.path
script_dir = Path(__file__).parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

import importlib
convert_pptx = importlib.import_module("convert-pptx")
get_shape_position = convert_pptx.get_shape_position


class TestGetShapePosition(unittest.TestCase):

    def test_normal_position_and_dimensions(self):
        """Test calculation when shape attributes are normal non-zero values."""
        shape = Mock()
        shape.left = 100
        shape.top = 200
        shape.width = 400
        shape.height = 300

        slide_width = 1000
        slide_height = 1000

        left, top, width, height = get_shape_position(shape, slide_width, slide_height)

        self.assertAlmostEqual(left, 10.0)
        self.assertAlmostEqual(top, 20.0)
        self.assertAlmostEqual(width, 40.0)
        self.assertAlmostEqual(height, 30.0)

    def test_falsy_or_none_shape_dimensions(self):
        """Test default fallbacks when left, top, width, or height are None or 0."""
        shape = Mock()
        shape.left = None
        shape.top = 0
        shape.width = None
        shape.height = 0

        slide_width = 1000
        slide_height = 1000

        left, top, width, height = get_shape_position(shape, slide_width, slide_height)

        self.assertEqual(left, 0)
        self.assertEqual(top, 0)
        self.assertEqual(width, 50)
        self.assertEqual(height, 30)

    def test_exception_handling_returns_default_box(self):
        """Test fallback position values when an exception is raised (e.g. invalid attribute access or division by zero)."""
        shape = Mock()
        # Triggering attribute error or zero division
        type(shape).left = property(fget=Mock(side_effect=AttributeError("Error accessing left")))

        slide_width = 1000
        slide_height = 1000

        left, top, width, height = get_shape_position(shape, slide_width, slide_height)

        self.assertEqual((left, top, width, height), (5, 5, 90, 40))

    def test_zero_slide_dimensions_triggers_exception(self):
        """Test that division by zero in slide dimensions triggers exception handler fallback."""
        shape = Mock()
        shape.left = 100
        shape.top = 100
        shape.width = 100
        shape.height = 100

        slide_width = 0
        slide_height = 0

        left, top, width, height = get_shape_position(shape, slide_width, slide_height)

        self.assertEqual((left, top, width, height), (5, 5, 90, 40))


if __name__ == "__main__":
    unittest.main()
