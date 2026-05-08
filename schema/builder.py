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


def build_cpt_config(section_name, cpt_slug):
    """
    Generates a CPT registration config dict.
    This is used to register the custom post type in WordPress
    via register_post_type() in functions.php or via REST API.

    Args:
        section_name: e.g. "4. Team Section"
        cpt_slug:     e.g. "team_member"

    Returns CPT registration dict.
    """
    # Generate human-readable labels from slug
    label = cpt_slug.replace("_", " ").title()

    return {
        "post_type": cpt_slug,
        "label":     label,
        "labels": {
            "name":          label + "s",
            "singular_name": label,
            "add_new":       "Add New " + label,
            "add_new_item":  "Add New " + label,
            "edit_item":     "Edit " + label,
            "view_item":     "View " + label,
            "all_items":     "All " + label + "s",
        },
        "public":       True,
        "has_archive":  True,
        "supports":     ["title", "thumbnail", "excerpt"],
        "show_in_rest": True,
    }


def get_cpt_slug(section_name):
    """
    Derives CPT slug from section name.
    '3. Services Section' → 'service'
    '4. Team Section'     → 'team_member'
    """
    slug_map = {
        "team":    "team_member",
        "service": "service",
        "staff":   "staff_member",
        "blog":    "post",
    }
    name_lower = section_name.lower()
    for keyword, slug in slug_map.items():
        if keyword in name_lower:
            return slug
    # Fallback — snake_case the section name
    return to_snake_case(
        re.sub(r'^\d+\.\s*', '', section_name)
           .replace(" Section", "")
    )


def build_cpt_schema(section_name, entries):
    """
    Builds the complete schema output for a CPT section.
    Returns a dict containing:
    - cpt_config:  CPT registration dict
    - field_group: ACF field group scoped to the CPT
    - relationship_field: ACF field to link CPT posts to a page

    Args:
        section_name: e.g. "4. Team Section"
        entries:      list of CPT entry dicts from extract_cpt_entries()
    """
    if not entries:
        return None

    cpt_slug   = get_cpt_slug(section_name)
    cpt_config = build_cpt_config(section_name, cpt_slug)

    # Build ACF fields from first entry's acf_fields
    # All entries share the same field structure
    first_entry = entries[0]
    acf_fields  = []
    for f in first_entry["acf_fields"]:
        acf_fields.append(build_field(
            section_name,
            f["label"],
            f["acf_type"]
        ))

    # Field group scoped to CPT
    field_group = build_field_group(
        section_name,
        first_entry["acf_fields"],
        location_type="post_type",
        location_value=cpt_slug
    )

    # Relationship field on the page to link CPT posts
    relationship_field = {
        "key":           make_field_key(section_name, "relationship"),
        "label":         section_name + " — Related Posts",
        "name":          to_snake_case(
                             re.sub(r'^\d+\.\s*', '', section_name)
                                .replace(" Section", "")
                         ) + "_posts",
        "type":          "relationship",
        "post_type":     [cpt_slug],
        "filters":       ["search"],
        "instructions":  f"Select {cpt_slug} posts to display in this section",
        "required":      0,
    }

    return {
        "cpt_config":          cpt_config,
        "field_group":         field_group,
        "relationship_field":  relationship_field,
    }

def build_options_schema(section_name, fields):
        """
        Builds ACF field group for options page sections.
        Location rule uses options_page instead of post_type.
        Scoped to ACF Options Page — applies sitewide.

        Args:
            section_name: e.g. "10. Global Header"
            fields:       list of {label, value, acf_type} dicts
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

    # Test on Team section
    team = result["4. Team Section"]
    schema = build_cpt_schema("4. Team Section", team["entries"])

    print("\n--- Team CPT Config ---")
    print(json.dumps(schema["cpt_config"], indent=2))

    print("\n--- Team ACF Field Group ---")
    print(json.dumps(schema["field_group"], indent=2))

    print("\n--- Team Relationship Field ---")
    print(json.dumps(schema["relationship_field"], indent=2))

    # Test on Services section
    services = result["3. Services Section"]
    schema2  = build_cpt_schema("3. Services Section", services["entries"])
    print("\n--- Services CPT slug ---")
    print(schema2["cpt_config"]["post_type"])