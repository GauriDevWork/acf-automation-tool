# tests/test_builder.py
from schema.builder import to_snake_case, make_field_key, build_field, build_field_group
from parser.parser import parse_document


# ── to_snake_case ─────────────────────────────────────────────────────────────
def test_snake_case_simple():
    assert to_snake_case("Hero Title") == "hero_title"

def test_snake_case_strips_numbers():
    assert to_snake_case("1.1 Headline") == "headline"

def test_snake_case_multiple_words():
    assert to_snake_case("Primary CTA Button") == "primary_cta_button"

def test_snake_case_background_image():
    assert to_snake_case("1.5 Background Image") == "background_image"


# ── make_field_key ────────────────────────────────────────────────────────────
def test_field_key_format():
    key = make_field_key("Hero Section", "Headline")
    assert key.startswith("field_")
    assert len(key) == 14  # "field_" + 8 chars

def test_field_key_deterministic():
    key1 = make_field_key("Hero Section", "Headline")
    key2 = make_field_key("Hero Section", "Headline")
    assert key1 == key2

def test_field_key_unique():
    key1 = make_field_key("Hero Section", "Headline")
    key2 = make_field_key("Hero Section", "Subheadline")
    assert key1 != key2


# ── build_field_group ─────────────────────────────────────────────────────────
def test_field_group_has_required_keys():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    assert "key"      in fg
    assert "title"    in fg
    assert "fields"   in fg
    assert "location" in fg

def test_field_group_key_format():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    assert fg["key"].startswith("group_")

def test_field_group_field_count():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    assert len(fg["fields"]) == 5

def test_field_group_field_keys_unique():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    keys = [f["key"] for f in fg["fields"]]
    assert len(keys) == len(set(keys))

def test_field_group_field_names_snake_case():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    for field in fg["fields"]:
        assert " " not in field["name"]
        assert field["name"] == field["name"].lower()

def test_field_group_location_structure():
    result = parse_document("TechArk-Content-Document.docx")
    hero = result["1. Hero Section"]
    fg = build_field_group("1. Hero Section", hero["fields"])
    assert isinstance(fg["location"], list)
    assert isinstance(fg["location"][0], list)
    assert "param" in fg["location"][0][0]