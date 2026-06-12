# validator/validator.py
import csv
import os
from api.content import get_post_acf_fields, to_field_name
from api.options import get_options_fields


def validate_flat_section(client, section_name, fields, page_id=5):
    """
    Validates flat field group section values against source document.
    Uses prefixed field names to match what was pushed.
    Returns list of result dicts.
    """
    results = []
    acf = get_post_acf_fields(client, page_id) or {}

    for f in fields:
        if f["acf_type"] == "image":
            continue
        if f["acf_type"] == "gallery":
            # Validate count instead of value
            name   = to_field_name(f["label"], section_name)
            actual = acf.get(name, [])
            expected_count = f["value"].count("File:")
            actual_count   = len(actual) if isinstance(actual, list) else 0
            status = "PASS" if actual_count == expected_count else "FAIL"
            results.append({
                "section":  section_name,
                "type":     "field_group",
                "field":    name,
                "expected": f"{expected_count} images",
                "actual":   f"{actual_count} images",
                "status":   status,
            })
            continue
        # Use prefixed name — matches what push_flat_sections() pushed
        name     = to_field_name(f["label"], section_name)
        expected = f["value"].strip()
        actual   = str(acf.get(name, "")).strip()

        if not actual:
            status = "EMPTY"
        elif expected == actual:
            status = "PASS"
        else:
            status = "FAIL"

        results.append({
            "section":  section_name,
            "type":     "field_group",
            "field":    name,
            "expected": expected[:80],
            "actual":   actual[:80],
            "status":   status,
        })

    return results


def validate_repeater_section(client, section_name, items, page_id=5):
    """
    Validates repeater section row count against source document.
    Returns one result dict per repeater.
    """
    import re

    field_name = to_field_name(
        re.sub(r'^\d+\.\s*', '', section_name)
           .replace(" Section", "")
    )

    acf            = get_post_acf_fields(client, page_id) or {}
    actual_rows    = acf.get(field_name, [])
    actual_count   = len(actual_rows) if isinstance(actual_rows, list) else 0
    expected_count = len(items)

    status = "PASS" if actual_count == expected_count else "FAIL"

    return [{
        "section":  section_name,
        "type":     "repeater",
        "field":    field_name,
        "expected": str(expected_count) + " rows",
        "actual":   str(actual_count) + " rows",
        "status":   status,
    }]


def validate_cpt_section(client, section_name, entries):
    """
    Validates CPT post count against source document.
    Returns one result dict per CPT.
    """
    from schema.builder import get_cpt_slug
    from api.cpt import get_existing_cpt_posts

    cpt_slug       = get_cpt_slug(section_name)
    existing       = get_existing_cpt_posts(client, cpt_slug)
    actual_count   = len(existing)
    expected_count = len(entries)

    status = "PASS" if actual_count == expected_count else "FAIL"

    return [{
        "section":  section_name,
        "type":     "cpt",
        "field":    cpt_slug,
        "expected": str(expected_count) + " posts",
        "actual":   str(actual_count) + " posts",
        "status":   status,
    }]


def validate_options_section(client, section_name, fields):
    """
    Validates options page field values against source document.
    Uses prefixed field names to match what was pushed.
    Returns list of result dicts.
    """
    results = []
    options = get_options_fields(client) or {}

    for f in fields:
        if f["acf_type"] == "image":
            continue
        # Use prefixed name — matches what push_all_options_sections() pushed
        name     = to_field_name(f["label"], section_name)
        expected = f["value"].strip()
        actual   = str(options.get(name, "")).strip()

        if not actual:
            status = "EMPTY"
        elif expected == actual:
            status = "PASS"
        else:
            status = "FAIL"

        results.append({
            "section":  section_name,
            "type":     "options_page",
            "field":    name,
            "expected": expected[:80],
            "actual":   actual[:80],
            "status":   status,
        })

    return results


def run_validation(client, parsed_output, page_id, output_dir="output"):
    """
    Runs full validation across all sections.
    Saves results to output/validation_report.csv.
    Returns list of all result dicts.
    """
    all_results = []

    print("\n[VALIDATION] Starting validation...")

    for section_name, data in parsed_output.items():
        section_type = data["type"]

        if section_type == "field_group":
            results = validate_flat_section(
                client, section_name, data["fields"], page_id
            )
        elif section_type == "repeater":
            if not data["items"]:
                continue
            results = validate_repeater_section(
                client, section_name, data["items"], page_id
            )
        elif section_type == "cpt":
            results = validate_cpt_section(
                client, section_name, data["entries"]
            )
        elif section_type == "options_page":
            results = validate_options_section(
                client, section_name, data["fields"]
            )
        else:
            continue

        for r in results:
            icon = "✓" if r["status"] == "PASS" else ("~" if r["status"] == "EMPTY" else "✗")
            print(f"  [{icon}] {r['section']} — {r['field']}: {r['status']}")

        all_results.extend(results)

    # Save report
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "validation_report.csv")
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["section", "type", "field", "expected", "actual", "status"]
        )
        writer.writeheader()
        writer.writerows(all_results)

    # Summary
    total  = len(all_results)
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    failed = sum(1 for r in all_results if r["status"] == "FAIL")
    empty  = sum(1 for r in all_results if r["status"] == "EMPTY")
    rate   = round(passed / total * 100) if total > 0 else 0

    print(f"\n[VALIDATION] Report saved to: {report_path}")
    print(f"[VALIDATION] Total: {total} | Pass: {passed} | Fail: {failed} | Empty: {empty}")
    print(f"[VALIDATION] Pass rate: {rate}%")

    return all_results


if __name__ == "__main__":
    import config
    from api.client import WPClient
    from parser.parser import parse_document

    client = WPClient(config.WP_URL, config.WP_USER, config.WP_PASSWORD)

    if not client.test_connection():
        exit(1)

    result = parse_document("TechArk-Content-Document.docx")
    run_validation(client, result, page_id=config.PAGE_ID)