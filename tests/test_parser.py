# tests/test_parser.py
import os
import json
from parser.parser import parse_document


def test_parse_document_returns_dict():
    result = parse_document("TechArk-Content-Document.docx")
    assert isinstance(result, dict)


def test_parse_document_section_count():
    result = parse_document("TechArk-Content-Document.docx")
    assert len(result) == 11


def test_all_sections_have_type():
    result = parse_document("TechArk-Content-Document.docx")
    valid_types = {"field_group", "repeater", "cpt", "options_page"}
    for name, data in result.items():
        assert "type" in data, f"Missing type in {name}"
        assert data["type"] in valid_types, f"Invalid type in {name}"


def test_field_group_sections_have_fields():
    result = parse_document("TechArk-Content-Document.docx")
    fg_sections = {k: v for k, v in result.items() if v["type"] == "field_group"}
    for name, data in fg_sections.items():
        assert "fields" in data, f"Missing fields in {name}"


def test_repeater_sections_have_items():
    result = parse_document("TechArk-Content-Document.docx")
    rep_sections = {k: v for k, v in result.items() if v["type"] == "repeater"}
    for name, data in rep_sections.items():
        assert "items" in data, f"Missing items in {name}"


def test_cpt_sections_have_entries():
    result = parse_document("TechArk-Content-Document.docx")
    cpt_sections = {k: v for k, v in result.items() if v["type"] == "cpt"}
    for name, data in cpt_sections.items():
        assert "entries" in data, f"Missing entries in {name}"


def test_options_page_sections_have_fields():
    result = parse_document("TechArk-Content-Document.docx")
    opt_sections = {k: v for k, v in result.items() if v["type"] == "options_page"}
    for name, data in opt_sections.items():
        assert "fields" in data, f"Missing fields in {name}"


def test_hero_section_content():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    assert hero["type"] == "field_group"
    assert len(hero["fields"]) == 5


def test_team_section_content():
    result = parse_document("TechArk-Content-Document.docx")
    team = result["4. Team Section"]
    assert team["type"] == "cpt"
    assert len(team["entries"]) == 3


def test_faq_section_content():
    result = parse_document("TechArk-Content-Document.docx")
    faq = result["6. FAQ Section"]
    assert faq["type"] == "repeater"
    assert len(faq["items"]) == 3


def test_output_json_created():
    parse_document("TechArk-Content-Document.docx")
    assert os.path.exists("output/parsed_output.json")


def test_output_json_valid():
    parse_document("TechArk-Content-Document.docx")
    with open("output/parsed_output.json", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 11