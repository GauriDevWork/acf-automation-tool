# schema/builder.py
import hashlib
import re


def to_snake_case(text, section_name=None):
    """
    Converts a label to snake_case field name.
    Optionally prefixes with section slug to avoid field name collisions.

    'Hero Title'              -> 'hero_title'
    '1.1 Headline'            -> 'headline'
    '1.1 Headline' + section  -> 'hero_section_headline'
    """
    text = re.sub(r'^\d+[\.\d]*\s*', '', text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text)
    text = text.strip('_')

    if section_name:
        prefix = re.sub(r'^\d+\.\s*', '', section_name)
        prefix = prefix.lower()
        prefix = re.sub(r'[^a-z0-9]+', '_', prefix)
        prefix = prefix.strip('_')
        text = f"{prefix}_{text}"

    return text


def make_field_key(section_name, label):
    """
    Generates a unique ACF field key.
    Uses MD5 hash of section_name + label — same input always
    produces the same key (idempotent).
    Format: field_ + first 8 chars of MD5 hash
    """
    raw = f"{section_name}_{label}".encode("utf-8")
    return "field_" + hashlib.md5(raw).hexdigest()[:8]


def make_group_key(section_name):
    """
    Generates a unique ACF field group key.
    Format: group_ + first 8 chars of MD5 hash of section name
    """
    raw = section_name.encode("utf-8")
    return "group_" + hashlib.md5(raw).hexdigest()[:8]


def build_field(section_name, label, acf_type):
    """
    Builds a single ACF field dict.
    Field name is prefixed with section slug to avoid collisions.
    show_in_rest and edit_in_rest enabled at field level.
    """
    return {
        "key":          make_field_key(section_name, label),
        "label":        label,
        "name":         to_snake_case(label, section_name),
        "type":         acf_type,
        "instructions": "",
        "required":     0,
        "show_in_rest": 1,
        "edit_in_rest": 1,
    }


def build_field_group(section_name, fields, location_type="post_type",
                      location_value="page"):
    """
    Builds a complete ACF field group dict from a section's fields list.
    show_in_rest enabled at field group level for ACF Pro 6.x compatibility.
    """
    acf_fields = []
    for f in fields:
        acf_fields.append(build_field(
            section_name,
            f["label"],
            f["acf_type"]
        ))

    return {
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                acf_fields,
        "show_in_rest":          1,
        "location":              [[{
            "param":    location_type,
            "operator": "==",
            "value":    location_value,
        }]],
        "menu_order":            0,
        "position":              "normal",
        "style":                 "default",
        "label_placement":       "top",
        "instruction_placement": "label",
        "active":                True,
    }


def build_repeater_sub_field(section_name, item_heading, label, acf_type):
    """
    Builds a single sub-field dict for inside a repeater.
    Sub-field names are NOT prefixed — they live inside the repeater namespace.
    """
    raw = f"{section_name}_{item_heading}_{label}".encode("utf-8")
    key = "field_" + hashlib.md5(raw).hexdigest()[:8]
    return {
        "key":          key,
        "label":        label,
        "name":         to_snake_case(label),
        "type":         acf_type,
        "instructions": "",
        "required":     0,
        "show_in_rest": 1,
        "edit_in_rest": 1,
    }


def build_repeater_field_group(section_name, items,
                                location_type="post_type",
                                location_value="page"):
    """
    Builds an ACF field group containing a single repeater field.
    show_in_rest enabled at field group level for ACF Pro 6.x compatibility.
    """
    if not items:
        return build_field_group(section_name, [], location_type, location_value)

    first_item = items[0]
    sub_fields = []
    for sf in first_item["sub_fields"]:
        sub_fields.append(build_repeater_sub_field(
            section_name,
            first_item["item_heading"],
            sf["label"],
            sf["acf_type"]
        ))

    section_slug = to_snake_case(
        re.sub(r'^\d+\.\s*', '', section_name)
           .replace(" Section", "")
           .replace(" section", "")
    )

    repeater_field = {
        "key":          make_field_key(section_name, "repeater"),
        "label":        section_name,
        "name":         section_slug,
        "type":         "repeater",
        "instructions": "",
        "required":     0,
        "show_in_rest": 1,
        "edit_in_rest": 1,
        "sub_fields":   sub_fields,
    }

    return {
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                [repeater_field],
        "show_in_rest":          1,
        "location":              [[{
            "param":    location_type,
            "operator": "==",
            "value":    location_value,
        }]],
        "menu_order":            0,
        "position":              "normal",
        "style":                 "default",
        "label_placement":       "top",
        "instruction_placement": "label",
        "active":                True,
    }


