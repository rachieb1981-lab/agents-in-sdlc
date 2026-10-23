import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Dynamically import convert-pdf.py (since the filename contains a hyphen)
script_path = Path(__file__).parent / "convert-pdf.py"
spec = importlib.util.spec_from_file_location("convert_pdf", script_path)
convert_pdf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pdf)

get_page_count = convert_pdf.get_page_count


def test_get_page_count_success():
    """Test get_page_count correctly parses output from pdfinfo when Pages field is present."""
    mock_output = (
        "Title:          Sample Document\n"
        "Author:         John Doe\n"
        "Pages:          42\n"
        "Page size:      612 x 792 pts (letter)\n"
    )
    mock_result = MagicMock()
    mock_result.stdout = mock_output

    with patch("subprocess.run", return_value=mock_result) as mock_run:
        count = get_page_count("sample.pdf")
        assert count == 42
        mock_run.assert_called_once_with(["pdfinfo", "sample.pdf"], capture_output=True, text=True)


def test_get_page_count_with_extra_spaces():
    """Test get_page_count handles varying whitespace around page count."""
    mock_output = "Pages:   100   \n"
    mock_result = MagicMock()
    mock_result.stdout = mock_output

    with patch("subprocess.run", return_value=mock_result):
        assert get_page_count("sample.pdf") == 100


def test_get_page_count_missing_pages_header():
    """Test get_page_count returns None when Pages header is absent in pdfinfo output."""
    mock_output = "Title: Sample Document\nAuthor: Jane Doe\n"
    mock_result = MagicMock()
    mock_result.stdout = mock_output

    with patch("subprocess.run", return_value=mock_result):
        assert get_page_count("sample.pdf") is None


def test_get_page_count_invalid_int():
    """Test get_page_count returns None when page count value cannot be parsed as an integer."""
    mock_output = "Pages: invalid_number\n"
    mock_result = MagicMock()
    mock_result.stdout = mock_output

    with patch("subprocess.run", return_value=mock_result):
        assert get_page_count("sample.pdf") is None


def test_get_page_count_subprocess_exception():
    """Test get_page_count handles exceptions raised by subprocess.run gracefully."""
    with patch("subprocess.run", side_effect=FileNotFoundError("pdfinfo not found")):
        assert get_page_count("sample.pdf") is None
