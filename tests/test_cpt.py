# tests/test_cpt.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections
from parser.extractor import extract_cpt_entries


def get_sections():
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    return group_sections(raw)


def test_team_entry_count():
    sections = get_sections()
    entries = extract_cpt_entries(sections["4. Team Section"])
    assert len(entries) == 3


def test_team_post_titles():
    sections = get_sections()
    entries = extract_cpt_entries(sections["4. Team Section"])
    titles = [e["post_title"] for e in entries]
    assert "Priya Sharma" in titles
    assert "Marcus Williams" in titles
    assert "Aisha Patel" in titles


def test_team_no_none_post_titles():
    sections = get_sections()
    entries = extract_cpt_entries(sections["4. Team Section"])
    for entry in entries:
        assert entry["post_title"] is not None, \
            f"{entry['entry_heading']} has no post_title"


def test_team_acf_field_types():
    sections = get_sections()
    entries = extract_cpt_entries(sections["4. Team Section"])
    for entry in entries:
        types = [f["acf_type"] for f in entry["acf_fields"]]
        assert "text"    in types  # Role, Department
        assert "wysiwyg" in types  # Bio
        assert "image"   in types  # Photo
        assert "url"     in types  # LinkedIn


def test_services_entry_count():
    sections = get_sections()
    entries = extract_cpt_entries(sections["3. Services Section"])
    assert len(entries) == 4


def test_services_post_titles():
    sections = get_sections()
    entries = extract_cpt_entries(sections["3. Services Section"])
    titles = [e["post_title"] for e in entries]
    assert "WordPress Development" in titles
    assert "Accessibility Remediation" in titles


def test_services_no_none_post_titles():
    sections = get_sections()
    entries = extract_cpt_entries(sections["3. Services Section"])
    for entry in entries:
        assert entry["post_title"] is not None, \
            f"{entry['entry_heading']} has no post_title"


def test_all_entries_have_required_keys():
    sections = get_sections()
    cpt_sections = ["4. Team Section", "3. Services Section"]
    for section_name in cpt_sections:
        entries = extract_cpt_entries(sections[section_name])
        for entry in entries:
            assert "post_title"    in entry
            assert "entry_heading" in entry
            assert "acf_fields"    in entry
            for f in entry["acf_fields"]:
                assert "label"    in f
                assert "value"    in f
                assert "acf_type" in f