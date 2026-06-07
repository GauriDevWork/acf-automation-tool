# parser/loader.py
from docx import Document
from docx.oxml.ns import qn


def load_document(file_path):
    """
    Opens a .docx file and returns the Document object.
    Raises FileNotFoundError if the path is wrong.
    """
    try:
        doc = Document(file_path)
        print(f"[OK] Loaded: {file_path}")
        print(f"[OK] Total paragraphs: {len(doc.paragraphs)}")
        return doc
    except FileNotFoundError:
        raise FileNotFoundError(f"[ERROR] File not found: {file_path}")


def extract_raw_structure(doc):
    """
    Reads every paragraph AND table in the document in order.
    Returns a list of dicts: {style, text, is_table_row, table_cells}

    For regular paragraphs:
        {style, text, is_table_row: False, table_cells: None}

    For table rows:
        {style: 'TableRow', text: '', is_table_row: True,
         table_cells: ['150', 'Projects Delivered', '+', 'briefcase']}

    Skips completely empty paragraphs and header rows.
    """
    from docx.text.paragraph import Paragraph as DocxParagraph
    from docx.table import Table as DocxTable

    raw = []

    # Iterate body elements in document order — includes both paragraphs and tables
    for child in doc.element.body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            # Regular paragraph
            para  = DocxParagraph(child, doc)
            text  = para.text.strip()
            style = para.style.name if para.style else "Normal"
            if text:
                raw.append({
                    "style":       style,
                    "text":        text,
                    "is_table_row": False,
                    "table_cells": None,
                })

        elif tag == "tbl":
            # Table — extract each row as a table_row item
            table = DocxTable(child, doc)
            for i, row in enumerate(table.rows):
                cells = [cell.text.strip() for cell in row.cells]
                # Skip empty rows and deduplicate merged cells
                cells = list(dict.fromkeys(cells))  # remove duplicates from merged cells
                cells = [c for c in cells if c]     # remove empty cells

                if not cells:
                    continue

                # Skip header row — if all cells look like column headers
                # (no numbers in the row) skip it
                has_number = any(c.replace("+", "").replace("%", "").isdigit()
                                 or c[:2].isdigit() for c in cells)
                if i == 0 and not has_number:
                    continue  # Skip header row

                raw.append({
                    "style":        "TableRow",
                    "text":         " | ".join(cells),
                    "is_table_row": True,
                    "table_cells":  cells,
                })

    return raw