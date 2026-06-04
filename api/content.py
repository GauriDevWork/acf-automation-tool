# api/content.py
import re


def update_post_acf_fields(client, post_id, fields_dict, post_type="pages"):
    """
    Pushes ACF field values to a WordPress post/page.

    Args:
        client:      WPClient instance
        post_id:     WordPress post/page ID
        fields_dict: dict of {field_name: value}
        post_type:   WordPress post type endpoint (default: pages)

    Returns True on success, False on failure.
    """
    payload  = {"acf": fields_dict}
    response = client.post(f"wp/v2/{post_type}/{post_id}", payload)

    if response.status_code == 200:
        print(f"[OK] Pushed {len(fields_dict)} fields to {post_type}/{post_id}")
        return True
    else:
        print(f"[ERROR] Failed to push to {post_type}/{post_id}")
        print(f"[ERROR] Status: {response.status_code}")
        print(f"[ERROR] Response: {response.text[:300]}")
        return False


def get_post_acf_fields(client, post_id, post_type="pages"):
    """
    Reads ACF field values from a WordPress post/page.
    Returns dict of {field_name: value} or None on failure.
    """
    response = client.get(
        f"wp/v2/{post_type}/{post_id}?context=edit&_fields=acf"
    )

    if response.status_code == 200:
        data = response.json()
        return data.get("acf", {})
    else:
        print(f"[ERROR] Failed to read {post_type}/{post_id}: {response.status_code}")
        return None


def to_field_name(label, section_name=None):
    """
    Converts a field label to snake_case field name.
    Optionally prefixes with section slug to avoid field name collisions.

    Without prefix: 'Headline'              -> 'headline'
    With prefix:    'Headline' + '1. Hero'  -> 'hero_section_headline'
    """
    name = re.sub(r'^\d+[\.\d]*\s*', '', label)
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')

    if section_name:
        prefix = re.sub(r'^\d+\.\s*', '', section_name)
        prefix = prefix.lower()
        prefix = re.sub(r'[^a-z0-9]+', '_', prefix)
        prefix = prefix.strip('_')
        name = f"{prefix}_{name}"

    return name


def push_flat_sections(client, parsed_output, page_id=5):
    """
    Pushes all field_group sections to the WordPress page.
    Skips image fields — those require media upload first.
    Field names are prefixed with section slug to avoid collisions.

    Args:
        client:        WPClient instance
        parsed_output: full dict from parse_document()
        page_id:       WordPress page ID to push to (default: 5)

    Returns dict of results per section.
    """
    results = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "field_group":
            continue

        fields = data["fields"]
        if not fields:
            print(f"[SKIP] {section_name} — no fields")
            continue

        print(f"\n[PUSH] {section_name}")

        # Build field dict — skip image fields, prefix names with section
        fields_dict = {}
        for f in fields:
            if f["acf_type"] == "image":
                print(f"  [SKIP] {f['label']} — image field, requires media upload")
                continue
            name = to_field_name(f["label"], section_name)
            fields_dict[name] = f["value"]

        if not fields_dict:
            print(f"  [SKIP] {section_name} — all fields are images")
            results[section_name] = "SKIPPED"
            continue

        success = update_post_acf_fields(client, page_id, fields_dict)
        results[section_name] = "OK" if success else "FAIL"

        # Verify first field read back
        acf = get_post_acf_fields(client, page_id)
        if acf:
            first_key = list(fields_dict.keys())[0]
            val = acf.get(first_key, "NOT FOUND")
            print(f"  [VERIFY] {first_key}: {str(val)[:60]}")

    return results


def format_repeater_payload(items, section_name=None):
    """
    Converts parsed repeater items into ACF-compatible array format.
    Sub-field names inside repeaters are NOT prefixed — they live
    inside the repeater namespace.

    Input (from extract_repeater_items):
    [
        {
            "item_index": 1,
            "item_heading": "FAQ 1",
            "sub_fields": [
                {"label": "Question", "value": "How long...", "acf_type": "text"},
                {"label": "Answer",   "value": "Most mid...", "acf_type": "wysiwyg"}
            ]
        },
        ...
    ]

    Output (ACF repeater format):
    [
        {"question": "How long...", "answer": "Most mid..."},
        ...
    ]
    """
    rows = []
    for item in items:
        row = {}
        for sf in item["sub_fields"]:
            if sf["acf_type"] == "image":
                continue
            # Sub-fields inside repeaters are NOT prefixed
            name = to_field_name(sf["label"])
            row[name] = sf["value"]
        if row:
            rows.append(row)
    return rows


def push_repeater_sections(client, parsed_output, page_id=5):
    """
    Pushes all repeater sections to the WordPress page.
    Skips Stats section — table-based, no items.

    Args:
        client:        WPClient instance
        parsed_output: full dict from parse_document()
        page_id:       WordPress page ID to push to (default: 5)

    Returns dict of results per section.
    """
    results = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "repeater":
            continue

        items = data["items"]
        if not items:
            print(f"[SKIP] {section_name} — no items (table-based section)")
            results[section_name] = "SKIPPED"
            continue

        print(f"\n[PUSH] {section_name} ({len(items)} items)")

        # Get repeater field name — NOT prefixed, uses section slug
        field_name = to_field_name(
            re.sub(r'^\d+\.\s*', '', section_name)
               .replace(" Section", "")
               .replace(" section", "")
        )

        # Format payload — sub-fields not prefixed
        rows = format_repeater_payload(items)
        if not rows:
            print(f"  [SKIP] {section_name} — all sub-fields are images")
            results[section_name] = "SKIPPED"
            continue

        fields_dict = {field_name: rows}
        success = update_post_acf_fields(client, page_id, fields_dict)
        results[section_name] = "OK" if success else "FAIL"

        # Verify row count
        acf = get_post_acf_fields(client, page_id)
        if acf and field_name in acf:
            actual_rows = acf[field_name]
            count = len(actual_rows) if isinstance(actual_rows, list) else "?"
            print(f"  [VERIFY] {field_name}: {count} rows in WordPress")
        else:
            print(f"  [VERIFY] {field_name}: not found in response")

    return results


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result = parse_document("TechArk-Content-Document.docx")

    print("\n=== Pushing flat sections ===")
    flat_results = push_flat_sections(client, result, page_id=5)

    print("\n=== Pushing repeater sections ===")
    repeater_results = push_repeater_sections(client, result, page_id=5)

    print("\n--- Push summary ---")
    all_results = {**flat_results, **repeater_results}
    for section, status in all_results.items():
        print(f"  [{status}] {section}")