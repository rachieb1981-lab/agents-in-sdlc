import importlib.util
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Dynamically import convert-pdf.py due to the hyphen in filename
script_path = Path(__file__).parent / "convert-pdf.py"
spec = importlib.util.spec_from_file_location("convert_pdf", script_path)
convert_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pdf)


class TestGetPageCount(unittest.TestCase):
    @patch("subprocess.run")
    def test_get_page_count_success(self, mock_run):
        mock_stdout = "Title: Test Document\nPages: 15\nPage size: 612 x 792 pts"
        mock_run.return_value = MagicMock(stdout=mock_stdout)

        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertEqual(count, 15)
        mock_run.assert_called_once_with(["pdfinfo", "dummy.pdf"], capture_output=True, text=True)

    @patch("subprocess.run")
    def test_get_page_count_no_pages_line(self, mock_run):
        mock_stdout = "Title: Test Document\nAuthor: Tester\n"
        mock_run.return_value = MagicMock(stdout=mock_stdout)

        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertIsNone(count)

    @patch("subprocess.run")
    def test_get_page_count_subprocess_exception(self, mock_run):
        mock_run.side_effect = FileNotFoundError("pdfinfo not found")

        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertIsNone(count)

    @patch("subprocess.run")
    def test_get_page_count_invalid_int(self, mock_run):
        mock_stdout = "Pages: invalid_number\n"
        mock_run.return_value = MagicMock(stdout=mock_stdout)

        count = convert_pdf.get_page_count("dummy.pdf")
        self.assertIsNone(count)


if __name__ == "__main__":
    unittest.main()
