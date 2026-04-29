# tests/test_extractor.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections
from parser.extractor import extract_fields


def get_sections():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    return group_sections(raw)


def test_hero_field_count():
    sections = get_sections()
    fields = extract_fields(sections["1. Hero Section"])
    # Hero has 5 fields: Headline, Subheadline, Primary CTA, Secondary CTA, Background Image
    assert len(fields) == 5


def test_hero_field_labels():
    sections = get_sections()
    fields = extract_fields(sections["1. Hero Section"])
    labels = [f["label"] for f in fields]
    assert "1.1 Headline" in labels
    assert "1.5 Background Image" in labels


def test_hero_field_values_not_empty():
    sections = get_sections()
    fields = extract_fields(sections["1. Hero Section"])
    for f in fields:
        assert f["value"] != "", f"Field '{f['label']}' has empty value"


def test_annotation_line_skipped():
    sections = get_sections()
    fields = extract_fields(sections["1. Hero Section"])
    # Annotation [FIELD GROUP: hero] must not appear as a field label or value
    for f in fields:
        assert not f["label"].startswith("[")
        assert not f["value"].startswith("[FIELD GROUP")


def test_faq_field_count():
    sections = get_sections()
    fields = extract_fields(sections["6. FAQ Section"])
    # FAQ has 3 items: FAQ 1, FAQ 2, FAQ 3
    assert len(fields) == 3


def test_all_fields_have_required_keys():
    sections = get_sections()
    for section_name, paragraphs in sections.items():
        fields = extract_fields(paragraphs)
        for f in fields:
            assert "label" in f, f"Missing label in {section_name}"
            assert "value" in f, f"Missing value in {section_name}"
            assert "raw_style" in f, f"Missing raw_style in {section_name}"