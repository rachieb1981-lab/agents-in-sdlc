import importlib
import pathlib
import sys
import unittest
from unittest.mock import MagicMock

# Load convert-pptx module dynamically due to hyphen in filename
SCRIPT_DIR = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR))
convert_pptx = importlib.import_module("convert-pptx")


class TestRgbToHex(unittest.TestCase):
    def test_rgb_to_hex_none(self):
        self.assertIsNone(convert_pptx.rgb_to_hex(None))

    def test_rgb_to_hex_valid_string_or_color(self):
        self.assertEqual(convert_pptx.rgb_to_hex("FF0000"), "#FF0000")
        self.assertEqual(convert_pptx.rgb_to_hex("00FF00"), "#00FF00")

    def test_rgb_to_hex_exception(self):
        class BadObject:
            def __str__(self):
                raise ValueError("Format error")

        self.assertIsNone(convert_pptx.rgb_to_hex(BadObject()))


class TestGetTextStyle(unittest.TestCase):
    def test_get_text_style_all_styles(self):
        run = MagicMock()
        run.font.bold = True
        run.font.italic = True
        run.font.underline = True
        run.font.size.pt = 14
        run.font.color.rgb = "FF0000"
        run.font.name = "Arial"

        style = convert_pptx.get_text_style(run)
        expected = (
            "font-weight:bold;"
            "font-style:italic;"
            "text-decoration:underline;"
            "font-size:14pt;"
            "color:#FF0000;"
            "font-family:'Arial',sans-serif"
        )
        self.assertEqual(style, expected)

    def test_get_text_style_no_styles(self):
        run = MagicMock()
        run.font.bold = False
        run.font.italic = False
        run.font.underline = False
        run.font.size = None
        run.font.color = None
        run.font.name = None

        style = convert_pptx.get_text_style(run)
        self.assertEqual(style, "")

    def test_get_text_style_exception(self):
        class BadRun:
            @property
            def font(self):
                raise AttributeError("No font")

        style = convert_pptx.get_text_style(BadRun())
        self.assertEqual(style, "")


class TestGetAlignment(unittest.TestCase):
    def test_get_alignment_enums(self):
        from pptx.enum.text import PP_ALIGN

        for align_enum, expected in [
            (PP_ALIGN.CENTER, "center"),
            (PP_ALIGN.RIGHT, "right"),
            (PP_ALIGN.JUSTIFY, "justify"),
            (PP_ALIGN.LEFT, "left"),
        ]:
            paragraph = MagicMock()
            paragraph.alignment = align_enum
            self.assertEqual(convert_pptx.get_alignment(paragraph), expected)

    def test_get_alignment_default_or_none(self):
        paragraph = MagicMock()
        paragraph.alignment = None
        self.assertEqual(convert_pptx.get_alignment(paragraph), "left")

    def test_get_alignment_exception(self):
        class BadParagraph:
            @property
            def alignment(self):
                raise Exception("Error")

        self.assertEqual(convert_pptx.get_alignment(BadParagraph()), "left")


class TestGetShapePosition(unittest.TestCase):
    def test_get_shape_position_normal(self):
        shape = MagicMock()
        shape.left = 100
        shape.top = 50
        shape.width = 500
        shape.height = 250

        left, top, width, height = convert_pptx.get_shape_position(shape, 1000, 500)
        self.assertEqual((left, top, width, height), (10.0, 10.0, 50.0, 50.0))

    def test_get_shape_position_falsy_values(self):
        shape = MagicMock()
        shape.left = 0
        shape.top = None
        shape.width = 0
        shape.height = None

        left, top, width, height = convert_pptx.get_shape_position(shape, 1000, 500)
        self.assertEqual((left, top, width, height), (0, 0, 50, 30))

    def test_get_shape_position_exception(self):
        shape = MagicMock()
        shape.left = 100
        # Division by zero causes exception
        left, top, width, height = convert_pptx.get_shape_position(shape, 0, 0)
        self.assertEqual((left, top, width, height), (5, 5, 90, 40))


