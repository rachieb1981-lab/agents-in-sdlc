import importlib.util
from unittest.mock import MagicMock

# Dynamically import convert-pptx.py
spec = importlib.util.spec_from_file_location(
    "convert_pptx",
    ".github/skills/publish-to-pages/scripts/convert-pptx.py"
)
convert_pptx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(convert_pptx)

from pptx.enum.text import PP_ALIGN


def test_get_alignment_center():
    paragraph = MagicMock()
    paragraph.alignment = PP_ALIGN.CENTER
    assert convert_pptx.get_alignment(paragraph) == "center"


def test_get_alignment_right():
    paragraph = MagicMock()
    paragraph.alignment = PP_ALIGN.RIGHT
    assert convert_pptx.get_alignment(paragraph) == "right"


def test_get_alignment_justify():
    paragraph = MagicMock()
    paragraph.alignment = PP_ALIGN.JUSTIFY
    assert convert_pptx.get_alignment(paragraph) == "justify"


def test_get_alignment_left_default():
    paragraph = MagicMock()
    paragraph.alignment = PP_ALIGN.LEFT
    assert convert_pptx.get_alignment(paragraph) == "left"


def test_get_alignment_none():
    paragraph = MagicMock()
    paragraph.alignment = None
    assert convert_pptx.get_alignment(paragraph) == "left"


def test_get_alignment_exception():
    paragraph = MagicMock()
    type(paragraph).alignment = property(fget=MagicMock(side_effect=AttributeError("No alignment")))
    assert convert_pptx.get_alignment(paragraph) == "left"
