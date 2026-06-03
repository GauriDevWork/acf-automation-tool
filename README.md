# ACF Automation Tool

A Python CLI that reads a client `.docx` content document, classifies each section into ACF field types, generates importable ACF field group JSON, pushes all content to WordPress via the REST API, then validates every field landed correctly.

---

## What it does

1. **Parses** a `.docx` content brief — extracts all sections, field labels, values, and infers ACF field types automatically
2. **Classifies** each section as field group, repeater, CPT, or options page
3. **Generates** ACF-importable `schema.json` with all field group definitions
4. **Pushes** all content to WordPress via REST API — flat fields, repeaters, CPT posts, relationship links, options page
5. **Validates** every pushed field against the source document — outputs `validation_report.csv`

---

## Installation

```bash
git clone https://github.com/GauriDevWork/acf-automation-tool.git
cd acf-automation-tool
pip install -r requirements.txt
```

Copy `config.example.py` to `config.py` and add your WordPress credentials:

```python
WP_URL      = "http://your-site.local"
WP_USER     = "admin"
WP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"
```

---

## WordPress Setup

See [docs/wordpress-setup.md](docs/wordpress-setup.md) for full setup instructions including:
- ACF Pro installation
- Schema import via ACF → Tools → Import
- Enabling ACF REST API in functions.php
- Creating Application Passwords

---

## Usage

**Dry run — parse and generate schema only, no WordPress writes:**
```bash
python main.py --input TechArk-Content-Document.docx --dry-run
```

**Full pipeline — parse, push, validate:**
```bash
python main.py --input TechArk-Content-Document.docx --phase all
```

**Schema only:**
```bash
python main.py --input TechArk-Content-Document.docx --phase schema
```

**Validate only:**
```bash
python main.py --input TechArk-Content-Document.docx --phase validate
```

**Override WordPress credentials:**
```bash
python main.py --input content.docx --url http://site.local --user admin --password "xxxx xxxx"
```

---

## CLI Flags

| Flag | Description | Default |
|---|---|---|
| `--input` | Path to .docx content document | required |
| `--url` | WordPress site URL | from config.py |
| `--user` | WordPress username | from config.py |
| `--password` | Application Password | from config.py |
| `--phase` | schema / push / validate / all | all |
| `--dry-run` | Parse + schema only, no WP writes | false |
| `--output-dir` | Directory for output files | output/ |

---

## Sample Output

```
============================================================
ACF AUTOMATION TOOL — FULL PIPELINE RUN
============================================================
[STEP 1/5] Pushing flat field sections...
[STEP 2/5] Pushing repeater sections...
[STEP 3/5] Creating CPT posts...
[STEP 4/5] Linking relationship fields...
[STEP 5/5] Pushing options page sections...
============================================================
PIPELINE COMPLETE — SUMMARY
============================================================
Total: 18/18 passed

[VALIDATION] Pass rate: 96%
```

---

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for design decisions including:
- Why Python CLI over a WordPress plugin
- CPT vs repeater classification logic
- Two-pass parser design
- Idempotent API calls

---

## Running Tests

```bash
pytest tests/ -v
```

112 tests passing across parser, schema builder, and API client modules.

---

## Known Limitations (v1.0)

- Image fields are skipped — media upload requires separate workflow
- Stats section (table-based) is not parsed — known limitation
- Field name collision when two sections share the same field name
- Relationship fields require manual field group creation in WP Admin

---

## Project Structure

```
acf-automation-tool/
├── parser/          # Document parsing — loader, grouper, classifier, extractor, mapper
├── schema/          # ACF JSON generation — builder, output
├── api/             # WordPress REST API — client, content, cpt, relationships, options, orchestrator
├── validator/       # Validation layer — field value comparison, report.csv
├── tests/           # 112 unit and integration tests
├── docs/            # WordPress setup guide
├── output/          # Generated files (gitignored) — schema.json, report.csv
├── main.py          # CLI entry point
└── config.py        # Credentials (gitignored)
```

---

*Built by Gauri — TechArk Solutions | Q2 2026*