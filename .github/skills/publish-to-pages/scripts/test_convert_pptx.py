import unittest
import importlib
import tempfile
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

convert_pptx = importlib.import_module("convert-pptx")

class TestConvertPptx(unittest.TestCase):
    @patch.object(convert_pptx, "_ensure_pptx")
    @patch("os.path.getsize")
    def test_convert_text_and_table_shapes(self, mock_getsize, mock_ensure):
        mock_getsize.return_value = 1024 * 1024 # 1 MB

        with patch.object(convert_pptx, "count_images", return_value=0), \
             patch("pptx.Presentation") as mock_presentation_cls:
            mock_prs = MagicMock()
            mock_presentation_cls.return_value = mock_prs
            mock_prs.slide_width = 1000
            mock_prs.slide_height = 500

            mock_slide = MagicMock()
            mock_prs.slides = [mock_slide]

            # Text shape
            mock_shape_text = MagicMock()
            mock_shape_text.top = 10
            mock_shape_text.left = 10
            mock_shape_text.width = 100
            mock_shape_text.height = 50
            mock_shape_text.shape_type = 1
            mock_shape_text.has_table = False
            mock_shape_text.has_text_frame = True
            mock_para = MagicMock()
            mock_run = MagicMock()
            mock_run.text = "Sample Title"
            mock_run.font.bold = True
            mock_run.font.italic = False
            mock_run.font.underline = False
            mock_run.font.size = None
            mock_run.font.color = None
            mock_run.font.name = None
            mock_para.runs = [mock_run]
            mock_shape_text.text_frame.paragraphs = [mock_para]
            mock_shape_text.text = "Sample Title"
            del mock_shape_text.image

            # Table shape
            mock_shape_table = MagicMock()
            mock_shape_table.top = 100
            mock_shape_table.left = 100
            mock_shape_table.width = 400
            mock_shape_table.height = 200
            mock_shape_table.shape_type = 19
            mock_shape_table.has_table = True
            mock_shape_table.has_text_frame = False
            cell1 = MagicMock()
            cell1.text = "Header & Text"
            row1 = MagicMock()
            row1.cells = [cell1]
            mock_shape_table.table.rows = [row1]
            del mock_shape_table.image

            mock_slide.shapes = [mock_shape_text, mock_shape_table]

            with tempfile.TemporaryDirectory() as tmpdir:
                input_pptx = os.path.join(tmpdir, "test.pptx")
                output_html = os.path.join(tmpdir, "test.html")
                Path(input_pptx).touch()

                convert_pptx.convert(input_pptx, output_html, external_assets=False)

                self.assertTrue(os.path.exists(output_html))
                content = Path(output_html).read_text()
                self.assertIn("Sample Title", content)
                self.assertIn("Header &amp; Text", content)
                self.assertIn("<table", content)

    @patch.object(convert_pptx, "_ensure_pptx")
    @patch("os.path.getsize")
    def test_convert_image_shapes_inline_and_external(self, mock_getsize, mock_ensure):
        mock_getsize.return_value = 1024 * 1024 # 1 MB

        with patch.object(convert_pptx, "count_images", return_value=1), \
             patch("pptx.Presentation") as mock_presentation_cls:
            mock_prs = MagicMock()
            mock_presentation_cls.return_value = mock_prs
            mock_prs.slide_width = 1000
            mock_prs.slide_height = 500

            mock_slide = MagicMock()
            mock_prs.slides = [mock_slide]

            mock_shape_img = MagicMock()
            mock_shape_img.top = 20
            mock_shape_img.left = 20
            mock_shape_img.width = 200
            mock_shape_img.height = 200
            mock_shape_img.shape_type = 13
            mock_shape_img.has_table = False
            mock_shape_img.has_text_frame = False
            mock_shape_img.image.blob = b"fake_image_bytes"
            mock_shape_img.image.content_type = "image/png"

            mock_slide.shapes = [mock_shape_img]

            with tempfile.TemporaryDirectory() as tmpdir:
                input_pptx = os.path.join(tmpdir, "test.pptx")

                # Test Inline Mode
                output_html1 = os.path.join(tmpdir, "inline.html")
                Path(input_pptx).touch()
                convert_pptx.convert(input_pptx, output_html1, external_assets=False)
                content1 = Path(output_html1).read_text()
                self.assertIn("data:image/png;base64,", content1)

                # Test External Assets Mode
                output_html2 = os.path.join(tmpdir, "external.html")
                convert_pptx.convert(input_pptx, output_html2, external_assets=True)
                content2 = Path(output_html2).read_text()
                self.assertIn("src=\"assets/img-001.png\"", content2)
                asset_file = Path(tmpdir) / "assets" / "img-001.png"
                self.assertTrue(asset_file.exists())
                self.assertEqual(asset_file.read_bytes(), b"fake_image_bytes")

if __name__ == "__main__":
    unittest.main()
