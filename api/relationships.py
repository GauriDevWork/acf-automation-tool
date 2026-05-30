# api/relationships.py
from api.content import update_post_acf_fields, to_field_name
from api.cpt import get_existing_cpt_posts
from schema.builder import get_cpt_slug
import re


def get_relationship_field_name(section_name):
    """
    Derives the relationship field name from section name.
    Matches the logic in schema/builder.py build_cpt_schema().
    '4. Team Section' → 'team_posts'
    '3. Services Section' → 'service_posts'
    """
    name = re.sub(r'^\d+\.\s*', '', section_name)
    name = name.replace(" Section", "").replace(" section", "")
    name = to_field_name(name)
    return f"{name}_posts"


def link_relationship_field(client, page_id, field_name, post_ids):
    """
    Links CPT posts to a page via ACF relationship field.

    Args:
        client:     WPClient instance
        page_id:    WordPress page ID (homepage = 5)
        field_name: ACF relationship field name e.g. 'team_posts'
        post_ids:   list of CPT post IDs to link e.g. [68, 69, 70]

    Returns True on success, False on failure.
    """
    fields_dict = {field_name: post_ids}
    success = update_post_acf_fields(client, page_id, fields_dict)

    if success:
        print(f"[OK] Linked {len(post_ids)} posts to {field_name}")
    return success


def link_all_relationships(client, parsed_output, page_id=5):
    """
    Links all CPT sections to the page via relationship fields.
    Fetches current CPT post IDs from WordPress — no hardcoding.

    Args:
        client:        WPClient instance
        parsed_output: full dict from parse_document()
        page_id:       WordPress page ID (default: 5)

    Returns dict of results per section.
    """
    results = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "cpt":
            continue

        cpt_slug       = get_cpt_slug(section_name)
        field_name     = get_relationship_field_name(section_name)

        print(f"\n[RELATIONSHIP] {section_name}")
        print(f"  CPT slug:    {cpt_slug}")
        print(f"  Field name:  {field_name}")

        # Fetch current post IDs from WordPress
        existing = get_existing_cpt_posts(client, cpt_slug)
        if not existing:
            print(f"  [SKIP] No {cpt_slug} posts found in WordPress")
            results[section_name] = "SKIPPED"
            continue

        post_ids = list(existing.values())
        print(f"  Post IDs:    {post_ids}")

        success = link_relationship_field(client, page_id, field_name, post_ids)
        results[section_name] = "OK" if success else "FAIL"

    return results


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result  = parse_document("TechArk-Content-Document.docx")
    results = link_all_relationships(client, result, page_id=5)

    print("\n--- Relationship summary ---")
    for section, status in results.items():
        print(f"  [{status}] {section}")