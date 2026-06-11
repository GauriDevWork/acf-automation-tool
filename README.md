# ACF Automation Tool

A Python CLI and Streamlit web app that reads a client `.docx` content document, classifies each section into ACF field types, generates importable ACF field group JSON, pushes all content to WordPress via the REST API — including images, gallery fields, repeaters, CPTs, and options page — then validates every field landed correctly.

**Live demo:** [acf-automation-tool.streamlit.app](https://acf-automation-tool-3uh3fcx7a943s3vwi9avtf.streamlit.app/)
**Demo site:** [acf-demo.webtechee.me](https://acf-demo.webtechee.me)

## Live Demo

[Try it live →](https://acf-automation-tool-3uh3fcx7a943s3vwi9avtf.streamlit.app)

Upload a `.docx` content document to see parse and schema generation in action.
Full WordPress push requires a connected WordPress instance.

---

## What it does

1. **Parses** a `.docx` content brief — extracts all sections, field labels, values, and infers ACF field types automatically including gallery detection
2. **Classifies** each section as field group, repeater, CPT, or options page — handles table-based sections too
3. **Generates** ACF-importable `schema.json` with 12 field groups — `show_in_rest` baked in, no manual WP Admin step
4. **Pushes** all content to WordPress via REST API in 6 steps — flat fields, repeaters, CPT posts, relationship links, options page, images
5. **Uploads** images to WordPress Media Library — JPG, PNG, SVG (auto-converted to PNG), gallery arrays
6. **Validates** every pushed field against the source document — outputs `validation_report.csv`

**Current result: 30/30 checks passing — 100% pass rate**

---

## Quick Start — Web UI

Open the live Streamlit demo, upload your `.docx`, enter WordPress credentials, enter your page ID, and click Run:

[https://acf-automation-tool-3uh3fcx7a943s3vwi9avtf.streamlit.app/](https://acf-automation-tool-3uh3fcx7a943s3vwi9avtf.streamlit.app/)

No installation required.

---

## Installation — CLI

```bash
git clone https://github.com/GauriDevWork/acf-automation-tool.git
cd acf-automation-tool
pip install -r requirements.txt
```

Copy `config.example.py` to `config.py` and fill in your details:

```python
WP_URL      = "https://your-site.com"   # must be HTTPS on live sites
WP_USER     = "admin"
WP_PASSWORD = "xxxx xxxx xxxx xxxx xxxx xxxx"
PAGE_ID     = 5    # WordPress page ID to push content to — check WP Admin URL
```

---

## WordPress Setup

The tool requires:

1. **ACF Pro** installed and activated
2. **functions.php additions** — registers CPTs, custom options REST endpoint, and ACF Options Page. See the snippet below or `docs/wordpress-setup.md`
3. **Schema imported** — run `--dry-run` to generate `output/schema.json`, then import via ACF → Tools → Import
4. **Application Password** — WP Admin → Users → Profile → Application Passwords → Add New
5. **Permalinks set to Post Name** — Settings → Permalinks → Post Name → Save (required for REST API)

```php
// Paste at the bottom of your active theme's functions.php
function acf_tool_register_cpts() {
    register_post_type( 'team_member', [
        'label' => 'Team Members', 'public' => true,
        'supports' => ['title','thumbnail','excerpt'], 'show_in_rest' => true,
    ]);
    register_post_type( 'service', [
        'label' => 'Services', 'public' => true,
        'supports' => ['title','thumbnail','excerpt'], 'show_in_rest' => true,
    ]);
}
add_action( 'init', 'acf_tool_register_cpts' );

add_action( 'rest_api_init', function () {
    register_rest_route( 'acf-tool/v1', '/options', [
        'methods' => ['GET','POST'],
        'callback' => function($request) {
            if ($request->get_method() === 'POST') {
                foreach ($request->get_json_params() as $key => $value)
                    update_field($key, $value, 'option');
                return rest_ensure_response(['status' => 'updated']);
            }
            return rest_ensure_response(get_fields('option') ?: []);
        },
        'permission_callback' => function() { return current_user_can('manage_options'); },
    ]);
});

if (function_exists('acf_add_options_page')) {
    acf_add_options_page(['page_title' => 'Theme Options', 'menu_slug' => 'acf-options']);
}
```

---

## Usage

**Dry run — parse and generate schema only, no WordPress writes:**
```bash
python main.py --input TechArk-Content-Document.docx --dry-run
```

**Full pipeline — parse, push all content, validate:**
```bash
python main.py --input TechArk-Content-Document.docx --phase all
```

**Specify page ID (if homepage is not ID 5):**
```bash
python main.py --input TechArk-Content-Document.docx --page-id 76
```

**Schema only:**
```bash
python main.py --input TechArk-Content-Document.docx --phase schema
```

**Validate only:**
```bash
python main.py --input TechArk-Content-Document.docx --phase validate
```

**Override WordPress credentials at runtime:**
```bash
python main.py --input content.docx --url https://site.com --user admin --password "xxxx xxxx" --page-id 76
```

**Run Streamlit locally:**
```bash
streamlit run streamlit_app.py
```

---

## CLI Flags

| Flag | Description | Default |
|---|---|---|
| `--input` | Path to .docx content document | required |
| `--url` | WordPress site URL | from config.py |
| `--user` | WordPress username | from config.py |
| `--password` | Application Password | from config.py |
| `--page-id` | WordPress page ID to push content to | from config.py |
| `--phase` | schema / push / validate / all | all |
| `--dry-run` | Parse + schema only, no WP writes | false |
| `--output-dir` | Directory for output files | output/ |

---

## Pipeline Steps

```
============================================================
ACF AUTOMATION TOOL — FULL PIPELINE RUN
============================================================
[STEP 1/6] Pushing flat field sections...
[STEP 2/6] Pushing repeater sections...
[STEP 3/6] Creating CPT posts...
[STEP 4/6] Linking relationship fields...
[STEP 5/6] Pushing options page sections...
[STEP 6/6] Uploading images...
============================================================
PIPELINE COMPLETE — SUMMARY
============================================================
Total: 18/18 passed

[VALIDATION] Total: 30 | Pass: 30 | Fail: 0 | Empty: 0
[VALIDATION] Pass rate: 100%
```

---

## What It Handles

| Content type | How |
|---|---|
| Flat field groups | Hero, CTA Banner, Gallery — pushed to specified page |
| Repeater fields | FAQ, Testimonials, Stats, Partner Logos — rows with sub-fields |
| Custom Post Types | Team Members and Services — individual posts with ACF fields |
| Relationship fields | CPT posts linked back to page via ACF relationship field |
| Options page | Global Header and Footer via custom REST endpoint |
| Image fields | Uploaded to Media Library, attachment ID pushed to ACF |
| Gallery field | Multiple images uploaded, array of IDs pushed |
| Table-based content | Stats section parsed from .docx table rows |
| SVG files | Auto-converted to PNG for WordPress compatibility |

---

## Architecture Decisions

**Why Python CLI over a WordPress plugin?**
A plugin couples the tool to one WordPress install. Python CLI runs anywhere — CI/CD, cron job, or terminal. No WP admin access required to run.

**Why CPT vs repeater?**
If an entity needs its own URL, admin filtering, or appears on multiple pages → CPT. If data is display-only and local to one page → repeater. Parser detects `[CPT]` annotations first, falls back to keyword heuristic.

**Why two-pass parser?**
First pass groups paragraphs into sections by Heading 1. Second pass extracts fields per section. Keeps concerns separate and makes each pass testable independently.

**Why idempotent API calls?**
Tool must be safe to run twice. Before creating a CPT post or uploading an image, it checks if it already exists. Skip if found, create if not.

**Why show_in_rest baked into schema?**
ACF Pro 6.x requires `show_in_rest: 1` at the field group level. Baking it into the generated JSON means no manual WP Admin configuration after import.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full decision log.

---

## Running Tests

```bash
pytest tests/ -v
```

**115 tests passing** across parser, schema builder, API client, and validator modules.

---

## Project Structure

```
acf-automation-tool/
├── parser/          # Document parsing — loader, grouper, classifier, extractor, mapper
├── schema/          # ACF JSON generation — builder, output
├── api/             # WordPress REST API — client, content, cpt, relationships, options, media, orchestrator
├── validator/       # Validation — field value comparison, report.csv
├── tests/           # 115 unit and integration tests
├── images/          # Placeholder images for demo
├── docs/            # WordPress setup guide
├── output/          # Generated files (gitignored) — schema.json, report.csv
├── main.py          # CLI entry point with argparse
├── streamlit_app.py # Web UI
└── config.py        # Credentials (gitignored)
```

---

## Versions

| Tag | What shipped |
|---|---|
| v0.5 | CLI + validation + docs |
| v1.1 | Streamlit web UI |
| v1.2 | All limitations fixed — image upload, gallery, stats table, field splits |
| v1.3 | Streamlit Step 6 image upload, validation table colours |
| v1.4 | page_id dynamic via config.py and CLI flag |

---

*Built by Gauri — TechArk Solutions | Q2 2026*