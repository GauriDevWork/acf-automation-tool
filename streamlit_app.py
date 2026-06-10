# streamlit_app.py
import streamlit as st
import tempfile
import os
import json

st.set_page_config(
    page_title="ACF Automation Tool",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ ACF Automation Tool")
st.markdown("Convert a client content document into fully populated WordPress ACF fields — including images, repeaters, CPTs, and gallery fields.")

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.header("WordPress Credentials")
wp_url      = st.sidebar.text_input("WordPress URL", placeholder="http://localhost:10046")
wp_user     = st.sidebar.text_input("Username", placeholder="admin")
wp_password = st.sidebar.text_input("Application Password", type="password")

st.sidebar.header("Options")
phase   = st.sidebar.selectbox("Phase", ["all", "schema", "push", "validate"])
dry_run = st.sidebar.checkbox("Dry run (no WordPress writes)")

st.sidebar.markdown("---")
st.sidebar.markdown("**Pipeline steps:**")
st.sidebar.markdown("1. Flat field sections")
st.sidebar.markdown("2. Repeater sections")
st.sidebar.markdown("3. CPT posts")
st.sidebar.markdown("4. Relationship fields")
st.sidebar.markdown("5. Options page")
st.sidebar.markdown("6. Image upload")

# ── Main area ──────────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader(
        "Upload your .docx content document",
        type=["docx"]
    )

with col2:
    st.header("2. Run Pipeline")
    run_btn = st.button("▶ Run", type="primary", disabled=uploaded_file is None)

# ── Pipeline execution ─────────────────────────────────────────────────────
if run_btn and uploaded_file:

    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    try:
        from parser.parser import parse_document
        from schema.output import build_all_schemas

        # ── Parse ──────────────────────────────────────────────────────────
        st.header("3. Results")
        with st.spinner("Parsing document..."):
            parsed = parse_document(tmp_path)

        st.success(f"✅ Parsed {len(parsed)} sections")

        with st.expander("Section Summary", expanded=True):
            summary_data = []
            for name, data in parsed.items():
                t = data["type"]
                if t == "repeater":
                    count = f"{len(data['items'])} items"
                elif t == "cpt":
                    count = f"{len(data['entries'])} entries"
                else:
                    count = f"{len(data['fields'])} fields"
                summary_data.append({"Section": name, "Type": t, "Count": count})
            st.dataframe(summary_data, use_container_width=True)

        # ── Schema ─────────────────────────────────────────────────────────
        with st.spinner("Building schemas..."):
            output_dir = tempfile.mkdtemp()
            schemas    = build_all_schemas(parsed, output_dir=output_dir)

        st.success(f"✅ Generated {len(schemas)} field groups")

        schema_path = os.path.join(output_dir, "schema.json")
        with open(schema_path, encoding="utf-8") as f:
            schema_json = f.read()

        st.download_button(
            label="⬇ Download schema.json",
            data=schema_json,
            file_name="schema.json",
            mime="application/json"
        )

        if dry_run:
            st.info("ℹ Dry run complete — no WordPress writes performed.")
            st.stop()

        # ── WordPress credentials check ────────────────────────────────────
        if not wp_url or not wp_user or not wp_password:
            st.warning("⚠ Enter WordPress credentials in the sidebar to push content.")
            st.stop()

        from api.client import WPClient
        from validator.validator import run_validation

        with st.spinner("Connecting to WordPress..."):
            client    = WPClient(wp_url, wp_user, wp_password)
            connected = client.test_connection()

        if not connected:
            st.error("❌ Cannot connect to WordPress. Check credentials.")
            st.stop()

        st.success("✅ Connected to WordPress")

        # ── Push pipeline ──────────────────────────────────────────────────
        if phase in ("push", "all"):
            progress  = st.progress(0, text="Starting pipeline...")
            log_area  = st.empty()
            log_lines = []

            def log(msg):
                log_lines.append(msg)
                log_area.code("\n".join(log_lines[-20:]))

            # Step 1 — Flat fields
            progress.progress(5, text="[1/6] Pushing flat field sections...")
            log("[STEP 1/6] Pushing flat field sections...")
            from api.content import push_flat_sections
            push_flat_sections(client, parsed)
            log("✅ Step 1 complete")

            # Step 2 — Repeaters
            progress.progress(20, text="[2/6] Pushing repeater sections...")
            log("[STEP 2/6] Pushing repeater sections...")
            from api.content import push_repeater_sections
            push_repeater_sections(client, parsed)
            log("✅ Step 2 complete")

            # Step 3 — CPT posts
            progress.progress(35, text="[3/6] Creating CPT posts...")
            log("[STEP 3/6] Creating CPT posts...")
            from api.cpt import create_all_cpt_posts
            create_all_cpt_posts(client, parsed)
            log("✅ Step 3 complete")

            # Step 4 — Relationships
            progress.progress(50, text="[4/6] Linking relationship fields...")
            log("[STEP 4/6] Linking relationship fields...")
            from api.relationships import link_all_relationships
            link_all_relationships(client, parsed)
            log("✅ Step 4 complete")

            # Step 5 — Options
            progress.progress(65, text="[5/6] Pushing options page sections...")
            log("[STEP 5/6] Pushing options page sections...")
            from api.options import push_all_options_sections
            push_all_options_sections(client, parsed)
            log("✅ Step 5 complete")

            # Step 6 — Images
            progress.progress(80, text="[6/6] Uploading images...")
            log("[STEP 6/6] Uploading images...")
            from api.media import push_image_fields
            image_results = push_image_fields(
                client, parsed, images_dir="images"
            )
            log(f"✅ Step 6 complete — {len(image_results)} images uploaded")

            progress.progress(100, text="Pipeline complete!")
            st.success(f"✅ Pipeline complete — {len(image_results)} images uploaded")

        # ── Validation ─────────────────────────────────────────────────────
        if phase in ("validate", "all"):
            with st.spinner("Running validation..."):
                results = run_validation(client, parsed, output_dir=output_dir)

            passed = sum(1 for r in results if r["status"] == "PASS")
            failed = sum(1 for r in results if r["status"] == "FAIL")
            empty  = sum(1 for r in results if r["status"] == "EMPTY")
            total  = len(results)
            rate   = round(passed / total * 100) if total > 0 else 0

            st.header("4. Validation Report")
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total checks", total)
            c2.metric("Passed", passed, delta=f"{rate}%")
            c3.metric("Failed", failed)
            c4.metric("Empty", empty)
            c5.metric("Pass rate", f"{rate}%")

            # Colour code the results
            def highlight_status(row):
                if row["status"] == "PASS":
                    return ["background-color: #1a4731; color: #ffffff"] * len(row)
                elif row["status"] == "FAIL":
                    return ["background-color: #5c1a1a; color: #ffffff"] * len(row)
                elif row["status"] == "EMPTY":
                    return ["background-color: #4a3c00; color: #ffffff"] * len(row)
                return [""] * len(row)

            import pandas as pd
            df = pd.DataFrame(results)
            st.dataframe(
                df.style.apply(highlight_status, axis=1),
                use_container_width=True
            )

            report_path = os.path.join(output_dir, "validation_report.csv")
            if os.path.exists(report_path):
                with open(report_path, encoding="utf-8") as f:
                    csv_data = f.read()
                st.download_button(
                    label="⬇ Download validation_report.csv",
                    data=csv_data,
                    file_name="validation_report.csv",
                    mime="text/csv"
                )

    except Exception as e:
        st.error(f"❌ Error: {e}")
        raise
    finally:
        os.unlink(tmp_path)