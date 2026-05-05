# schema/builder.py
import hashlib
import re


def to_snake_case(text):
    """
    Converts a label to snake_case field name.
    'Hero Title'    → 'hero_title'
    '1.1 Headline'  → 'headline'
    'Primary CTA Button' → 'primary_cta_button'
    """
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
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                acf_fields,
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
    Uses section + item_heading + label to generate a unique key.
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
    }


def build_repeater_field_group(section_name, items,
                                location_type="post_type",
                                location_value="page"):
    """
    Builds an ACF field group containing a single repeater field.
    The repeater field contains sub_fields derived from the first item's
    sub_fields — all items share the same sub-field structure.

    Args:
        section_name: e.g. "6. FAQ Section"
        items:        list of item dicts from extract_repeater_items()

    Returns ACF field group dict with repeater field inside.
    """
    if not items:
        return build_field_group(section_name, [], location_type, location_value)

    # All items share the same sub-field structure — use first item
    first_item = items[0]
    sub_fields = []
    for sf in first_item["sub_fields"]:
        sub_fields.append(build_repeater_sub_field(
            section_name,
            first_item["item_heading"],
            sf["label"],
            sf["acf_type"]
        ))

    # Extract repeater name from section name
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
        "sub_fields":   sub_fields,
    }

    return {
        "key":                   make_group_key(section_name),
        "title":                 section_name,
        "fields":                [repeater_field],
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


if __name__ == "__main__":
    import json
    from parser.parser import parse_document

    result = parse_document("TechArk-Content-Document.docx")

    # Test on FAQ repeater
    faq = result["6. FAQ Section"]
    fg  = build_repeater_field_group("6. FAQ Section", faq["items"])
    print("\n--- FAQ Repeater Field Group ---")
    print(json.dumps(fg, indent=2))

    # Test on Partner Logos repeater
    logos = result["8. Partner Logos Section"]
    fg2   = build_repeater_field_group("8. Partner Logos Section", logos["items"])
    print("\n--- Partner Logos Repeater Field Group ---")
    print(json.dumps(fg2, indent=2))