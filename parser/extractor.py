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

def extract_repeater_items(paragraphs):
    """
    Extracts repeater items from a section's paragraph list.

    Pattern:
    - Heading 3 = item heading (e.g. 'FAQ 1', 'Partner 1', 'Testimonial 1')
    - Normal paragraphs below it = sub-fields in "Label: Value" format
    - Each item becomes a dict with item_index and sub_fields list

    Returns list of item dicts:
    [
        {
            "item_index": 1,
            "sub_fields": [
                {"label": "Question", "value": "...", "acf_type": "text"},
                {"label": "Answer",   "value": "...", "acf_type": "wysiwyg"}
            ]
        },
        ...
    ]
    """
    from parser.mapper import map_field_type

    items = []
    current_item = None

    def parse_sub_field(text):
        """
        Splits 'Label: Value' into label and value.
        If no colon found, treats entire text as value with label 'content'.
        """
        if ":" in text:
            label, _, value = text.partition(":")
            return label.strip(), value.strip()
        return "content", text.strip()

    for item in paragraphs:
        style = item["style"]
        text  = item["text"]

        # Skip annotation line
        if text.startswith("[") and style == "Normal":
            continue

        # Skip section heading (e.g. "Trusted by Industry Leaders")
        if style == "Heading 3" and text.lower().startswith("section"):
            continue

        if style == "Heading 3":
            # Save previous item
            if current_item is not None:
                items.append(current_item)

            # Start new item
            current_item = {
                "item_index": len(items) + 1,
                "item_heading": text,
                "sub_fields": []
            }

        elif style in ("Normal", "List Paragraph"):
            if current_item is not None:
                label, value = parse_sub_field(text)
                acf_type = map_field_type(label, value)
                current_item["sub_fields"].append({
                    "label":    label,
                    "value":    value,
                    "acf_type": acf_type
                })

    # Save last item
    if current_item is not None:
        items.append(current_item)

    return items


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure
    from parser.grouper import group_sections

    doc      = load_document("TechArk-Content-Document.docx")
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    # Test on FAQ, Testimonials, Partner Logos
    for section_name in [
        "6. FAQ Section",
        "5. Testimonials Section",
        "8. Partner Logos Section"
    ]:
        print(f"\n--- {section_name} ---")
        items = extract_repeater_items(sections[section_name])
        print(f"  Items found: {len(items)}")
        for item in items:
            print(f"\n  [{item['item_heading']}]")
            for sf in item["sub_fields"]:
                print(f"    [{sf['acf_type']:<12}] {sf['label']}: {sf['value'][:50]}")