class TestGetSlideBackground(unittest.TestCase):
    def test_get_slide_background_solid_fill_on_slide(self):
        slide = MagicMock()
        bg_el = MagicMock()
        slide.background._element = bg_el

        sf_node = MagicMock()
        clr_node = MagicMock()
        clr_node.get.side_effect = lambda k: "FF1122" if k == "val" else None
        sf_node.find.return_value = clr_node
        bg_el.iter.return_value = [sf_node]

        prs = MagicMock()
        result = convert_pptx.get_slide_background(slide, prs)
        self.assertEqual(result, "background-color:#FF1122")

    def test_get_slide_background_fallback_default(self):
        class BadSlide:
            @property
            def background(self):
                raise Exception("No background")

            @property
            def slide_layout(self):
                class BadLayout:
                    @property
                    def background(self):
                        raise Exception("No layout background")
                return BadLayout()

        prs = MagicMock()
        result = convert_pptx.get_slide_background(BadSlide(), prs)
        self.assertEqual(result, "background-color:#ffffff")


class TestGetShapeFill(unittest.TestCase):
    def test_get_shape_fill_valid(self):
        shape = MagicMock()
        sp_pr = MagicMock()
        sf = MagicMock()
        clr = MagicMock()
        clr.get.side_effect = lambda k: "AABBCC" if k == "val" else None

        shape._element.find.return_value = sp_pr
        sp_pr.find.return_value = sf
        sf.find.return_value = clr

        self.assertEqual(convert_pptx.get_shape_fill(shape), "#AABBCC")

    def test_get_shape_fill_none_or_exception(self):
        shape = MagicMock()
        shape._element.find.return_value = None

        self.assertIsNone(convert_pptx.get_shape_fill(shape))


class TestRenderParagraph(unittest.TestCase):
    def test_render_paragraph_with_content(self):
        paragraph = MagicMock()
        paragraph.alignment = None

        run1 = MagicMock()
        run1.text = "Hello & Welcome"
        run1.font.bold = True
        run1.font.italic = False
        run1.font.underline = False
        run1.font.size = None
        run1.font.color = None
        run1.font.name = None

        run2 = MagicMock()
        run2.text = "<World>"
        run2.font.bold = False
        run2.font.italic = False
        run2.font.underline = False
        run2.font.size = None
        run2.font.color = None
        run2.font.name = None

        paragraph.runs = [run1, run2]

        rendered = convert_pptx.render_paragraph(paragraph)
        expected = '<p style="text-align:left;margin:0.3em 0;line-height:1.4"><span style="font-weight:bold">Hello &amp; Welcome</span>&lt;World&gt;</p>'
        self.assertEqual(rendered, expected)

    def test_render_paragraph_empty(self):
        paragraph = MagicMock()
        paragraph.runs = []
        self.assertEqual(convert_pptx.render_paragraph(paragraph), "")

        run_empty = MagicMock()
        run_empty.text = ""
        paragraph.runs = [run_empty]
        self.assertEqual(convert_pptx.render_paragraph(paragraph), "")


class TestExtractImageData(unittest.TestCase):
    def test_extract_image_data_success(self):
        shape = MagicMock()
        shape.image.blob = b"imagedata"
        shape.image.content_type = "image/png"

        blob, content_type = convert_pptx.extract_image_data(shape)
        self.assertEqual(blob, b"imagedata")
        self.assertEqual(content_type, "image/png")

    def test_extract_image_data_exception(self):
        class BadShape:
            @property
            def image(self):
                raise AttributeError("No image")

        blob, content_type = convert_pptx.extract_image_data(BadShape())
        self.assertIsNone(blob)
        self.assertIsNone(content_type)


class TestCountImages(unittest.TestCase):
    def test_count_images(self):
        prs = MagicMock()

        slide1 = MagicMock()
        shape1 = MagicMock()
        shape1.shape_type = 13
        shape1.image = MagicMock()

        shape2 = MagicMock()
        shape2.shape_type = 1
        del shape2.image  # shape without image attribute

        slide1.shapes = [shape1, shape2]

        slide2 = MagicMock()
        shape3 = MagicMock()
        shape3.shape_type = 1
        shape3.image = MagicMock()  # has image attribute

        class CorruptImageShape:
            shape_type = 13

            @property
            def image(self):
                raise Exception("Corrupt image")

        shape4 = CorruptImageShape()

        slide2.shapes = [shape3, shape4]

        prs.slides = [slide1, slide2]

        count = convert_pptx.count_images(prs)
        self.assertEqual(count, 2)


if __name__ == "__main__":
    unittest.main()
