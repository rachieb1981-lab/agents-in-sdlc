import base64
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent))
import importlib
convert_pdf = importlib.import_module("convert-pdf")


class TestConvertPdf(unittest.TestCase):

    @patch("subprocess.run")
    def test_convert_end_to_end_external_assets(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "which":
                return MagicMock(returncode=0)
            elif cmd[0] == "pdfinfo":
                return MagicMock(returncode=0, stdout="Pages: 3\n")
            elif cmd[0] == "pdftoppm":
                prefix = cmd[-1]
                for i in range(1, 4):
                    Path(f"{prefix}-{i:02d}.png").write_bytes(f"page-{i}".encode())
                return MagicMock(returncode=0, stderr="")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"dummy pdf content")
            out_html = tmp_path / "output.html"

            convert_pdf.convert(str(pdf_file), output_path=str(out_html), external_assets=True)

            self.assertTrue(out_html.exists())
            html_content = out_html.read_text()
            self.assertIn('<img src="assets/img-001.png" alt="Page 1">', html_content)
            self.assertIn('<img src="assets/img-002.png" alt="Page 2">', html_content)
            self.assertIn('<img src="assets/img-003.png" alt="Page 3">', html_content)

            assets_dir = tmp_path / "assets"
            self.assertTrue((assets_dir / "img-001.png").exists())
            self.assertTrue((assets_dir / "img-002.png").exists())
            self.assertTrue((assets_dir / "img-003.png").exists())

    @patch("subprocess.run")
    def test_convert_end_to_end_inline(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "which":
                return MagicMock(returncode=0)
            elif cmd[0] == "pdfinfo":
                return MagicMock(returncode=0, stdout="Pages: 2\n")
            elif cmd[0] == "pdftoppm":
                prefix = cmd[-1]
                for i in range(1, 3):
                    Path(f"{prefix}-{i:02d}.png").write_bytes(f"page-{i}".encode())
                return MagicMock(returncode=0, stderr="")
            return MagicMock(returncode=0)

        mock_run.side_effect = side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"dummy pdf content")
            out_html = tmp_path / "output.html"

            convert_pdf.convert(str(pdf_file), output_path=str(out_html), external_assets=False)

            self.assertTrue(out_html.exists())
            html_content = out_html.read_text()
            b64_1 = base64.b64encode(b"page-1").decode()
            b64_2 = base64.b64encode(b"page-2").decode()
            self.assertIn(f'src="data:image/png;base64,{b64_1}"', html_content)
            self.assertIn(f'src="data:image/png;base64,{b64_2}"', html_content)


if __name__ == "__main__":
    unittest.main()
