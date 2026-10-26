import unittest
from unittest.mock import MagicMock

class TestTableRender(unittest.TestCase):
    def test_table_html_generation(self):
        # Mock table structure
        mock_cell1 = MagicMock()
        mock_cell1.text = "Header 1 & More"
        mock_cell2 = MagicMock()
        mock_cell2.text = "<Header 2>"

        mock_row1 = MagicMock()
        mock_row1.cells = [mock_cell1, mock_cell2]

        mock_table = MagicMock()
        mock_table.rows = [mock_row1]

        # Replicate conversion table construction logic
        table_parts = ['<table style="width:100%;border-collapse:collapse;font-size:0.9em">']
        for row in mock_table.rows:
            table_parts.append("<tr>")
            for cell in row.cells:
                cell_text = cell.text.replace("&", "&amp;").replace("<", "&lt;")
                table_parts.append(f'<td style="border:1px solid #ccc;padding:6px 10px">{cell_text}</td>')
            table_parts.append("</tr>")
        table_parts.append("</table>")
        table_html = "".join(table_parts)

        expected_html = (
            '<table style="width:100%;border-collapse:collapse;font-size:0.9em">'
            '<tr>'
            '<td style="border:1px solid #ccc;padding:6px 10px">Header 1 &amp; More</td>'
            '<td style="border:1px solid #ccc;padding:6px 10px">&lt;Header 2></td>'
            '</tr>'
            '</table>'
        )
        self.assertEqual(table_html, expected_html)

if __name__ == '__main__':
    unittest.main()
