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

def extract_cpt_entries(paragraphs):
    """
    Extracts CPT entries from a section's paragraph list.

    Pattern:
    - Heading 3 = CPT entry heading (e.g. 'Team Member 1', 'Service 1')
    - Normal paragraphs below it = fields in "Label: Value" format
    - Label containing 'post title' → becomes the WP post_title
    - Everything else → becomes an ACF field on the CPT

    Returns list of post dicts:
    [
        {
            "post_title": "Priya Sharma",
            "entry_heading": "Team Member 1",
            "acf_fields": [
                {"label": "Role",       "value": "Founder & CEO",  "acf_type": "text"},
                {"label": "Bio",        "value": "Priya has 18...", "acf_type": "wysiwyg"},
                {"label": "Photo",      "value": "priya-sharma.jpg","acf_type": "image"},
                {"label": "LinkedIn",   "value": "https://...",     "acf_type": "url"},
                {"label": "Department", "value": "Leadership",      "acf_type": "text"},
            ]
        },
        ...
    ]
    """
    from parser.mapper import map_field_type

    entries = []
    current_entry = None

    def parse_field(text):
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

        if style == "Heading 3":
            # Save previous entry
            if current_entry is not None:
                entries.append(current_entry)

            # Start new entry
            current_entry = {
                "post_title":    None,
                "entry_heading": text,
                "acf_fields":    []
            }

        elif style == "Normal":
            if current_entry is not None:
                label, value = parse_field(text)

                # Detect post title field
                if "post title" in label.lower() or label.strip().lower() == "title":
                    current_entry["post_title"] = value
                else:
                    acf_type = map_field_type(label, value)
                    current_entry["acf_fields"].append({
                        "label":    label,
                        "value":    value,
                        "acf_type": acf_type
                    })

    # Save last entry
    if current_entry is not None:
        entries.append(current_entry)

    return entries


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure
    from parser.grouper import group_sections

    doc      = load_document("TechArk-Content-Document.docx")
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    for section_name in ["4. Team Section", "3. Services Section"]:
        print(f"\n--- {section_name} ---")
        entries = extract_cpt_entries(sections[section_name])
        print(f"  Entries found: {len(entries)}")
        for entry in entries:
            print(f"\n  [{entry['entry_heading']}]")
            print(f"    post_title: {entry['post_title']}")
            for f in entry["acf_fields"]:
                print(f"    [{f['acf_type']:<12}] {f['label']}: {f['value'][:50]}")