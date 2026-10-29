import html
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util
import sys

# Import convert-pdf.py module dynamically since filename contains hyphen
spec_pdf = importlib.util.spec_from_file_location(
    "convert_pdf",
    Path(__file__).parent / "convert-pdf.py"
)
convert_pdf = importlib.util.module_from_spec(spec_pdf)
spec_pdf.loader.exec_module(convert_pdf)

# Import convert-pptx.py module dynamically
spec_pptx = importlib.util.spec_from_file_location(
    "convert_pptx",
    Path(__file__).parent / "convert-pptx.py"
)
convert_pptx = importlib.util.module_from_spec(spec_pptx)
spec_pptx.loader.exec_module(convert_pptx)


class TestXSSFix(unittest.TestCase):
    @patch("builtins.open", unittest.mock.mock_open(read_data=b"fake_image_data"))
    @patch("os.path.getsize", return_value=1024)
    @patch("glob.glob", return_value=["/tmp/page-1.png"])
    @patch("subprocess.run")
    @patch("pathlib.Path.exists", return_value=True)
    @patch("pathlib.Path.write_text")
    def test_convert_pdf_title_xss_escaped(self, mock_write_text, mock_exists, mock_subproc, mock_glob, mock_getsize):
        mock_subproc.return_value = MagicMock(returncode=0, stdout="Pages: 1\n", stderr="")

        pdf_filename = 'test_<img src=x onerror=alert("XSS")>_file.pdf'
        convert_pdf.convert(pdf_filename, output_path="output.html", external_assets=False)

        mock_write_text.assert_called_once()
        written_html = mock_write_text.call_args[0][0]

        expected_escaped_title = "<title>test &lt;img src=x onerror=alert(&quot;XSS&quot;)&gt; file</title>"
        self.assertIn(expected_escaped_title, written_html)
        self.assertNotIn('<title>test <img src=x onerror=alert("XSS")> file</title>', written_html)

    @patch("os.path.getsize", return_value=1024)
    @patch("pathlib.Path.write_text")
    @patch.object(convert_pptx, "get_slide_background", return_value="")
    @patch.object(convert_pptx, "get_shape_position", return_value=(0.0, 0.0, 100.0, 100.0))
    @patch.object(convert_pptx, "extract_image_data", return_value=(None, None))
    @patch.object(convert_pptx, "get_shape_fill", return_value=None)
    def test_convert_pptx_title_xss_escaped(self, mock_fill, mock_extract_img, mock_pos, mock_bg, mock_write_text, mock_getsize):
        mock_prs = MagicMock()
        mock_slide = MagicMock()
        mock_title_shape = MagicMock()
        mock_title_shape.text = "<script>alert('XSS')</script>"
        mock_title_shape.shape_type = 1
        mock_title_shape.has_table = False
        mock_title_shape.has_text_frame = False
        mock_slide.shapes = [mock_title_shape]
        mock_prs.slides = [mock_slide]
        mock_prs.slide_width = 1000
        mock_prs.slide_height = 750

        mock_pptx_module = MagicMock()
        mock_pptx_module.Presentation.return_value = mock_prs

        with patch.dict(sys.modules, {"pptx": mock_pptx_module}), \
             patch.object(convert_pptx, "_ensure_pptx", return_value=True):
            convert_pptx.convert("test.pptx", output_path="output.html", external_assets=False)

        mock_write_text.assert_called_once()
        written_html = mock_write_text.call_args[0][0]

        expected_escaped_title = "<title>&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;</title>"
        self.assertIn(expected_escaped_title, written_html)
        self.assertNotIn("<title><script>alert('XSS')</script></title>", written_html)


if __name__ == "__main__":
    unittest.main()
