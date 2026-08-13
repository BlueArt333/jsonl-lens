"""Command-line interface for JSONL Lens."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


@dataclass
class Inspection:
    records: int = 0
    blank_lines: int = 0
    errors: list[str] = field(default_factory=list)
    fields: Counter[str] = field(default_factory=Counter)
    types: Counter[str] = field(default_factory=Counter)


def _type_name(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    return "object"


def inspect_stream(
    stream: TextIO,
    *,
    max_errors: int = 20,
    required_fields: tuple[str, ...] = (),
) -> Inspection:
    result = Inspection()
    for line_number, raw_line in enumerate(stream, start=1):
        text = raw_line.strip()
        if not text:
            result.blank_lines += 1
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            if len(result.errors) < max_errors:
                result.errors.append(
                    f"line {line_number}: column {exc.colno}: {exc.msg}"
                )
            continue

        result.records += 1
        result.types[_type_name(value)] += 1
        if isinstance(value, dict):
            result.fields.update(str(key) for key in value)
            missing = [field_name for field_name in required_fields if field_name not in value]
            if missing and len(result.errors) < max_errors:
                result.errors.append(
                    f"line {line_number}: missing required field(s): {', '.join(missing)}"
                )
        elif required_fields and len(result.errors) < max_errors:
            result.errors.append(
                f"line {line_number}: expected an object for required-field validation"
            )
    return result


def _render_text(result: Inspection, source: str) -> str:
    lines = [
        f"source: {source}",
        f"valid records: {result.records}",
        f"invalid lines: {len(result.errors)}",
        f"blank lines: {result.blank_lines}",
    ]
    if result.types:
        lines.append("record types: " + ", ".join(f"{k}={v}" for k, v in result.types.items()))
    if result.fields:
        fields = sorted(result.fields.items(), key=lambda item: (-item[1], item[0]))
        lines.append("top fields: " + ", ".join(f"{name}={count}" for name, count in fields[:10]))
    if result.errors:
        lines.append("errors:")
        lines.extend(f"  - {error}" for error in result.errors)
    return "\n".join(lines) + "\n"


def _render_json(result: Inspection, source: str) -> str:
    payload = {
        "source": source,
        "valid_records": result.records,
        "invalid_lines": len(result.errors),
        "blank_lines": result.blank_lines,
        "record_types": dict(result.types),
        "fields": dict(result.fields),
        "errors": result.errors,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jsonl-lens",
        description="Validate and summarize a JSON Lines file without loading it into memory.",
    )
    parser.add_argument("path", nargs="?", help="JSONL file path; omit to read standard input")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--max-errors", type=int, default=20)
    parser.add_argument(
        "--require-field",
        action="append",
        default=[],
        metavar="NAME",
        help="require NAME in every object record; may be repeated",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_errors < 1:
        raise SystemExit("--max-errors must be at least 1")

    source = args.path or "<stdin>"
    try:
        if args.path:
            with Path(args.path).open(encoding="utf-8") as stream:
                result = inspect_stream(
                    stream,
                    max_errors=args.max_errors,
                    required_fields=tuple(args.require_field),
                )
        else:
            result = inspect_stream(
                sys.stdin,
                max_errors=args.max_errors,
                required_fields=tuple(args.require_field),
            )
    except (OSError, UnicodeError) as exc:
        print(f"jsonl-lens: {exc}", file=sys.stderr)
        return 2

    renderer = _render_json if args.format == "json" else _render_text
    sys.stdout.write(renderer(result, source))
    return 1 if result.errors else 0


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
