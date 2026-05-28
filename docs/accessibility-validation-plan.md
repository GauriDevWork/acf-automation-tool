# Accessibility Validation — Planned for Phase 5

## Checks to implement (Day 25 or 26)

1. IMAGE FIELDS
   - Every image field must have a companion alt_text field
   - Alt text must be non-empty
   - Alt text must not be generic: "image", "photo", "picture", "img"

2. LINK FIELDS
   - Every url field must have a companion label field
   - Label must be descriptive — flag if it contains "click here", "here", "link"

3. BUTTON LABELS
   - CTA button labels must be descriptive
   - Flag: "Click here", "Read more", "Learn more" without context

4. HEADING HIERARCHY
   - Document must not skip heading levels (H1 → H3 with no H2 is a flag)
   - First heading must be H1

5. COLOR FIELDS
   - Flag all hex color values for manual contrast ratio check
   - Cannot auto-check contrast without knowing background + foreground pair

## Output
   - Add ACCESSIBILITY column to validation_report.csv
   - PASS / FAIL / WARN per field
   - WARN = needs manual review, not automatic fail