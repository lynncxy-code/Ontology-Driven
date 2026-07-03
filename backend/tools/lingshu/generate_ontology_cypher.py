#!/usr/bin/env python3
"""Generate Neo4j Cypher statements from ontology JSON."""

from __future__ import annotations

import sys
from pathlib import Path

from ontology_rules import (
    OntologyValidationError,
    build_cypher_arg_parser,
    generate_cypher,
    load_json,
    validate_json_schema,
    validate_ontology,
)


def main(argv: list[str] | None = None) -> int:
    parser = build_cypher_arg_parser()
    args = parser.parse_args(argv)

    try:
        registry = load_json(args.json_file)
        if not args.skip_schema:
            validate_json_schema(registry, args.schema)
        validate_ontology(registry)
        cypher = generate_cypher(registry)
    except (OntologyValidationError, ValueError) as exc:
        print("FAILED", file=sys.stderr)
        if isinstance(exc, OntologyValidationError):
            for error in exc.errors:
                print(f"- {error}", file=sys.stderr)
        else:
            print(f"- {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(cypher, encoding="utf-8")
    else:
        print(cypher, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
