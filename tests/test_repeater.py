# tests/test_repeater.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections
from parser.extractor import extract_repeater_items


def get_sections():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    return group_sections(raw)


def test_faq_item_count():
    sections = get_sections()
    items = extract_repeater_items(sections["6. FAQ Section"])
    assert len(items) == 3


def test_faq_sub_field_count():
    sections = get_sections()
    items = extract_repeater_items(sections["6. FAQ Section"])
    for item in items:
        assert len(item["sub_fields"]) == 2


def test_faq_sub_field_types():
    sections = get_sections()
    items = extract_repeater_items(sections["6. FAQ Section"])
    for item in items:
        labels = [sf["label"] for sf in item["sub_fields"]]
        types  = [sf["acf_type"] for sf in item["sub_fields"]]
        assert "Question" in labels
        assert "Answer" in labels
        assert "text" in types
        assert "wysiwyg" in types


def test_testimonials_item_count():
    sections = get_sections()
    items = extract_repeater_items(sections["5. Testimonials Section"])
    assert len(items) == 2


def test_testimonials_has_image():
    sections = get_sections()
    items = extract_repeater_items(sections["5. Testimonials Section"])
    for item in items:
        types = [sf["acf_type"] for sf in item["sub_fields"]]
        assert "image" in types


def test_partner_logos_item_count():
    sections = get_sections()
    items = extract_repeater_items(sections["8. Partner Logos Section"])
    assert len(items) == 4


def test_partner_logos_sub_field_types():
    sections = get_sections()
    items = extract_repeater_items(sections["8. Partner Logos Section"])
    for item in items:
        types = [sf["acf_type"] for sf in item["sub_fields"]]
        assert "image" in types
        assert "url" in types
        assert "text" in types


def test_all_items_have_required_keys():
    sections = get_sections()
    repeater_sections = [
        "6. FAQ Section",
        "5. Testimonials Section",
        "8. Partner Logos Section"
    ]
    for section_name in repeater_sections:
        items = extract_repeater_items(sections[section_name])
        for item in items:
            assert "item_index" in item
            assert "item_heading" in item
            assert "sub_fields" in item
            for sf in item["sub_fields"]:
                assert "label" in sf
                assert "value" in sf
                assert "acf_type" in sf