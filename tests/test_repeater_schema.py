# tests/test_repeater_schema.py
from schema.builder import build_repeater_field_group
from parser.parser import parse_document


def get_result():
    return parse_document("TechArk-Content-Document.docx")


def test_faq_repeater_group_has_required_keys():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    assert "key"      in fg
    assert "title"    in fg
    assert "fields"   in fg
    assert "location" in fg


def test_faq_repeater_has_one_field():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    assert len(fg["fields"]) == 1


def test_faq_repeater_field_type():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    assert fg["fields"][0]["type"] == "repeater"


def test_faq_repeater_sub_field_count():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    assert len(sub_fields) == 2


def test_faq_repeater_sub_field_types():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    types = [sf["type"] for sf in sub_fields]
    assert "text"    in types
    assert "wysiwyg" in types


def test_faq_repeater_sub_field_names():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    names = [sf["name"] for sf in sub_fields]
    assert "question" in names
    assert "answer"   in names


def test_partner_logos_sub_field_count():
    result = get_result()
    fg = build_repeater_field_group("8. Partner Logos Section",
                                    result["8. Partner Logos Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    assert len(sub_fields) == 3


def test_partner_logos_sub_field_types():
    result = get_result()
    fg = build_repeater_field_group("8. Partner Logos Section",
                                    result["8. Partner Logos Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    types = [sf["type"] for sf in sub_fields]
    assert "image" in types
    assert "text"  in types
    assert "url"   in types


def test_all_sub_field_keys_unique():
    result = get_result()
    fg = build_repeater_field_group("6. FAQ Section", result["6. FAQ Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    keys = [sf["key"] for sf in sub_fields]
    assert len(keys) == len(set(keys))


def test_all_sub_field_names_snake_case():
    result = get_result()
    fg = build_repeater_field_group("8. Partner Logos Section",
                                    result["8. Partner Logos Section"]["items"])
    sub_fields = fg["fields"][0]["sub_fields"]
    for sf in sub_fields:
        assert " " not in sf["name"]
        assert sf["name"] == sf["name"].lower()