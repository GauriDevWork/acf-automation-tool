# tests/test_schema_output.py
import os
import json
from parser.parser import parse_document
from schema.output import build_all_schemas, build_options_schema


def get_schemas():
    result = parse_document("TechArk-Content-Document.docx")
    return build_all_schemas(result)


def test_schema_output_count():
    schemas = get_schemas()
    # 11 sections minus 1 skipped (Stats table) = 10
    assert len(schemas) == 10


def test_schema_json_file_exists():
    get_schemas()
    assert os.path.exists("output/schema.json")


def test_schema_json_valid():
    get_schemas()
    with open("output/schema.json", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) == 10


def test_cpt_configs_file_exists():
    get_schemas()
    assert os.path.exists("output/cpt_configs.json")


def test_cpt_configs_count():
    get_schemas()
    with open("output/cpt_configs.json", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 2


def test_all_field_groups_have_key():
    schemas = get_schemas()
    for fg in schemas:
        assert "key" in fg
        assert fg["key"].startswith("group_")


def test_all_field_groups_have_location():
    schemas = get_schemas()
    for fg in schemas:
        assert "location" in fg
        assert isinstance(fg["location"], list)


def test_hero_in_schema():
    schemas = get_schemas()
    titles = [fg["title"] for fg in schemas]
    assert "1. Hero Section" in titles


def test_options_page_location():
    result = parse_document("TechArk-Content-Document.docx")
    fg = build_options_schema(
        "10. Global Header",
        result["10. Global Header"]["fields"]
    )
    assert fg["location"][0][0]["param"]  == "options_page"
    assert fg["location"][0][0]["value"]  == "acf-options"


def test_schemas_dir_exists():
    get_schemas()
    assert os.path.exists("output/schemas")