import html
import unittest

class TestConvertPptxTitleEscaping(unittest.TestCase):
    def test_title_escaping(self):
        unsafe_title = "Test <script>alert('xss')</script> & Presentation"
        escaped_title = html.escape(unsafe_title)
        self.assertEqual(
            escaped_title,
            "Test &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt; &amp; Presentation"
        )
        self.assertNotIn("<script>", escaped_title)

if __name__ == "__main__":
    unittest.main()
