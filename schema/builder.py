# schema/builder.py
import hashlib


def to_snake_case(text):
    """
    Converts a label to snake_case field name.
    'Hero Title'    → 'hero_title'
    '1.1 Headline'  → 'headline'
    'Primary CTA Button' → 'primary_cta_button'
    """
    import re
    # Remove leading numbers and dots (e.g. "1.1 ")
    text = re.sub(r'^\d+[\.\d]*\s*', '', text)
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric with underscore
    text = re.sub(r'[^a-z0-9]+', '_', text)
    # Strip leading/trailing underscores
    text = text.strip('_')
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
    Follows ACF export format exactly.
    """
    return {
        "key":          make_field_key(section_name, label),
        "label":        label,
        "name":         to_snake_case(label),
        "type":         acf_type,
        "instructions": "",
        "required":     0,
    }


def build_field_group(section_name, fields, location_type="post_type",
                      location_value="page"):
    """
    Builds a complete ACF field group dict from a section's fields list.
    Follows ACF export/import format exactly.

    Args:
        section_name:   e.g. "1. Hero Section"
        fields:         list of {label, value, acf_type} dicts
        location_type:  ACF location rule param (default: post_type)
        location_value: ACF location rule value (default: page)

    Returns ACF field group dict ready for JSON export.
    """
    acf_fields = []
    for f in fields:
        acf_fields.append(build_field(
            section_name,
            f["label"],
            f["acf_type"]
        ))

    return {
        "key":                make_group_key(section_name),
        "title":              section_name,
        "fields":             acf_fields,
        "location":           [[{
            "param":    location_type,
            "operator": "==",
            "value":    location_value,
        }]],
        "menu_order":         0,
        "position":           "normal",
        "style":              "default",
        "label_placement":    "top",
        "instruction_placement": "label",
        "active":             True,
    }


if __name__ == "__main__":
    import json
    from parser.parser import parse_document

    result = parse_document("TechArk-Content-Document.docx")

    # Test on Hero section
    hero = result["1. Hero Section"]
    field_group = build_field_group("1. Hero Section", hero["fields"])

    print("\n--- Hero Section Field Group ---")
    print(json.dumps(field_group, indent=2))