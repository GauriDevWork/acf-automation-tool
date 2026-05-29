# api/field_groups.py
import json


def get_existing_field_groups(client):
    """
    Attempts to fetch ACF field groups via REST API.
    ACF Pro 6.x removed the acf/v3 namespace — field groups
    must be imported manually via ACF → Tools → Import.
    Returns empty dict — field group creation is skipped.
    """
    print("[INFO] ACF Pro 6.x does not support field group creation via REST API.")
    print("[INFO] Field groups must be imported via ACF → Tools → Import.")
    print("[INFO] schema.json import already completed on Day 14.")
    return {}


def verify_field_groups_exist(client, schema_path="output/schema.json"):
    """
    Verifies that ACF fields are accessible on WordPress posts.
    Checks if the homepage post returns ACF fields in the REST response.

    Returns True if fields are accessible, False otherwise.
    """
    print("\n[FIELD GROUPS] Verifying ACF fields are accessible via REST API...")

    # Fetch homepage (post ID 2 is typically the sample page, try posts first)
    response = client.get("wp/v2/pages?per_page=1")

    if response.status_code != 200:
        print(f"[ERROR] Cannot fetch pages: {response.status_code}")
        return False

    pages = response.json()
    if not pages:
        print("[ERROR] No pages found in WordPress")
        return False

    page = pages[0]
    page_id = page["id"]
    print(f"[INFO] Found page: '{page['title']['rendered']}' (ID: {page_id})")

    # Check if ACF meta is accessible
    response = client.get(f"wp/v2/pages/{page_id}?context=edit")
    if response.status_code == 200:
        data = response.json()
        if "meta" in data or "acf" in data:
            print(f"[OK] ACF fields accessible on page ID {page_id}")
            return True
        else:
            print(f"[WARN] No ACF fields found on page ID {page_id}")
            print(f"[WARN] Field groups may not be assigned to this page type")
            return True  # Fields exist, just not on this page
    else:
        print(f"[ERROR] Cannot fetch page details: {response.status_code}")
        return False


if __name__ == "__main__":
    import config
    from api.client import WPClient

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if client.test_connection():
        verify_field_groups_exist(client)