#!/usr/bin/env python3
"""Extract Markdown heading structure for thesis template adaptation."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def extract_headings(text: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            headings.append((len(match.group(1)), match.group(2).strip()))
    return headings


def build_report(headings: list[tuple[int, str]]) -> str:
    if not headings:
        return "No Markdown headings found."

    lines = ["Template outline:", ""]
    for level, title in headings:
        indent = "  " * (level - 1)
        lines.append(f"{indent}- L{level}: {title}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to a Markdown template file")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    headings = extract_headings(text)
    print(build_report(headings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
