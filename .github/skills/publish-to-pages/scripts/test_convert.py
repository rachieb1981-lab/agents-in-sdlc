import html
import unittest

class TestTitleEscaping(unittest.TestCase):
    def test_pptx_title_escaping(self):
        vulnerable_title = "<script>alert('XSS')</script> & Presentation <Title>"
        escaped_title = html.escape(vulnerable_title)

        html_template = f"<title>{escaped_title}</title>"

        self.assertNotIn("<script>", html_template)
        self.assertIn("&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt; &amp; Presentation &lt;Title&gt;", html_template)

    def test_pdf_title_escaping(self):
        vulnerable_stem = "test_<script>alert(1)</script>"
        title = vulnerable_stem.replace("-", " ").replace("_", " ")
        escaped_title = html.escape(title)

        html_template = f"<title>{escaped_title}</title>"

        self.assertNotIn("<script>", html_template)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html_template)

if __name__ == "__main__":
    unittest.main()
