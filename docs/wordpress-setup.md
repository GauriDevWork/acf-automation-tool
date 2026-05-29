# WordPress Setup Guide

Before running the ACF Automation Tool against a WordPress site,
complete these setup steps.

## 1. Install ACF Pro
Install and activate Advanced Custom Fields PRO (tested on 6.x).

## 2. Import Field Groups
Run the schema builder to generate schema.json:
    python -m schema.output

Then import into WordPress:
WP Admin → Custom Fields → Tools → Import → select output/schema.json

## 3. Enable ACF REST API
Add to your theme's functions.php:

    add_filter('acf/rest_api/field_settings/show_in_rest', '__return_true');
    add_filter('acf/rest_api/field_settings/edit_in_rest', '__return_true');

This enables ACF fields to be read and written via the WordPress REST API.

## 4. Create Application Password
WP Admin → Users → Profile → Application Passwords
Create a new password for the automation tool.
Add credentials to config.py (never commit this file).

## 5. Verify Connection
    python -m api.client

Should print: [OK] Connected to WordPress