def get_cpt_slug(section_name):
    """
    Derives the CPT post type slug from section name.
    '3. Services Section' -> 'service'
    '4. Team Section'     -> 'team_member'
    """
    name = re.sub(r'^\d+\.\s*', '', section_name)
    name = name.replace(" Section", "").replace(" section", "").strip()

    cpt_map = {
        "team":     "team_member",
        "services": "service",
        "service":  "service",
    }

    key = name.lower().split()[0] if name else ""
    return cpt_map.get(key, to_snake_case(name))


def build_cpt_schema(section_name, entries):
    """
    Builds ACF field group scoped to CPT, plus CPT registration config.
    show_in_rest enabled at field group level for ACF Pro 6.x compatibility.
    """
    if not entries:
        return None

    cpt_slug = get_cpt_slug(section_name)

    first_entry = entries[0]
    acf_fields  = []
    for f in first_entry["acf_fields"]:
        acf_fields.append(build_field(section_name, f["label"], f["acf_type"]))

    field_group = {
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                acf_fields,
        "show_in_rest":          1,
        "location":              [[{
            "param":    "post_type",
            "operator": "==",
            "value":    cpt_slug,
        }]],
        "menu_order":            0,
        "position":              "normal",
        "style":                 "default",
        "label_placement":       "top",
        "instruction_placement": "label",
        "active":                True,
    }

    match = re.match(r'^\d+\.\s*', section_name)
    label = section_name.replace(
        " Section", ""
    ).replace(match.group(), "").strip() if match else section_name

    cpt_config = {
        "post_type": cpt_slug,
        "label":     label,
        "supports":  ["title", "thumbnail", "excerpt"],
    }

    field_slug = to_snake_case(
        re.sub(r'^\d+\.\s*', '', section_name)
           .replace(" Section", "")
    )
    relationship_field = {
        "key":          make_field_key(section_name, "relationship"),
        "label":        f"{section_name} Posts",
        "name":         f"{field_slug}_posts",
        "type":         "relationship",
        "post_type":    [cpt_slug],
        "instructions": "",
        "required":     0,
        "show_in_rest": 1,
        "edit_in_rest": 1,
    }

    return {
        "field_group":        field_group,
        "cpt_config":         cpt_config,
        "relationship_field": relationship_field,
    }


def build_options_schema(section_name, fields):
    """
    Builds ACF field group for options page sections.
    show_in_rest enabled at field group level for ACF Pro 6.x compatibility.
    """
    acf_fields = []
    for f in fields:
        acf_fields.append(build_field(
            section_name,
            f["label"],
            f["acf_type"]
        ))

    return {
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                acf_fields,
        "show_in_rest":          1,
        "location":              [[{
            "param":    "options_page",
            "operator": "==",
            "value":    "acf-options",
        }]],
        "menu_order":            0,
        "position":              "normal",
        "style":                 "default",
        "label_placement":       "top",
        "instruction_placement": "label",
        "active":                True,
    }


if __name__ == "__main__":
    import json
    from parser.parser import parse_document

    result = parse_document("TechArk-Content-Document.docx")

    hero = result["1. Hero Section"]
    fg   = build_field_group("1. Hero Section", hero["fields"])
    print("\n--- Hero Section ---")
    print(f"  show_in_rest (group): {fg['show_in_rest']}")
    for f in fg["fields"]:
        print(f"  {f['name']} (show_in_rest: {f['show_in_rest']})")

    cta = result["7. CTA Banner Section"]
    fg2 = build_field_group("7. CTA Banner Section", cta["fields"])
    print("\n--- CTA Banner Section ---")
    print(f"  show_in_rest (group): {fg2['show_in_rest']}")
    for f in fg2["fields"]:
        print(f"  {f['name']} (show_in_rest: {f['show_in_rest']})")