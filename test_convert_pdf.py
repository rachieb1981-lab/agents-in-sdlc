import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import importlib.util

# Import convert-pdf module dynamically due to hyphen in path
script_path = Path(__file__).parent / ".github" / "skills" / "publish-to-pages" / "scripts" / "convert-pdf.py"
spec = importlib.util.spec_from_file_location("convert_pdf", script_path)
convert_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pdf)


class TestConvertPdfSecurity(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_page_count_uses_double_dash(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Pages: 5\n", returncode=0)
        pdf_path = "-h"

        count = convert_pdf.get_page_count(pdf_path)

        self.assertEqual(count, 5)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "pdfinfo")
        self.assertEqual(cmd[1], "--")
        self.assertEqual(cmd[2], pdf_path)

    @patch("subprocess.run")
    def test_convert_pdftoppm_uses_double_dash(self, mock_run):
        # First call is `which pdftoppm`, second is `pdftoppm` command
        def subprocess_side_effect(cmd, **kwargs):
            if cmd[0] == "which":
                return MagicMock(returncode=0)
            elif cmd[0] == "pdfinfo":
                return MagicMock(stdout="Pages: 1\n", returncode=0)
            elif cmd[0] == "pdftoppm":
                return MagicMock(returncode=0, stderr="")
            return MagicMock(returncode=1)

        mock_run.side_effect = subprocess_side_effect

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_file = Path(tmpdir) / "-h.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 dummy content")
            output_file = Path(tmpdir) / "output.html"

            # Patch glob to return a dummy rendered page image
            dummy_png = Path(tmpdir) / "page-1.png"
            dummy_png.write_bytes(b"dummy png content")

            with patch("glob.glob", return_value=[str(dummy_png)]):
                convert_pdf.convert(str(pdf_file), str(output_file), dpi=150)

            # Inspect calls to subprocess.run
            pdftoppm_calls = [
                call for call in mock_run.call_args_list if call[0][0][0] == "pdftoppm"
            ]
            self.assertEqual(len(pdftoppm_calls), 1)
            pdftoppm_cmd = pdftoppm_calls[0][0][0]

            # Verify '--' argument separator is present right before pdf_path argument
            self.assertIn("--", pdftoppm_cmd)
            dash_index = pdftoppm_cmd.index("--")
            self.assertEqual(pdftoppm_cmd[dash_index + 1], str(pdf_file.resolve()))


if __name__ == "__main__":
    unittest.main()
