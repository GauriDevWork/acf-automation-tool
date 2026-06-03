# Architecture Decisions

## Why Python CLI over a WordPress Plugin

A plugin couples the tool to one WordPress install — Python CLI runs anywhere. It can be triggered from CI/CD, Basecamp automation, or a cron job. No WP admin access required to run — works from terminal. Readable in a code review without needing WordPress context.

## Two-Pass Parser

The document parser runs in two passes:
1. **Pass 1** — groups paragraphs into named sections by Heading 1 boundaries
2. **Pass 2** — extracts fields, classifies types, and structures data per section type

This separation keeps the grouper and extractor independent. The grouper does not need to know about field types. The extractor does not need to know about document structure.

## CPT vs Repeater Decision

- **CPT**: entity needs its own URL, admin filtering, or appears on multiple pages
- **Repeater**: data is display-only and local to one page

Examples: Team = CPT (single member pages, filter by department). Testimonials = Repeater (no identity beyond the carousel). The parser detects [CPT] annotations first, then falls back to keyword heuristics.

## Idempotent Keys

All ACF field keys are generated using MD5 hash of section_name + label. Same document run twice produces identical keys. The tool is safe to run multiple times without creating duplicate field groups.

## Idempotent API Calls

CPT post creation checks for existing posts by title before creating. If a post with the same title exists, it skips creation and only updates the ACF fields. Safe to run against a populated WordPress install.

## ACF Pro 6.x Compatibility

ACF Pro 6.x removed the acf/v3 REST API namespace. The tool adapted to use standard wp/v2 endpoints with show_in_rest filters, and a custom acf-tool/v1/options endpoint for options page fields.

## Field Type Detection

Field types are inferred from value patterns in fixed priority order:
1. URL (starts with / or http)
2. Image (contains image extension, under 120 chars)
3. Email (contains @)
4. Number (pure digits)
5. True/False (yes/no/true/false)
6. Wysiwyg (label contains answer/bio/description)
7. Textarea (over 100 characters)
8. Text (default fallback)

Order matters — specific patterns checked before generic length-based fallbacks.