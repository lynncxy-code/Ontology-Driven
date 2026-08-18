"""Dry-run or commit an automatic UE customer-edit return file.

The default is dry-run. ``--commit`` always writes a full project backup before
the single atomic transaction.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from customer_edit_changes import CustomerEditError, apply_customer_edit_changes, load_change_document
from project_store import ProjectStore


def main(argv=None):
    parser = argparse.ArgumentParser(description="Apply OntoTwin customer edit changes")
    parser.add_argument("--input", required=True, help="customer-overrides.json")
    parser.add_argument("--commit", action="store_true", help="write changes; default is dry-run")
    parser.add_argument(
        "--backup-dir",
        default=os.path.join(os.path.dirname(__file__), "customer_edit_backups"),
        help="mandatory pre-commit backup directory",
    )
    args = parser.parse_args(argv)
    try:
        result = apply_customer_edit_changes(
            ProjectStore(),
            load_change_document(args.input),
            commit=args.commit,
            backup_dir=args.backup_dir,
        )
    except (CustomerEditError, OSError, ValueError, json.JSONDecodeError) as error:
        payload = error.response() if isinstance(error, CustomerEditError) else {
            "error": "customer_edit_import_failed", "message": str(error)
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.commit:
        print("DRY-RUN ONLY: review the summary, then re-run with --commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
