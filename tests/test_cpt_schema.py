# tests/test_cpt_schema.py
from schema.builder import build_cpt_schema, get_cpt_slug, build_cpt_config
from parser.parser import parse_document


def get_result():
    return parse_document("TechArk-Content-Document.docx")


def test_get_cpt_slug_team():
    assert get_cpt_slug("4. Team Section") == "team_member"


def test_get_cpt_slug_services():
    assert get_cpt_slug("3. Services Section") == "service"


def test_cpt_config_post_type():
    config = build_cpt_config("4. Team Section", "team_member")
    assert config["post_type"] == "team_member"


def test_cpt_config_has_required_keys():
    config = build_cpt_config("4. Team Section", "team_member")
    assert "post_type"   in config
    assert "label"       in config
    assert "labels"      in config
    assert "supports"    in config
    assert "show_in_rest" in config


def test_cpt_config_supports():
    config = build_cpt_config("4. Team Section", "team_member")
    assert "title"     in config["supports"]
    assert "thumbnail" in config["supports"]
    assert "excerpt"   in config["supports"]


def test_cpt_schema_has_required_keys():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    assert "cpt_config"         in schema
    assert "field_group"        in schema
    assert "relationship_field" in schema


def test_cpt_schema_field_group_location():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    location = schema["field_group"]["location"][0][0]
    assert location["param"]    == "post_type"
    assert location["operator"] == "=="
    assert location["value"]    == "team_member"


def test_cpt_schema_field_group_fields():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    fields = schema["field_group"]["fields"]
    names  = [f["name"] for f in fields]
    assert "role"       in names
    assert "bio"        in names
    assert "photo"      in names
    assert "linkedin"   in names
    assert "department" in names


def test_cpt_schema_relationship_field():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    rel = schema["relationship_field"]
    assert rel["type"]          == "relationship"
    assert "team_member"        in rel["post_type"]
    assert rel["name"]          == "team_posts"


def test_services_cpt_schema():
    result = get_result()
    schema = build_cpt_schema("3. Services Section", result["3. Services Section"]["entries"])
    assert schema["cpt_config"]["post_type"]        == "service"
    assert schema["field_group"]["location"][0][0]["value"] == "service"