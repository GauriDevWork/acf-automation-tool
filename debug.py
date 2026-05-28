# debug.py
from parser.loader import load_document, extract_raw_structure
from parser.grouper import group_sections

doc = load_document("TechArk-Content-Document.docx")
raw = extract_raw_structure(doc)
sections = group_sections(raw)

print("\n--- CTA Banner Section ---")
for item in sections["7. CTA Banner Section"]:
    print(f"  [{item['style']}] {item['text'][:60]}")

print("\n--- Global Header ---")
for item in sections["10. Global Header"]:
    print(f"  [{item['style']}] {item['text'][:60]}")