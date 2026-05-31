# api/options.py
from api.content import to_field_name


def push_options_fields(client, fields_dict):
    """
    Pushes ACF options page fields via custom REST endpoint.
    Uses the acf-tool/v1/options endpoint registered in functions.php.

    Args:
        client:      WPClient instance
        fields_dict: dict of {field_name: value}

    Returns True on success, False on failure.
    """
    response = client.post("acf-tool/v1/options", fields_dict)

    if response.status_code == 200:
        print(f"[OK] Pushed {len(fields_dict)} options fields")
        return True
    else:
        print(f"[ERROR] Failed to push options fields")
        print(f"[ERROR] Status: {response.status_code}")
        print(f"[ERROR] Response: {response.text[:300]}")
        return False


def get_options_fields(client):
    """
    Reads all ACF options page field values.
    Returns dict of {field_name: value} or empty dict on failure.
    """
    response = client.get("acf-tool/v1/options")

    if response.status_code == 200:
        data = response.json()
        return data if isinstance(data, dict) else {}
    else:
        print(f"[ERROR] Failed to read options fields: {response.status_code}")
        return {}


def push_all_options_sections(client, parsed_output):
    """
    Pushes all options_page sections to the ACF Options Page.
    Skips image fields.

    Args:
        client:        WPClient instance
        parsed_output: full dict from parse_document()

    Returns dict of results per section.
    """
    results = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "options_page":
            continue

        fields = data["fields"]
        if not fields:
            print(f"[SKIP] {section_name} — no fields")
            continue

        print(f"\n[OPTIONS] {section_name}")

        fields_dict = {}
        for f in fields:
            if f["acf_type"] == "image":
                print(f"  [SKIP] {f['label']} — image field")
                continue
            name = to_field_name(f["label"])
            fields_dict[name] = f["value"]

        if not fields_dict:
            print(f"  [SKIP] {section_name} — all fields are images")
            results[section_name] = "SKIPPED"
            continue

        success = push_options_fields(client, fields_dict)
        results[section_name] = "OK" if success else "FAIL"

        # Verify one field
        options = get_options_fields(client)
        if options:
            first_key = list(fields_dict.keys())[0]
            val = options.get(first_key, "NOT FOUND")
            print(f"  [VERIFY] {first_key}: {str(val)[:60]}")

    return results


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result  = parse_document("TechArk-Content-Document.docx")
    results = push_all_options_sections(client, result)

    print("\n--- Options summary ---")
    for section, status in results.items():
        print(f"  [{status}] {section}")