# api/content.py
import json
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


def to_field_name(label):
    """
    Converts a field label to snake_case field name.
    Matches the same logic used in schema/builder.py to_snake_case().
    """
    name = re.sub(r'^\d+[\.\d]*\s*', '', label)
    name = name.lower()
    name = re.sub(r'[^a-z0-9]+', '_', name)
    name = name.strip('_')
    return name


def push_flat_sections(client, parsed_output, page_id=5):
    """
    Pushes all field_group sections to the WordPress page.
    Skips image fields — those require media upload first.

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

        # Build field dict — skip image fields
        fields_dict = {}
        for f in fields:
            if f["acf_type"] == "image":
                print(f"  [SKIP] {f['label']} — image field, requires media upload")
                continue
            name = to_field_name(f["label"])
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


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result = parse_document("TechArk-Content-Document.docx")
    results = push_flat_sections(client, result, page_id=5)

    print("\n--- Push summary ---")
    for section, status in results.items():
        print(f"  [{status}] {section}")