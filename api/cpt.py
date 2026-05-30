# api/cpt.py
from api.content import update_post_acf_fields, get_post_acf_fields, to_field_name


def create_cpt_post(client, post_type, title):
    """
    Creates a single CPT post in WordPress.
    Returns the post ID on success, None on failure.

    Args:
        client:    WPClient instance
        post_type: CPT slug e.g. 'team_member', 'service'
        title:     Post title e.g. 'Priya Sharma'
    """
    payload  = {"title": title, "status": "publish"}
    response = client.post(f"wp/v2/{post_type}", payload)

    if response.status_code == 201:
        post_id = response.json().get("id")
        print(f"[OK] Created {post_type}: '{title}' (ID: {post_id})")
        return post_id
    else:
        print(f"[ERROR] Failed to create {post_type}: '{title}'")
        print(f"[ERROR] Status: {response.status_code}")
        print(f"[ERROR] Response: {response.text[:300]}")
        return None


def push_cpt_acf_fields(client, post_type, post_id, acf_fields):
    """
    Pushes ACF fields to a CPT post.
    Skips image fields — require media upload.

    Args:
        client:     WPClient instance
        post_type:  CPT slug
        post_id:    WordPress post ID
        acf_fields: list of {label, value, acf_type} dicts
    """
    fields_dict = {}
    for f in acf_fields:
        if f["acf_type"] == "image":
            continue
        name = to_field_name(f["label"])
        fields_dict[name] = f["value"]

    if not fields_dict:
        print(f"  [SKIP] No non-image fields to push")
        return False

    return update_post_acf_fields(client, post_id, fields_dict, post_type)


def get_existing_cpt_posts(client, post_type):
    """
    Fetches existing CPT posts for idempotency check.
    Returns dict of {title: post_id}.
    """
    response = client.get(f"wp/v2/{post_type}?per_page=100&status=publish")

    if response.status_code == 200:
        posts = response.json()
        return {p["title"]["rendered"]: p["id"] for p in posts}
    else:
        print(f"[ERROR] Failed to fetch {post_type} posts: {response.status_code}")
        return {}


def create_all_cpt_posts(client, parsed_output):
    """
    Creates all CPT posts for cpt-type sections.
    Idempotent — skips posts that already exist by title.

    Returns dict of {post_type: {title: post_id}}.
    """
    from schema.builder import get_cpt_slug

    all_post_ids = {}

    for section_name, data in parsed_output.items():
        if data["type"] != "cpt":
            continue

        entries  = data["entries"]
        cpt_slug = get_cpt_slug(section_name)

        print(f"\n[CPT] {section_name} → post_type: {cpt_slug}")

        # Fetch existing posts for idempotency
        existing = get_existing_cpt_posts(client, cpt_slug)
        print(f"[CPT] Found {len(existing)} existing {cpt_slug} posts")

        post_ids = {}

        for entry in entries:
            title = entry["post_title"]
            if not title:
                print(f"  [SKIP] Entry with no post_title")
                continue

            # Idempotency check
            if title in existing:
                post_id = existing[title]
                print(f"  [SKIP] Already exists: '{title}' (ID: {post_id})")
                post_ids[title] = post_id
            else:
                post_id = create_cpt_post(client, cpt_slug, title)
                if post_id:
                    post_ids[title] = post_id

            # Push ACF fields regardless of whether post was new or existing
            if title in post_ids:
                push_cpt_acf_fields(
                    client, cpt_slug, post_ids[title], entry["acf_fields"]
                )

        all_post_ids[cpt_slug] = post_ids

    return all_post_ids


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result   = parse_document("TechArk-Content-Document.docx")
    post_ids = create_all_cpt_posts(client, result)

    print("\n--- CPT post IDs ---")
    for cpt_slug, posts in post_ids.items():
        print(f"\n  {cpt_slug}:")
        for title, pid in posts.items():
            print(f"    {pid}: {title}")