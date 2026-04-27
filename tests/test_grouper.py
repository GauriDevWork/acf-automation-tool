# tests/test_grouper.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections

def test_group_sections_count():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    sections = group_sections(raw)

    assert len(sections) == 11

def test_group_sections_names():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    sections = group_sections(raw)

    assert "1. Hero Section" in sections
    assert "4. Team Section" in sections
    assert "11. Global Footer" in sections

def test_group_sections_have_content():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    sections = group_sections(raw)

    # Every section except Stats must have more than 1 paragraph
    for name, paragraphs in sections.items():
        if "Stats" not in name:
            assert len(paragraphs) > 1, f"Section '{name}' has no content"

def test_no_paragraphs_before_first_section():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    sections = group_sections(raw)

    # Cover page content must be excluded
    # No section key should be None or empty string
    for name in sections.keys():
        assert name is not None
        assert name.strip() != ""