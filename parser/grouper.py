# parser/grouper.py

def group_sections(raw_structure):
    """
    Walks the raw paragraph list from extract_raw_structure().
    Splits into sections every time a Heading 1 is encountered.
    Returns a dict: {section_name: [list of paragraph dicts]}
    Skips any paragraphs before the first Heading 1 (cover page content).
    """
    sections = {}
    current_section = None

    for item in raw_structure:
        if item["style"] == "Heading 1":
            current_section = item["text"]
            sections[current_section] = []
        elif current_section is not None:
            sections[current_section].append(item)

    return sections


if __name__ == "__main__":
    from parser.loader import load_document, extract_raw_structure

    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    sections = group_sections(raw)

    print(f"\n--- Sections found: {len(sections)} ---")
    for name, paragraphs in sections.items():
        print(f"\n  [{name}]  ({len(paragraphs)} paragraphs)")
        for p in paragraphs[:3]:
            print(f"    [{p['style']}] {p['text'][:60]}")
        if len(paragraphs) > 3:
            print(f"    ... and {len(paragraphs) - 3} more")