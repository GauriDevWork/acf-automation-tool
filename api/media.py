# api/media.py
import os
import mimetypes
import requests


def get_mime_type(file_path):
    """
    Returns the MIME type for a file based on its extension.
    Defaults to image/jpeg for unknown types.
    """
    mime, _ = mimetypes.guess_type(file_path)
    if mime:
        return mime
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".svg":  "image/svg+xml",
        ".gif":  "image/gif",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "image/jpeg")


def extract_filename(raw_value):
    """
    Extracts just the filename from an image field value.
    Handles:
    - Plain filename:       "hero-bg.jpg"
    - File: prefix:         "File: hero-bg.jpg"
    - Multi-line with Alt:  "File: hero-bg.jpg\nAlt text: ..."
    - Pipe-separated:       "hero-bg.jpg | Alt: some text"
    """
    if not raw_value:
        return ""

    first_line = raw_value.split("\n")[0].strip()

    if "|" in first_line:
        first_line = first_line.split("|")[0].strip()

    if ":" in first_line:
        label, _, value = first_line.partition(":")
        if label.strip().lower() in ("file", "filename", "image"):
            first_line = value.strip()

    return first_line.strip()


def convert_svg_to_png(svg_path):
    """
    Converts SVG to PNG for WordPress upload compatibility.
    WordPress blocks SVG uploads by default — PNG is universally accepted.
    Returns path to the PNG file.
    """
    png_path = svg_path.replace(".svg", ".png")
    if os.path.exists(png_path):
        return png_path

    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path)
        print(f"  [CONVERT] {os.path.basename(svg_path)} → PNG")
        return png_path
    except ImportError:
        pass

    try:
        from PIL import Image, ImageDraw
        img  = Image.new("RGB", (200, 80), color=(31, 56, 100))
        d    = ImageDraw.Draw(img)
        name = os.path.basename(svg_path).replace(
            "-logo.svg", "").replace("-", " ").title()
        d.text((10, 30), name, fill=(255, 255, 255))
        img.save(png_path)
        print(f"  [CONVERT] {os.path.basename(svg_path)} → PNG (placeholder)")
        return png_path
    except ImportError:
        pass

    import shutil
    shutil.copy(svg_path, png_path)
    return png_path


def upload_image(client, file_path):
    """
    Uploads an image file to WordPress Media Library.
    Converts SVG to PNG automatically.
    Returns the attachment ID (integer) on success, None on failure.
    """
    if not os.path.exists(file_path):
        print(f"  [SKIP] Image not found: {file_path}")
        return None

    if file_path.lower().endswith(".svg"):
        file_path = convert_svg_to_png(file_path)

    filename  = os.path.basename(file_path)
    mime_type = get_mime_type(file_path)

    print(f"  [UPLOAD] {filename} ({mime_type})")

    with open(file_path, "rb") as f:
        file_data = f.read()

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Content-Type":        mime_type,
    }

    url      = f"{client.base_url}/wp-json/wp/v2/media"
    response = requests.post(
        url,
        data=file_data,
        headers=headers,
        auth=client.auth,
    )

    if response.status_code == 201:
        attachment_id = response.json().get("id")
        print(f"  [OK] Uploaded: {filename} (ID: {attachment_id})")
        return attachment_id
    else:
        print(f"  [ERROR] Failed to upload: {filename}")
        print(f"  [ERROR] Status: {response.status_code}")
        print(f"  [ERROR] Response: {response.text[:200]}")
        return None


def get_existing_media(client, filename):
    """
    Checks if a media file with the given filename already exists.
    Returns attachment ID if found, None if not.
    """
    if filename.lower().endswith(".svg"):
        filename = filename.replace(".svg", ".png")

    search   = os.path.splitext(filename)[0]
    response = client.get(f"wp/v2/media?search={search}&per_page=10")

    if response.status_code == 200:
        media_items = response.json()
        for item in media_items:
            source_url = item.get("source_url", "")
            if filename in source_url:
                print(f"  [SKIP] Already uploaded: {filename} (ID: {item['id']})")
                return item["id"]
    return None


def upload_image_idempotent(client, file_path):
    """
    Uploads image only if not already in WordPress Media Library.
    Returns attachment ID on success, None on failure.
    """
    filename = os.path.basename(file_path)
    existing = get_existing_media(client, filename)
    if existing:
        return existing
    return upload_image(client, file_path)


def push_gallery_field(client, field_name, gallery_value,
                       images_dir="images", page_id=5):
    """
    Handles ACF gallery field — uploads multiple images and pushes
    array of attachment IDs.

    ACF gallery field REST API format:
        {"acf": {"field_name": [101, 102, 103, 104, 105, 106]}}
    """
    from api.content import update_post_acf_fields

    attachment_ids = []

    for line in gallery_value.split("\n"):
        line = line.strip()
        if not line or "File:" not in line:
            continue

        after_file = line.split("File:")[1]
        filename   = after_file.split("|")[0].strip()

        if not filename:
            continue

        file_path = os.path.join(images_dir, filename)
        att_id    = upload_image_idempotent(client, file_path)
        if att_id:
            attachment_ids.append(att_id)
            print(f"  [GALLERY] {filename} → ID {att_id}")

    if attachment_ids:
        # Try array format first (ACF Pro 6.x)
        success = update_post_acf_fields(
            client, page_id, {field_name: attachment_ids}
        )
        if not success:
            # Fallback — comma separated string
            update_post_acf_fields(
                client, page_id,
                {field_name: ",".join(str(i) for i in attachment_ids)}
            )
        print(f"  [OK] Gallery '{field_name}' — {len(attachment_ids)} images")

    return attachment_ids


