# schema/output.py
import json
import os

from schema.builder import (
    build_field_group,
    build_repeater_field_group,
    build_cpt_schema,
)


def build_options_schema(section_name, fields):
    """
    Builds ACF field group for options page sections.
    Location rule: options_page instead of post_type.
    """
    from schema.builder import make_group_key, build_field
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


def build_all_schemas(parsed_output, output_dir="output"):
    """
    Routes each section to the correct builder function.
    Saves individual JSON files + combined schema.json.

    Router logic:
    - field_group  → build_field_group(section_name, fields)
    - repeater     → build_repeater_field_group(section_name, items)
    - cpt          → build_cpt_schema(section_name, entries)
    - options_page → build_options_schema(section_name, fields)

    Returns list of all field group dicts.
    """
    os.makedirs(output_dir, exist_ok=True)
    schemas_dir = os.path.join(output_dir, "schemas")
    os.makedirs(schemas_dir, exist_ok=True)

    all_field_groups = []
    cpt_configs      = []

    for section_name, data in parsed_output.items():
        section_type = data["type"]
        print(f"[SCHEMA] [{section_type:<15}] {section_name}")

        if section_type == "field_group":
            fg = build_field_group(section_name, data["fields"])
            all_field_groups.append(fg)

        elif section_type == "repeater":
            if data["items"]:
                fg = build_repeater_field_group(section_name, data["items"])
                all_field_groups.append(fg)
            else:
                print(f"[SCHEMA]   Skipped — no items (table-based section)")

        elif section_type == "cpt":
            result = build_cpt_schema(section_name, data["entries"])
            if result:
                all_field_groups.append(result["field_group"])
                cpt_configs.append(result["cpt_config"])

        elif section_type == "options_page":
            if data["fields"]:
                fg = build_options_schema(section_name, data["fields"])
                all_field_groups.append(fg)

        # Save individual JSON file
        safe_name = section_name.replace(" ", "_").replace(".", "").replace("/", "_").lower()
        section_path = os.path.join(schemas_dir, f"{safe_name}.json")
        with open(section_path, "w", encoding="utf-8") as f:
            if section_type == "cpt":
                result = build_cpt_schema(section_name, data["entries"])
                json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                json.dump(all_field_groups[-1] if all_field_groups else {}, f,
                          indent=2, ensure_ascii=False)

    # Save combined schema.json — ACF bulk import format
    schema_path = os.path.join(output_dir, "schema.json")
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(all_field_groups, f, indent=2, ensure_ascii=False)

    # Save CPT configs separately
    if cpt_configs:
        cpt_path = os.path.join(output_dir, "cpt_configs.json")
        with open(cpt_path, "w", encoding="utf-8") as f:
            json.dump(cpt_configs, f, indent=2, ensure_ascii=False)

    print(f"\n[SCHEMA] Done.")
    print(f"[SCHEMA] Field groups generated: {len(all_field_groups)}")
    print(f"[SCHEMA] CPT configs generated:  {len(cpt_configs)}")
    print(f"[SCHEMA] schema.json saved to:   {schema_path}")

    return all_field_groups


if __name__ == "__main__":
    from parser.parser import parse_document

    result = parse_document("TechArk-Content-Document.docx")
    schemas = build_all_schemas(result)

    print(f"\n--- Schema summary ---")
    for fg in schemas:
        field_count = len(fg.get("fields", []))
        print(f"  [{fg['key']}] {fg['title']} — {field_count} fields")