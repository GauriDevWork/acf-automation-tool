# main.py
import argparse
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
logger = logging.getLogger(__name__)


def run(args):
    """Main pipeline runner."""
    import config
    from api.client import WPClient
    from parser.parser import parse_document
    from schema.output import build_all_schemas

    # Load and parse document
    logger.info(f"\n[ACF TOOL] Input: {args.input}")
    if not os.path.exists(args.input):
        logger.error(f"[ERROR] File not found: {args.input}")
        sys.exit(1)

    parsed = parse_document(args.input)

    # Schema phase
    if args.phase in ("schema", "all"):
        logger.info("\n[ACF TOOL] Building schemas...")
        schemas = build_all_schemas(parsed, output_dir=args.output_dir)
        logger.info(f"[ACF TOOL] {len(schemas)} field groups saved to {args.output_dir}/")

    # Dry run stops here
    if args.dry_run:
        logger.info("\n[ACF TOOL] Dry run complete — no WordPress writes performed.")
        logger.info(f"[ACF TOOL] Schema saved to: {args.output_dir}/schema.json")
        return

    # API phase
    if args.phase in ("push", "all"):
        client = WPClient(args.url, args.user, args.password)

        logger.info("\n[ACF TOOL] Testing WordPress connection...")
        if not client.test_connection():
            logger.error("[ERROR] Cannot connect to WordPress. Check --url, --user, --password.")
            sys.exit(1)

        from api.orchestrator import run_all
        logger.info("\n[ACF TOOL] Starting full pipeline...")
        run_all(client, parsed)

    # Validate phase
    if args.phase in ("validate", "all"):
        if args.dry_run:
            return
        client = WPClient(args.url, args.user, args.password)
        from validator.validator import run_validation
        logger.info("\n[ACF TOOL] Running validation...")
        run_validation(client, parsed, output_dir=args.output_dir)


def main():
    parser = argparse.ArgumentParser(
        prog="acf-tool",
        description="ACF Automation Tool — Convert .docx content documents to WordPress ACF fields.",
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the .docx content document"
    )
    parser.add_argument(
        "--url",
        default=None,
        help="WordPress site URL (e.g. http://localhost:10046)"
    )
    parser.add_argument(
        "--user",
        default=None,
        help="WordPress username"
    )
    parser.add_argument(
        "--password",
        default=None,
        help="WordPress Application Password"
    )
    parser.add_argument(
        "--phase",
        choices=["schema", "push", "validate", "all"],
        default="all",
        help="Which phase to run (default: all)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and generate schema only — no WordPress writes"
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory for output files (default: output)"
    )

    args = parser.parse_args()

    # Load from config.py if not provided via flags
    if not args.dry_run:
        try:
            import config
            if not args.url:
                args.url = config.WP_URL
            if not args.user:
                args.user = config.WP_USER
            if not args.password:
                args.password = config.WP_PASSWORD
        except ImportError:
            if args.phase != "schema":
                logger.error("[ERROR] config.py not found. Provide --url, --user, --password.")
                sys.exit(1)

    run(args)


if __name__ == "__main__":
    main()