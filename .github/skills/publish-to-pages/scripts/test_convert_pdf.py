import unittest
from unittest.mock import patch, MagicMock, mock_open
import sys
import os
from pathlib import Path

# Add script directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

import importlib
convert_pdf = importlib.import_module("convert-pdf")


class TestConvertPdfSecurity(unittest.TestCase):

    @patch("subprocess.run")
    def test_get_page_count_uses_double_dash(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Pages: 10\n", returncode=0)

        # Test with a normal path
        count = convert_pdf.get_page_count("test.pdf")
        self.assertEqual(count, 10)
        mock_run.assert_called_with(["pdfinfo", "--", "test.pdf"], capture_output=True, text=True)

        # Test with a path that looks like a CLI flag
        count_flag = convert_pdf.get_page_count("-v")
        self.assertEqual(count_flag, 10)
        mock_run.assert_called_with(["pdfinfo", "--", "-v"], capture_output=True, text=True)

    @patch("subprocess.run")
    @patch("os.path.getsize")
    @patch("tempfile.TemporaryDirectory")
    @patch("glob.glob")
    def test_convert_uses_double_dash_for_pdftoppm(self, mock_glob, mock_tempdir, mock_getsize, mock_run):
        mock_getsize.return_value = 1024 * 1024  # 1MB
        mock_tempdir.return_value.__enter__.return_value = "/tmp/dummy"
        mock_glob.return_value = ["/tmp/dummy/page-1.png"]

        # mock subprocess.run calls
        def fake_run(cmd, **kwargs):
            res = MagicMock()
            res.returncode = 0
            res.stdout = "Pages: 5\n"
            return res

        mock_run.side_effect = fake_run

        m_open = mock_open(read_data=b"fake image data")

        with patch.object(Path, "exists", return_value=True), \
             patch.object(Path, "write_text") as mock_write_text, \
             patch("builtins.open", m_open):

            convert_pdf.convert("-filename_starting_with_dash.pdf")

            # Check that pdftoppm call included '--'
            pdftoppm_calls = [
                call for call in mock_run.call_args_list
                if call[0][0][0] == "pdftoppm"
            ]
            self.assertTrue(len(pdftoppm_calls) > 0)
            args = pdftoppm_calls[0][0][0]
            self.assertIn("--", args)
            # Ensure '--' comes immediately before pdf_path argument
            pdf_path_arg = str(Path("-filename_starting_with_dash.pdf").resolve())
            dash_idx = args.index("--")
            self.assertEqual(args[dash_idx + 1], pdf_path_arg)


if __name__ == "__main__":
    unittest.main()
