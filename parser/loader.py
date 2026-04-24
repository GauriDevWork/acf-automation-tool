# parser/loader.py
from docx import Document


def load_document(file_path):
    """
    Opens a .docx file and returns the Document object.
    Raises FileNotFoundError if the path is wrong.
    """
    try:
        doc = Document(file_path)
        print(f"[OK] Loaded: {file_path}")
        print(f"[OK] Total paragraphs: {len(doc.paragraphs)}")
        return doc
    except FileNotFoundError:
        raise FileNotFoundError(f"[ERROR] File not found: {file_path}")


def extract_raw_structure(doc):
    """
    Reads every paragraph in the document.
    Returns a list of dicts: {style, text}
    Skips completely empty paragraphs.
    """
    raw = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            raw.append({
                "style": para.style.name if para.style else "Normal",
                "text":  text
            })
    return raw


if __name__ == "__main__":
    doc = load_document("TechArk-Content-Document.docx")
    raw = extract_raw_structure(doc)
    print(f"\n--- All paragraph styles found ---")
    for item in raw:
        print(f"  [{item['style']}]  {item['text'][:60]}")