def push_image_fields(client, parsed_output, images_dir="images", page_id=5):
    """
    Finds all image fields across all sections and pushes them to WordPress.
    Handles flat image fields, CPT image fields, repeater image sub-fields,
    and ACF gallery fields.

    Returns list of result dicts.
    """
    from api.content import update_post_acf_fields, to_field_name, get_post_acf_fields
    from schema.builder import get_cpt_slug
    from api.cpt import get_existing_cpt_posts
    import re

    results = []

    for section_name, data in parsed_output.items():
        section_type = data["type"]

        # ── Flat field groups ──────────────────────────────────────────────
        if section_type == "field_group":
            fields = data["fields"]

            # Regular image fields
            image_fields = [f for f in fields if f["acf_type"] == "image"]
            if image_fields:
                print(f"\n[IMAGE] {section_name}")
                fields_dict = {}
                for f in image_fields:
                    filename  = extract_filename(f["value"])
                    if not filename:
                        continue
                    file_path = os.path.join(images_dir, filename)
                    att_id    = upload_image_idempotent(client, file_path)
                    if att_id:
                        name = to_field_name(f["label"], section_name)
                        fields_dict[name] = att_id
                        results.append({
                            "section":       section_name,
                            "field":         name,
                            "filename":      filename,
                            "attachment_id": att_id,
                        })
                if fields_dict:
                    update_post_acf_fields(client, page_id, fields_dict)

            # ACF gallery fields
            gallery_fields = [f for f in fields if f["acf_type"] == "gallery"]
            if gallery_fields:
                print(f"\n[GALLERY] {section_name}")
                for f in gallery_fields:
                    name = to_field_name(f["label"], section_name)
                    ids  = push_gallery_field(
                        client, name, f["value"],
                        images_dir=images_dir, page_id=page_id
                    )
                    for i, att_id in enumerate(ids):
                        results.append({
                            "section":       section_name,
                            "field":         f"{name}[{i}]",
                            "filename":      f"gallery image {i+1}",
                            "attachment_id": att_id,
                        })

        # ── CPT posts ──────────────────────────────────────────────────────
        elif section_type == "cpt":
            entries  = data["entries"]
            cpt_slug = get_cpt_slug(section_name)
            existing = get_existing_cpt_posts(client, cpt_slug)

            print(f"\n[IMAGE] {section_name} — CPT: {cpt_slug}")

            for entry in entries:
                title   = entry["post_title"]
                post_id = existing.get(title)
                if not post_id:
                    continue

                image_fields = [f for f in entry["acf_fields"]
                                if f["acf_type"] == "image"]
                if not image_fields:
                    continue

                fields_dict = {}
                for f in image_fields:
                    filename  = extract_filename(f["value"])
                    if not filename:
                        continue
                    file_path = os.path.join(images_dir, filename)
                    att_id    = upload_image_idempotent(client, file_path)
                    if att_id:
                        name = to_field_name(f["label"], section_name)
                        fields_dict[name] = att_id
                        results.append({
                            "section":       section_name,
                            "post":          title,
                            "field":         name,
                            "filename":      filename,
                            "attachment_id": att_id,
                        })

                if fields_dict:
                    update_post_acf_fields(
                        client, post_id, fields_dict, post_type=cpt_slug
                    )

        # ── Repeater sections ──────────────────────────────────────────────
        elif section_type == "repeater":
            items = data["items"]
            has_images = any(
                sf["acf_type"] == "image"
                for item in items
                for sf in item["sub_fields"]
            )
            if not has_images:
                continue

            print(f"\n[IMAGE] {section_name} — repeater")

            field_name = to_field_name(
                re.sub(r'^\d+\.\s*', '', section_name)
                   .replace(" Section", "")
            )

            acf  = get_post_acf_fields(client, page_id) or {}
            rows = acf.get(field_name, [])

            for i, item in enumerate(items):
                if i >= len(rows):
                    break
                for sf in item["sub_fields"]:
                    if sf["acf_type"] != "image":
                        continue
                    filename  = extract_filename(sf["value"])
                    if not filename:
                        continue
                    file_path = os.path.join(images_dir, filename)
                    att_id    = upload_image_idempotent(client, file_path)
                    if att_id:
                        sub_name      = to_field_name(sf["label"])
                        rows[i][sub_name] = att_id
                        update_post_acf_fields(
                            client, page_id, {field_name: rows}
                        )
                        results.append({
                            "section":       section_name,
                            "row":           i,
                            "field":         sub_name,
                            "filename":      filename,
                            "attachment_id": att_id,
                        })

    return results


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result = parse_document("TechArk-Content-Document.docx")
    pushed = push_image_fields(client, result, images_dir="images", page_id=5)

    print(f"\n--- Image upload summary ---")
    print(f"Total images pushed: {len(pushed)}")
    for item in pushed:
        if "post" in item:
            print(f"  [{item['section']}] {item['post']} → {item['field']}: ID {item['attachment_id']}")
        elif "row" in item:
            print(f"  [{item['section']}] row {item['row']} → {item['field']}: ID {item['attachment_id']}")
        else:
            print(f"  [{item['section']}] {item['field']}: ID {item['attachment_id']}")