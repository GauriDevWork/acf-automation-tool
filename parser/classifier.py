# parser/classifier.py

# Annotation keywords mapped to section types
ANNOTATION_MAP = {
    "[CPT:":          "cpt",
    "[REPEATER:":     "repeater",
    "[OPTIONS PAGE:": "options_page",
    "[FIELD GROUP:":  "field_group",
}

# Keyword fallback — if no annotation found, guess from section name
KEYWORD_MAP = {
    "team":        "cpt",
    "service":     "cpt",
    "staff":       "cpt",
    "blog":        "cpt",
    "faq":         "repeater",
    "testimonial": "repeater",
    "partner":     "repeater",
    "logo":        "repeater",
    "stat":        "repeater",
    "gallery":     "field_group",
    "header":      "options_page",
    "footer":      "options_page",
    "cta":         "field_group",
    "hero":        "field_group",
    "banner":      "field_group",
}


def classify_section(section_name, paragraphs):
    """
    Detects the ACF structure type for a section.

    Strategy:
    1. Look for annotation in first Normal paragraph e.g. [CPT: service]
    2. If no annotation, fall back to keyword matching on section name
    3. If no keyword match, default to field_group

    Returns one of: cpt | repeater | options_page | field_group
    """
    # Step 1 — check annotation in first paragraph
    for item in paragraphs[:3]:
        if item["style"] == "Normal":
            text = item["text"]
            for keyword, section_type in ANNOTATION_MAP.items():
                if keyword in text:
                    return section_type
            break  # only check first Normal paragraph

    # Step 2 — keyword fallback on section name
    name_lower = section_name.lower()
    for keyword, section_type in KEYWORD_MAP.items():
        if keyword in name_lower:
            return section_type

    # Step 3 — safe default
    return "field_group"


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure
    from parser.grouper import group_sections

    doc      = load_document("TechArk-Content-Document.docx")
    raw      = extract_raw_structure(doc)
    sections = group_sections(raw)

    print(f"\n--- Section classifications ---")
    for name, paragraphs in sections.items():
        section_type = classify_section(name, paragraphs)
        print(f"  [{section_type:<15}]  {name}")