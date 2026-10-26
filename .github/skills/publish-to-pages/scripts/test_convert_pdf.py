import base64
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Dynamically import convert-pdf.py since it contains hyphens in filename
script_path = Path(__file__).parent / "convert-pdf.py"
spec = importlib.util.spec_from_file_location("convert_pdf", script_path)
convert_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pdf)


class TestConvertPdf(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_page_count_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Title: Test\nPages: 12\nEncrypted: no",
            stderr="",
            returncode=0
        )
        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertEqual(count, 12)

    @patch("subprocess.run", side_effect=Exception("Failed"))
    def test_get_page_count_failure(self, mock_run):
        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertIsNone(count)

    @patch("subprocess.run")
    def test_check_pdftoppm_installed_success(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        convert_pdf.check_pdftoppm_installed()

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_check_pdftoppm_installed_missing(self, mock_run, mock_stdout):
        mock_run.return_value = MagicMock(returncode=1)
        with self.assertRaises(SystemExit) as cm:
            convert_pdf.check_pdftoppm_installed()
        self.assertEqual(cm.exception.code, 1)

    @patch("glob.glob")
    @patch("subprocess.run")
    def test_render_pdf_to_images_success(self, mock_run, mock_glob):
        mock_run.return_value = MagicMock(returncode=0)
        mock_glob.return_value = ["/tmp/page-02.png", "/tmp/page-01.png"]

        pages = convert_pdf.render_pdf_to_images("test.pdf", "/tmp", dpi=150)
        self.assertEqual(pages, ["/tmp/page-01.png", "/tmp/page-02.png"])
        mock_run.assert_called_once_with(
            ["pdftoppm", "-png", "-r", "150", "test.pdf", os.path.join("/tmp", "page")],
            capture_output=True, text=True
        )

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_render_pdf_to_images_command_error(self, mock_run, mock_stdout):
        mock_run.return_value = MagicMock(returncode=1, stderr="pdftoppm failed")
        with self.assertRaises(SystemExit) as cm:
            convert_pdf.render_pdf_to_images("test.pdf", "/tmp")
        self.assertEqual(cm.exception.code, 1)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("glob.glob", return_value=[])
    @patch("subprocess.run")
    def test_render_pdf_to_images_no_pages(self, mock_run, mock_glob, mock_stdout):
        mock_run.return_value = MagicMock(returncode=0)
        with self.assertRaises(SystemExit) as cm:
            convert_pdf.render_pdf_to_images("test.pdf", "/tmp")
        self.assertEqual(cm.exception.code, 1)

    def test_build_slide_sections_inline(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, "p1.png")
            Path(p1).write_bytes(b"image_bytes_1")

            sections = convert_pdf.build_slide_sections([p1], external_assets=False)
            self.assertEqual(len(sections), 1)

            b64_expected = base64.b64encode(b"image_bytes_1").decode()
            self.assertIn(f'src="data:image/png;base64,{b64_expected}"', sections[0])
            self.assertIn('alt="Page 1"', sections[0])

    def test_build_slide_sections_external(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, "p1.png")
            Path(p1).write_bytes(b"image_bytes_1")

            assets_dir = Path(tmpdir) / "assets"
            assets_dir.mkdir()

            sections = convert_pdf.build_slide_sections([p1], external_assets=True, assets_dir=assets_dir)
            self.assertEqual(len(sections), 1)
            self.assertIn('src="assets/img-001.png"', sections[0])
            self.assertTrue((assets_dir / "img-001.png").exists())
            self.assertEqual((assets_dir / "img-001.png").read_bytes(), b"image_bytes_1")

    def test_build_slide_sections_external_missing_assets_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            p1 = os.path.join(tmpdir, "p1.png")
            Path(p1).write_bytes(b"image_bytes_1")
            with self.assertRaises(ValueError):
                convert_pdf.build_slide_sections([p1], external_assets=True, assets_dir=None)

    def test_generate_presentation_html(self):
        slides = ['<section class="slide">Slide 1</section>', '<section class="slide">Slide 2</section>']
        html = convert_pdf.generate_presentation_html("My Presentation", slides)
        self.assertIn("<title>My Presentation</title>", html)
        self.assertIn('<section class="slide">Slide 1</section>', html)
        self.assertIn('<section class="slide">Slide 2</section>', html)
        self.assertIn("const slides = document.querySelectorAll('.slide');", html)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_convert_end_to_end(self, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "sample-doc.pdf")
            out_path = os.path.join(tmpdir, "sample-doc.html")
            Path(pdf_path).write_bytes(b"dummy pdf content")

            dummy_png = os.path.join(tmpdir, "page-1.png")
            Path(dummy_png).write_bytes(b"png data")

            with patch.object(convert_pdf, "check_pdftoppm_installed"), \
                 patch.object(convert_pdf, "get_page_count", return_value=5), \
                 patch.object(convert_pdf, "render_pdf_to_images", return_value=[dummy_png]):
                convert_pdf.convert(pdf_path, output_path=out_path, dpi=150, external_assets=False)

            self.assertTrue(os.path.exists(out_path))
            html_content = Path(out_path).read_text(encoding="utf-8")
            self.assertIn("<title>sample doc</title>", html_content)


if __name__ == "__main__":
    unittest.main()
