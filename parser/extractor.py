# parser/extractor.py


def extract_fields(paragraphs):
    """
    Extracts field label/value pairs from a section's paragraph list.

    Handles two patterns:
    Pattern A: Heading 3 = label, Normal = value (Hero, Gallery)
    Pattern B: Normal "Label: Value" lines (CTA Banner, Options Page)

    Special case: If Normal lines under a Heading 3 are themselves
    "Label: Value" pairs (e.g. CTA Button sub-fields), split them
    into separate fields instead of joining as one value.

    Returns list of dicts: [{label, value, raw_style, acf_type}]
    """
    from parser.mapper import map_field_type

    fields = []
    current_label  = None
    current_values = []
    current_style  = None

    # Detect pattern — check if section has any Heading 3
    has_heading3 = any(item["style"] == "Heading 3" for item in paragraphs)

    def is_inline_pair(lines):
        """
        Returns True if lines look like sub-field Label: Value pairs
        that should be split into separate fields.
        """
        if len(lines) < 2:
            return False

        # All lines must be Label: Value format
        pair_count = sum(1 for line in lines if ":" in line)
        if pair_count != len(lines):
            return False

        # Keep navigation menu items as one block
        nav_count = sum(1 for line in lines if " — /" in line)
        if nav_count > 0:
            return False

        # Keep gallery image lines as one block — detected by "File:" pattern
        image_count = sum(1 for line in lines if "File:" in line or "| Alt:" in line)
        if image_count > 0:
            return False

        return True

    def save_current():
        if not current_label:
            return

        if is_inline_pair(current_values):
            # Split into separate fields e.g. primary_cta_label, primary_cta_url
            for line in current_values:
                if ":" in line:
                    sub_label, _, sub_value = line.partition(":")
                    sub_label = sub_label.strip()
                    sub_value = sub_value.strip()

                    # Convert Yes/No to boolean string for true_false fields
                    if sub_value.lower() == "yes":
                        sub_value = "1"
                    elif sub_value.lower() == "no":
                        sub_value = "0"

                    combined_label = f"{current_label} {sub_label}"
                    fields.append({
                        "label":     combined_label,
                        "value":     sub_value,
                        "raw_style": current_style,
                        "acf_type":  map_field_type(combined_label, sub_value),
                    })
        else:
            value = "\n".join(current_values).strip()
            fields.append({
                "label":     current_label,
                "value":     value,
                "raw_style": current_style,
                "acf_type":  map_field_type(current_label, value),
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
                label = label.strip()
                value = value.strip()
                fields.append({
                    "label":     label,
                    "value":     value,
                    "raw_style": style,
                    "acf_type":  map_field_type(label, value),
                })

    return fields


def extract_table_items(paragraphs):
    """
    Extracts repeater items from a table-based section.
    Detects TableRow items and converts each row into a repeater item.

    The Stats section table has columns:
    Stat Number | Label | Suffix | Icon (optional)

    Returns list of item dicts compatible with extract_repeater_items() format.
    """
    from parser.mapper import map_field_type

    # Get column headers from the first TableRow or use defaults
    col_headers = ["stat_number", "label", "suffix", "icon"]

    items = []
    for item in paragraphs:
        if not item.get("is_table_row"):
            continue

        cells = item["table_cells"]
        sub_fields = []

        for i, value in enumerate(cells):
            label    = col_headers[i] if i < len(col_headers) else f"column_{i+1}"
            acf_type = map_field_type(label, value)
            sub_fields.append({
                "label":    label,
                "value":    value,
                "acf_type": acf_type,
            })

        if sub_fields:
            items.append({
                "item_index":   len(items) + 1,
                "item_heading": f"Stat {len(items) + 1}",
                "sub_fields":   sub_fields,
            })

    return items

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