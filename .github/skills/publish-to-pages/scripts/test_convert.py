import html
import unittest
from pathlib import Path

class TestPDFTitleEscaping(unittest.TestCase):
    def test_title_escaping(self):
        filename = "<img src=x onerror=alert(1)>_test-file"
        stem = Path(filename).stem.replace("-", " ").replace("_", " ")
        title = html.escape(stem)
        self.assertNotIn("<img", title)
        self.assertEqual(title, "&lt;img src=x onerror=alert(1)&gt; test file")

if __name__ == "__main__":
    unittest.main()
