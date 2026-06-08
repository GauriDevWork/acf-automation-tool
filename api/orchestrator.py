# api/orchestrator.py
import json


def run_all(client, parsed_output, page_id=5):
    """
    Full pipeline orchestrator — runs all API push steps in correct order.

    Order matters:
    1. Push flat field sections (Hero, CTA Banner, Gallery)
    2. Push repeater sections (FAQ, Testimonials, Partner Logos)
    3. Create CPT posts (Team, Services)
    4. Link relationship fields (team_posts, services_posts)
    5. Push options page sections (Global Header, Global Footer)

    Args:
        client:        WPClient instance
        parsed_output: full dict from parse_document()
        page_id:       WordPress page ID (default: 5)

    Returns summary dict of all results.
    """
    from api.content import push_flat_sections, push_repeater_sections
    from api.cpt import create_all_cpt_posts
    from api.relationships import link_all_relationships
    from api.options import push_all_options_sections

    summary = {}

    print("\n" + "="*60)
    print("ACF AUTOMATION TOOL — FULL PIPELINE RUN")
    print("="*60)

    # Step 1 — Flat field groups
    print("\n[STEP 1/6] Pushing flat field sections...")
    flat_results = push_flat_sections(client, parsed_output, page_id)
    summary["flat_sections"] = flat_results

    # Step 2 — Repeater sections
    print("\n[STEP 2/6] Pushing repeater sections...")
    repeater_results = push_repeater_sections(client, parsed_output, page_id)
    summary["repeater_sections"] = repeater_results

    # Step 3 — CPT posts
    print("\n[STEP 3/6] Creating CPT posts...")
    cpt_results = create_all_cpt_posts(client, parsed_output)
    summary["cpt_posts"] = cpt_results

    # Step 4 — Relationship fields
    print("\n[STEP 4/6] Linking relationship fields...")
    rel_results = link_all_relationships(client, parsed_output, page_id)
    summary["relationships"] = rel_results

    # Step 5 — Options page
    print("\n[STEP 5/6] Pushing options page sections...")
    options_results = push_all_options_sections(client, parsed_output)
    summary["options_sections"] = options_results

    # Step 6 — Image upload
    print("\n[STEP 6/6] Uploading images...")
    from api.media import push_image_fields
    image_results = push_image_fields(client, parsed_output, images_dir="images")
    summary["image_fields"] = image_results

    # Print final summary
    print("\n" + "="*60)
    print("PIPELINE COMPLETE — SUMMARY")
    print("="*60)

    total  = 0
    passed = 0

    for step, results in summary.items():
        if isinstance(results, dict):
            for section, status in results.items():
                if isinstance(status, dict):
                    # CPT results are nested dicts
                    for title, pid in status.items():
                        total  += 1
                        passed += 1
                        print(f"  [OK] {title} (ID: {pid})")
                else:
                    total += 1
                    if status in ("OK", "SKIPPED"):
                        passed += 1
                    print(f"  [{status}] {section}")

    print(f"\nTotal: {passed}/{total} passed")
    return summary


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result = parse_document("TechArk-Content-Document.docx")
    run_all(client, result, page_id=5)