# parser/parser.py
import json
import os

from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections
from parser.classifier import classify_section
from parser.extractor import extract_fields, extract_repeater_items, extract_cpt_entries


def parse_document(file_path, output_dir="output"):
    """
    Main orchestrator — ties all parser functions together.

    Steps:
    1. Load the docx file
    2. Extract raw paragraph structure
    3. Group paragraphs into named sections
    4. Classify each section type
    5. Call the correct extractor per section type
    6. Assemble complete output dict
    7. Save as parsed_output.json

    Returns complete output dict:
    {
        section_name: {
            "type": "field_group" | "repeater" | "cpt" | "options_page",
            "fields" | "items" | "entries": [...]
        },
        ...
    }
    """
    print(f"\n[PARSER] Starting: {file_path}")

    # Step 1-3: Load and structure
    doc      = load_document(file_path)
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    print(f"[PARSER] Sections found: {len(sections)}")

    output = {}

    # Step 4-5: Classify and extract
    for section_name, paragraphs in sections.items():
        section_type = classify_section(section_name, paragraphs)

        print(f"[PARSER]   [{section_type:<15}] {section_name}")

        if section_type == "repeater":
            data = {
                "type":  "repeater",
                "items": extract_repeater_items(paragraphs)
            }
        elif section_type == "cpt":
            data = {
                "type":    "cpt",
                "entries": extract_cpt_entries(paragraphs)
            }
        elif section_type == "options_page":
            data = {
                "type":   "options_page",
                "fields": extract_fields(paragraphs)
            }
        else:
            # field_group default
            data = {
                "type":   "field_group",
                "fields": extract_fields(paragraphs)
            }

        output[section_name] = data

    # Step 6: Save JSON
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "parsed_output.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[PARSER] Done. Output saved to: {output_path}")
    print(f"[PARSER] Total sections parsed: {len(output)}")

    return output


if __name__ == "__main__":
    result = parse_document("TechArk-Content-Document.docx")

    print("\n--- Section summary ---")
    for name, data in result.items():
        section_type = data["type"]
        if section_type == "repeater":
            count = len(data["items"])
            print(f"  [{section_type:<15}] {name} — {count} items")
        elif section_type == "cpt":
            count = len(data["entries"])
            print(f"  [{section_type:<15}] {name} — {count} entries")
        else:
            count = len(data["fields"])
            print(f"  [{section_type:<15}] {name} — {count} fields")