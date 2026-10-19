import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Dynamically import convert-pdf.py since it has a hyphen in its name
script_path = Path(__file__).parent / "convert-pdf.py"
spec = importlib.util.spec_from_file_location("convert_pdf", script_path)
convert_pdf = importlib.util.module_from_spec(spec)
sys.modules["convert_pdf"] = convert_pdf
spec.loader.exec_module(convert_pdf)


class TestConvertPDF(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_page_count_success(self, mock_run):
        mock_run.return_value = MagicMock(
            stdout="Title: Test\nPages: 12\nPage size: A4",
            stderr="",
            returncode=0
        )
        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertEqual(count, 12)
        mock_run.assert_called_once_with(["pdfinfo", "dummy.pdf"], capture_output=True, text=True)

    @patch("subprocess.run")
    def test_get_page_count_failure(self, mock_run):
        mock_run.side_effect = FileNotFoundError("pdfinfo not found")
        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertIsNone(count)

    @patch("sys.stdout", new_callable=io.StringIO)
    def test_convert_file_not_found(self, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_pdf = os.path.join(tmpdir, "missing.pdf")
            with self.assertRaises(SystemExit) as cm:
                convert_pdf.convert(non_existent_pdf)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("not found", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_convert_missing_pdftoppm(self, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "test.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")

            # First subprocess.run call is `which pdftoppm`
            mock_run.return_value = MagicMock(returncode=1)

            with self.assertRaises(SystemExit) as cm:
                convert_pdf.convert(dummy_pdf)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("pdftoppm not found", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_convert_pdftoppm_error(self, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "test.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")

            def side_effect(cmd, **kwargs):
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "pdfinfo":
                    return MagicMock(stdout="Pages: 1\n", returncode=0)
                if cmd[0] == "pdftoppm":
                    return MagicMock(returncode=1, stderr="Error converting PDF render")
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            with self.assertRaises(SystemExit) as cm:
                convert_pdf.convert(dummy_pdf)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("Error converting PDF: Error converting PDF render", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_convert_no_pages_rendered(self, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "test.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")

            def side_effect(cmd, **kwargs):
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "pdfinfo":
                    return MagicMock(stdout="Pages: 1\n", returncode=0)
                if cmd[0] == "pdftoppm":
                    # pdftoppm succeeds but doesn't write any png files
                    return MagicMock(returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            with self.assertRaises(SystemExit) as cm:
                convert_pdf.convert(dummy_pdf)
            self.assertEqual(cm.exception.code, 1)
            self.assertIn("No pages rendered from PDF", mock_stdout.getvalue())

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_convert_inline_assets_success(self, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "my-presentation.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")
            output_html = os.path.join(tmpdir, "my-presentation.html")

            def side_effect(cmd, **kwargs):
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "pdfinfo":
                    return MagicMock(stdout="Pages: 2\n", returncode=0)
                if cmd[0] == "pdftoppm":
                    prefix = cmd[-1]
                    Path(f"{prefix}-1.png").write_bytes(b"PNGDATA1")
                    Path(f"{prefix}-2.png").write_bytes(b"PNGDATA2")
                    return MagicMock(returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            convert_pdf.convert(dummy_pdf, output_path=output_html, external_assets=False)

            self.assertTrue(Path(output_html).exists())
            content = Path(output_html).read_text(encoding="utf-8")
            self.assertIn("<title>my presentation</title>", content)
            self.assertIn("data:image/png;base64,", content)
            self.assertIn('<img src="data:image/png;base64,', content)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    def test_convert_external_assets_success(self, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "deck.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")
            output_html = os.path.join(tmpdir, "deck.html")

            def side_effect(cmd, **kwargs):
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "pdfinfo":
                    return MagicMock(stdout="Pages: 2\n", returncode=0)
                if cmd[0] == "pdftoppm":
                    prefix = cmd[-1]
                    Path(f"{prefix}-1.png").write_bytes(b"PNGDATA1")
                    Path(f"{prefix}-2.png").write_bytes(b"PNGDATA2")
                    return MagicMock(returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            convert_pdf.convert(dummy_pdf, output_path=output_html, external_assets=True)

            self.assertTrue(Path(output_html).exists())
            content = Path(output_html).read_text(encoding="utf-8")
            self.assertIn('src="assets/img-001.png"', content)
            self.assertIn('src="assets/img-002.png"', content)

            assets_dir = Path(tmpdir) / "assets"
            self.assertTrue((assets_dir / "img-001.png").exists())
            self.assertEqual((assets_dir / "img-001.png").read_bytes(), b"PNGDATA1")
            self.assertTrue((assets_dir / "img-002.png").exists())
            self.assertEqual((assets_dir / "img-002.png").read_bytes(), b"PNGDATA2")

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("subprocess.run")
    @patch("os.path.getsize")
    def test_convert_auto_detect_external_assets_large_file(self, mock_getsize, mock_run, mock_stdout):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy_pdf = os.path.join(tmpdir, "large.pdf")
            Path(dummy_pdf).write_bytes(b"%PDF-1.4 dummy content")
            output_html = os.path.join(tmpdir, "large.html")

            # Pretend PDF is 200MB (triggers both warning > 150MB and external_assets > 20MB)
            def getsize_side_effect(p):
                if str(p) == str(Path(dummy_pdf).resolve()):
                    return 200 * 1024 * 1024
                return len(Path(p).read_bytes())

            mock_getsize.side_effect = getsize_side_effect

            def side_effect(cmd, **kwargs):
                if cmd[0] == "which":
                    return MagicMock(returncode=0)
                if cmd[0] == "pdfinfo":
                    return MagicMock(stdout="Pages: 10\n", returncode=0)
                if cmd[0] == "pdftoppm":
                    prefix = cmd[-1]
                    Path(f"{prefix}-1.png").write_bytes(b"PNGDATA1")
                    return MagicMock(returncode=0)
                return MagicMock(returncode=0)

            mock_run.side_effect = side_effect

            convert_pdf.convert(dummy_pdf, output_path=output_html, external_assets=None)

            content = Path(output_html).read_text(encoding="utf-8")
            self.assertIn('src="assets/img-001.png"', content)
            self.assertIn("WARNING: PDF is 200MB", mock_stdout.getvalue())
            self.assertIn("Auto-enabling external assets mode", mock_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
