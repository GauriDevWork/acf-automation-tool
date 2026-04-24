# tests/test_loader.py
from parser.loader import load_document, extract_raw_structure


def test_load_document():
    doc = load_document("TechArk-Content-Document.docx")
    assert doc is not None
    assert len(doc.paragraphs) > 0


def test_extract_raw_structure():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)

    # Must have content
    assert len(raw) > 0

    # Every item must have style and text keys
    for item in raw:
        assert "style" in item
        assert "text" in item
        assert item["text"] != ""

    # Must contain our known styles
    styles = [item["style"] for item in raw]
    assert "Heading 1" in styles
    assert "Heading 3" in styles
    assert "Normal" in styles

    print(f"\n[OK] Total non-empty paragraphs: {len(raw)}")
    print(f"[OK] Unique styles found: {set(styles)}")