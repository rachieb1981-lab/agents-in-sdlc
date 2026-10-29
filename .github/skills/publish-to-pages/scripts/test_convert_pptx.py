import importlib.util
import os
import unittest

# Dynamic import because convert-pptx.py contains hyphens
script_path = os.path.join(os.path.dirname(__file__), "convert-pptx.py")
spec = importlib.util.spec_from_file_location("convert_pptx", script_path)
convert_pptx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pptx)


class TestRgbToHex(unittest.TestCase):
    def test_none_input(self):
        """Test that None input returns None."""
        self.assertIsNone(convert_pptx.rgb_to_hex(None))

    def test_valid_rgb_color(self):
        """Test valid RGB string/color values format properly with leading #."""
        self.assertEqual(convert_pptx.rgb_to_hex("FF0000"), "#FF0000")
        self.assertEqual(convert_pptx.rgb_to_hex("123456"), "#123456")

    def test_exception_handling(self):
        """Test that objects raising exceptions on string formatting return None."""
        class FaultyRGB:
            def __str__(self):
                raise ValueError("String conversion error")

        self.assertIsNone(convert_pptx.rgb_to_hex(FaultyRGB()))


if __name__ == "__main__":
    unittest.main()
