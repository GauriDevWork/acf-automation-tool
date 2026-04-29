# parser/extractor.py


def extract_fields(paragraphs):
    """
    Extracts field label/value pairs from a section's paragraph list.

    Pattern:
    - Heading 3 = field label
    - Normal paragraph(s) following it = field value
    - Multiple Normal paragraphs are joined with newline
    - Annotation line (starts with '[') is skipped
    - List Paragraph items are collected as a list

    Returns list of dicts: [{label, value, raw_style}]
    """
    fields = []
    current_label = None
    current_values = []
    current_style  = None

    def save_current():
        if current_label:
            fields.append({
                "label":     current_label,
                "value":     "\n".join(current_values).strip(),
                "raw_style": current_style,
            })

    for item in paragraphs:
        style = item["style"]
        text  = item["text"]

        # Skip annotation line
        if text.startswith("[") and style == "Normal":
            continue

        if style == "Heading 3":
            save_current()
            current_label  = text
            current_values = []
            current_style  = style

        elif style in ("Normal", "List Paragraph"):
            if current_label is not None:
                current_values.append(text)

    # Save last field
    save_current()

    return fields


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure
    from parser.grouper import group_sections

    doc      = load_document("TechArk-Content-Document.docx")
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    # Test on Hero section
    print("\n--- Hero Section fields ---")
    hero_fields = extract_fields(sections["1. Hero Section"])
    for f in hero_fields:
        print(f"  [{f['label']}]")
        print(f"    → {f['value'][:80]}")

    # Test on FAQ section
    print("\n--- FAQ Section fields ---")
    faq_fields = extract_fields(sections["6. FAQ Section"])
    for f in faq_fields:
        print(f"  [{f['label']}]")
        print(f"    → {f['value'][:80]}")