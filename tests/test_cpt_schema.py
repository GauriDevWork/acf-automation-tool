# tests/test_cpt_schema.py
from schema.builder import build_cpt_schema, get_cpt_slug
from parser.parser import parse_document


def get_result():
    return parse_document("TechArk-Content-Document.docx")


def test_get_cpt_slug_team():
    assert get_cpt_slug("4. Team Section") == "team_member"


def test_get_cpt_slug_services():
    assert get_cpt_slug("3. Services Section") == "service"


def test_cpt_config_post_type():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    assert schema["cpt_config"]["post_type"] == "team_member"


def test_cpt_config_has_required_keys():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    config = schema["cpt_config"]
    assert "post_type" in config
    assert "label"     in config
    assert "supports"  in config


def test_cpt_config_supports():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    assert "title"     in schema["cpt_config"]["supports"]
    assert "thumbnail" in schema["cpt_config"]["supports"]
    assert "excerpt"   in schema["cpt_config"]["supports"]


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
    # Field names are now prefixed with section slug
    assert "team_section_role"       in names
    assert "team_section_bio"        in names
    assert "team_section_photo"      in names
    assert "team_section_linkedin"   in names
    assert "team_section_department" in names


def test_cpt_schema_relationship_field():
    result = get_result()
    schema = build_cpt_schema("4. Team Section", result["4. Team Section"]["entries"])
    rel = schema["relationship_field"]
    assert rel["type"]     == "relationship"
    assert "team_member"   in rel["post_type"]
    assert rel["name"]     == "team_posts"


def test_services_cpt_schema():
    result = get_result()
    schema = build_cpt_schema("3. Services Section", result["3. Services Section"]["entries"])
    assert schema["cpt_config"]["post_type"]                    == "service"
    assert schema["field_group"]["location"][0][0]["value"]     == "service"