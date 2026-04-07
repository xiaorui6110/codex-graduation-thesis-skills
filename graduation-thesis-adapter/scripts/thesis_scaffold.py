#!/usr/bin/env python3
"""Generate a Markdown thesis scaffold from a target template."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def normalize_heading(line: str) -> str | None:
    match = HEADING_RE.match(line.strip())
    if not match:
        return None
    level = match.group(1)
    title = " ".join(match.group(2).split())
    return f"{level} {title}"


def build_scaffold(text: str, placeholder: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        heading = normalize_heading(raw_line)
        if not heading:
            continue
        lines.append(heading)
        lines.append("")
        lines.append(placeholder)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", required=True, help="Path to the target Markdown template")
    parser.add_argument("--output", help="Optional output file path")
    parser.add_argument("--placeholder", default="[待撰写]", help="Placeholder paragraph text")
    args = parser.parse_args()

    path = Path(args.template)
    if not path.exists():
        print(f"Template file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    scaffold = build_scaffold(text, args.placeholder)

    if args.output:
        Path(args.output).write_text(scaffold, encoding="utf-8")
    else:
        print(scaffold, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
