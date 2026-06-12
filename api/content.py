# api/content.py
import re


def update_post_acf_fields(client, post_id, fields_dict, post_type="pages"):
    """
    Pushes ACF field values to a WordPress post/page.
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


def push_flat_sections(client, parsed_output, page_id=5, section_page_map=None):
    """
    Pushes all field_group sections to WordPress.
    Uses section_page_map to route each section to a specific page ID.
    Falls back to page_id if section not in map.

    Args:
        client:           WPClient instance
        parsed_output:    full dict from parse_document()
        page_id:          default WordPress page ID (default: 5)
        section_page_map: optional dict of {section_name: page_id}
    """
    results = {}
    if section_page_map is None:
        section_page_map = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "field_group":
            continue

        fields = data["fields"]
        if not fields:
            print(f"[SKIP] {section_name} — no fields")
            continue

        # Look up page ID for this section — fall back to default
        target_page_id = section_page_map.get(section_name, page_id)

        print(f"\n[PUSH] {section_name}")

        fields_dict = {}
        for f in fields:
            if f["acf_type"] == "image":
                print(f"  [SKIP] {f['label']} — image field, requires media upload")
                continue
            if f["acf_type"] == "gallery":
                print(f"  [SKIP] {f['label']} — gallery field, handled in image upload step")
                continue
            name = to_field_name(f["label"], section_name)
            fields_dict[name] = f["value"]

        if not fields_dict:
            print(f"  [SKIP] {section_name} — all fields are images")
            results[section_name] = "SKIPPED"
            continue

        success = update_post_acf_fields(client, target_page_id, fields_dict)
        results[section_name] = "OK" if success else "FAIL"

        acf = get_post_acf_fields(client, target_page_id)
        if acf:
            first_key = list(fields_dict.keys())[0]
            val = acf.get(first_key, "NOT FOUND")
            print(f"  [VERIFY] {first_key}: {str(val)[:60]}")

    return results


def format_repeater_payload(items, section_name=None):
    """
    Converts parsed repeater items into ACF-compatible array format.
    Sub-field names inside repeaters are NOT prefixed.
    """
    rows = []
    for item in items:
        row = {}
        for sf in item["sub_fields"]:
            if sf["acf_type"] == "image":
                continue
            name = to_field_name(sf["label"])
            row[name] = sf["value"]
        if row:
            rows.append(row)
    return rows


def push_repeater_sections(client, parsed_output, page_id=5, section_page_map=None):
    """
    Pushes all repeater sections to WordPress.
    Uses section_page_map to route each section to a specific page ID.
    Falls back to page_id if section not in map.

    Args:
        client:           WPClient instance
        parsed_output:    full dict from parse_document()
        page_id:          default WordPress page ID (default: 5)
        section_page_map: optional dict of {section_name: page_id}
    """
    results = {}
    if section_page_map is None:
        section_page_map = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "repeater":
            continue

        items = data["items"]
        if not items:
            print(f"[SKIP] {section_name} — no items (table-based section)")
            results[section_name] = "SKIPPED"
            continue

        # Look up page ID for this section — fall back to default
        target_page_id = section_page_map.get(section_name, page_id)

        print(f"\n[PUSH] {section_name} ({len(items)} items)")

        field_name = to_field_name(
            re.sub(r'^\d+\.\s*', '', section_name)
               .replace(" Section", "")
               .replace(" section", "")
        )

        rows = format_repeater_payload(items)
        if not rows:
            print(f"  [SKIP] {section_name} — all sub-fields are images")
            results[section_name] = "SKIPPED"
            continue

        fields_dict = {field_name: rows}
        success = update_post_acf_fields(client, target_page_id, fields_dict)
        results[section_name] = "OK" if success else "FAIL"

        acf = get_post_acf_fields(client, target_page_id)
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

    section_page_map = getattr(config, 'SECTION_PAGE_MAP', {})

    print("\n=== Pushing flat sections ===")
    flat_results = push_flat_sections(
        client, result,
        page_id=config.PAGE_ID,
        section_page_map=section_page_map
    )

    print("\n=== Pushing repeater sections ===")
    repeater_results = push_repeater_sections(
        client, result,
        page_id=config.PAGE_ID,
        section_page_map=section_page_map
    )