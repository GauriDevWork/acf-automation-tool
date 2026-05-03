# parser/mapper.py

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".svg", ".gif", ".webp")


def map_field_type(label, value):
    """
    Detects the ACF field type from a field's label and value.
    Uses pattern matching on the value string — not meaning.

    Detection order matters — specific patterns checked first,
    generic fallback last.

    Returns one of:
    url | image | email | number | true_false | textarea | text
    """
    v = value.strip()
    l = label.lower()

    # 1. URL — starts with / or contains http
    if v.startswith("/") or v.startswith("http"):
        return "url"

   # 2. Image — ends with or contains image extension (only if value is short)
    if len(v) < 120 and (
        v.lower().endswith(IMAGE_EXTENSIONS) or
        any(ext in v.lower() for ext in IMAGE_EXTENSIONS)
    ):
        return "image"

    # 3. Email — contains @ symbol
    if "@" in v:
        return "email"

    # 4. Number — pure numeric value
    if v.isdigit():
        return "number"

    # 5. True/False — boolean values
    if v.lower() in ("yes", "no", "true", "false"):
        return "true_false"

    # 6. Label hint — wysiwyg for known rich text fields
    if any(word in l for word in ("answer", "bio", "description", "content", "body")):
        return "wysiwyg"

    # 7. Long text — textarea
    if len(v) > 100:
        return "textarea"

    # 8. Safe default
    return "text"


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure
    from parser.grouper import group_sections
    from parser.extractor import extract_fields

    doc      = load_document("TechArk-Content-Document.docx")
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    for section_name, paragraphs in sections.items():
        fields = extract_fields(paragraphs)
        if not fields:
            continue
        print(f"\n--- {section_name} ---")
        for f in fields:
            acf_type = map_field_type(f["label"], f["value"])
            print(f"  [{acf_type:<12}]  {f['label']}")