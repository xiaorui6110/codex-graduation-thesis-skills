#!/usr/bin/env python3
"""Audit a Markdown thesis draft and emit keep/rewrite/delete oriented findings."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import sys


PLACEHOLDER_PATTERNS = [
    r"\.\.\.",
    r"\[待补充\]",
    r"\[待撰写\]",
    r"\bTODO\b",
    r"\bTBD\b",
]

INSTRUCTION_PATTERNS = [
    r"^\s*>?\s*此为.*模板",
    r"^\s*>?\s*说明：",
    r"请在此",
    r"请根据.*替换",
    r"本节仅保留",
    r"填写说明",
]

UNSUPPORTED_CLAIM_PATTERNS = [
    r"显著提高",
    r"大幅提升",
    r"高并发",
    r"生产环境",
    r"海量用户",
]

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")


def classify_line(line: str, is_heading: bool) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped:
        return None

    if is_heading and "..." in stripped:
        return "delete", f"placeholder heading -> {stripped}"

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, stripped, re.IGNORECASE):
            return "rewrite", f"placeholder text -> {stripped}"

    for pattern in INSTRUCTION_PATTERNS:
        if re.search(pattern, stripped):
            return "delete", f"template or instruction text -> {stripped}"

    for pattern in UNSUPPORTED_CLAIM_PATTERNS:
        if re.search(pattern, stripped):
            return "rewrite", f"possibly unsupported claim -> {stripped}"

    return None


def audit_text(text: str) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = defaultdict(list)
    lines = text.splitlines()

    for index, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        result = classify_line(line, heading_match is not None)
        if result:
            action, message = result
            buckets[action].append(f"line {index}: {message}")

    if "系统" in text and "平台" in text:
        buckets["keep_with_minor_edits"].append(
            "global: mixed usage of '系统' and '平台' detected; normalize terminology"
        )

    if not any(bucket for bucket in buckets.values()):
        buckets["keep"].append("global: no obvious placeholder or template residue found")

    return dict(buckets)


def render_report(findings: dict[str, list[str]]) -> str:
    ordered_keys = ["delete", "rewrite", "keep_with_minor_edits", "keep"]
    title_map = {
        "delete": "Delete",
        "rewrite": "Rewrite",
        "keep_with_minor_edits": "Keep With Minor Edits",
        "keep": "Keep",
    }

    lines = ["# Draft Audit Report", ""]
    for key in ordered_keys:
        items = findings.get(key)
        if not items:
            continue
        lines.append(f"## {title_map[key]}")
        lines.append("")
        for item in items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to a Markdown thesis draft")
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    report = render_report(audit_text(text))

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
