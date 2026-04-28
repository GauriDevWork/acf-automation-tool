# tests/test_classifier.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections
from parser.classifier import classify_section


def get_sections():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    return group_sections(raw)


def test_classify_field_groups():
    sections = get_sections()
    assert classify_section("1. Hero Section",       sections["1. Hero Section"])       == "field_group"
    assert classify_section("7. CTA Banner Section", sections["7. CTA Banner Section"]) == "field_group"
    assert classify_section("9. Gallery Section",    sections["9. Gallery Section"])    == "field_group"


def test_classify_repeaters():
    sections = get_sections()
    assert classify_section("2. Stats / Numbers Section", sections["2. Stats / Numbers Section"]) == "repeater"
    assert classify_section("5. Testimonials Section",    sections["5. Testimonials Section"])    == "repeater"
    assert classify_section("6. FAQ Section",             sections["6. FAQ Section"])             == "repeater"
    assert classify_section("8. Partner Logos Section",   sections["8. Partner Logos Section"])   == "repeater"


def test_classify_cpts():
    sections = get_sections()
    assert classify_section("3. Services Section", sections["3. Services Section"]) == "cpt"
    assert classify_section("4. Team Section",     sections["4. Team Section"])     == "cpt"


def test_classify_options_pages():
    sections = get_sections()
    assert classify_section("10. Global Header", sections["10. Global Header"]) == "options_page"
    assert classify_section("11. Global Footer", sections["11. Global Footer"]) == "options_page"


def test_all_sections_classified():
    sections = get_sections()
    valid_types = {"field_group", "repeater", "cpt", "options_page"}
    for name, paragraphs in sections.items():
        result = classify_section(name, paragraphs)
        assert result in valid_types, f"'{name}' returned invalid type: '{result}'"