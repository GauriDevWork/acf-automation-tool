# tests/test_mapper.py
from parser.mapper import map_field_type


# ── URL detection ─────────────────────────────────────────────────────────────
def test_url_with_slash():
    assert map_field_type("link", "/contact") == "url"

def test_url_with_http():
    assert map_field_type("linkedin", "https://linkedin.com/in/priyasharma") == "url"

def test_url_relative_path():
    assert map_field_type("button url", "/services/wordpress-development") == "url"


# ── Image detection ───────────────────────────────────────────────────────────
def test_image_jpg():
    assert map_field_type("photo", "priya-sharma.jpg") == "image"

def test_image_svg():
    assert map_field_type("logo", "techark-logo.svg") == "image"

def test_image_png():
    assert map_field_type("background", "hero-bg.png") == "image"

def test_image_in_short_value():
    assert map_field_type("background image", "File: hero-bg.jpg") == "image"


# ── Email detection ───────────────────────────────────────────────────────────
def test_email():
    assert map_field_type("email", "hello@techark.com") == "email"


# ── Number detection ──────────────────────────────────────────────────────────
def test_number():
    assert map_field_type("stat number", "150") == "number"

def test_number_single_digit():
    assert map_field_type("columns", "3") == "number"


# ── True/False detection ──────────────────────────────────────────────────────
def test_true_false_yes():
    assert map_field_type("lightbox", "Yes") == "true_false"

def test_true_false_no():
    assert map_field_type("active", "No") == "true_false"


# ── Wysiwyg detection ─────────────────────────────────────────────────────────
def test_wysiwyg_answer():
    assert map_field_type("answer", "Short") == "wysiwyg"

def test_wysiwyg_bio():
    assert map_field_type("bio", "Short bio") == "wysiwyg"


# ── Textarea detection ────────────────────────────────────────────────────────
def test_textarea_long_text():
    long = "We are a full-service digital agency specializing in WordPress development, UI/UX design, and performance optimization for enterprise clients."
    assert map_field_type("subheadline", long) == "textarea"


# ── Text default ──────────────────────────────────────────────────────────────
def test_text_default():
    assert map_field_type("headline", "Building Digital Experiences") == "text"

def test_text_short_label():
    assert map_field_type("button label", "Get a Free Consultation") == "text"