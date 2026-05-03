# parser/extractor.py


def extract_fields(paragraphs):
    """
    Extracts field label/value pairs from a section's paragraph list.

    Handles two patterns:
    Pattern A: Heading 3 = label, Normal = value (Hero, Gallery)
    Pattern B: Normal "Label: Value" lines (CTA Banner, Options Page)

    Returns list of dicts: [{label, value, raw_style}]
    """
    fields = []
    current_label = None
    current_values = []
    current_style  = None

    # Detect pattern — check if section has any Heading 3
    has_heading3 = any(item["style"] == "Heading 3" for item in paragraphs)

    def save_current():
        if current_label:
            fields.append({
                "label":     current_label,
                "value":     "\n".join(current_values).strip(),
                "raw_style": current_style,
            })

    if has_heading3:
        # Pattern A — Heading 3 as label
        for item in paragraphs:
            style = item["style"]
            text  = item["text"]

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

        save_current()

    else:
        # Pattern B — Normal "Label: Value" lines
        for item in paragraphs:
            style = item["style"]
            text  = item["text"]

            if text.startswith("[") and style == "Normal":
                continue

            if ":" in text and style in ("Normal", "List Paragraph"):
                label, _, value = text.partition(":")
                fields.append({
                    "label":     label.strip(),
                    "value":     value.strip(),
                    "raw_style": style,
                })

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
            "item_heading": "FAQ 1",
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
        if ":" in text:
            label, _, value = text.partition(":")
            return label.strip(), value.strip()
        return "content", text.strip()

    for item in paragraphs:
        style = item["style"]
        text  = item["text"]

        if text.startswith("[") and style == "Normal":
            continue

        if style == "Heading 3" and text.lower().startswith("section"):
            continue

        if style == "Heading 3":
            if current_item is not None:
                items.append(current_item)

            current_item = {
                "item_index":   len(items) + 1,
                "item_heading": text,
                "sub_fields":   []
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

    if current_item is not None:
        items.append(current_item)

    return items


def extract_cpt_entries(paragraphs):
    """
    Extracts CPT entries from a section's paragraph list.

    Pattern:
    - Heading 3 = CPT entry heading (e.g. 'Team Member 1', 'Service 1')
    - Normal paragraphs below it = fields in "Label: Value" format
    - Label containing 'post title' or exactly 'title' → becomes WP post_title
    - Everything else → becomes an ACF field on the CPT

    Returns list of post dicts:
    [
        {
            "post_title": "Priya Sharma",
            "entry_heading": "Team Member 1",
            "acf_fields": [
                {"label": "Role",  "value": "Founder & CEO", "acf_type": "text"},
                ...
            ]
        }
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

        if text.startswith("[") and style == "Normal":
            continue

        if style == "Heading 3":
            if current_entry is not None:
                entries.append(current_entry)

            current_entry = {
                "post_title":    None,
                "entry_heading": text,
                "acf_fields":    []
            }

        elif style == "Normal":
            if current_entry is not None:
                label, value = parse_field(text)
                if "post title" in label.lower() or label.strip().lower() == "title":
                    current_entry["post_title"] = value
                else:
                    acf_type = map_field_type(label, value)
                    current_entry["acf_fields"].append({
                        "label":    label,
                        "value":    value,
                        "acf_type": acf_type
                    })

    if current_entry is not None:
        entries.append(current_entry)

    return entries