#!/usr/bin/env python3
"""Check one thesis chapter for common quality issues."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


PLACEHOLDER_PATTERNS = [r"\[待补充\]", r"\[待撰写\]", r"\bTODO\b", r"\bTBD\b"]
RISKY_PATTERNS = [
    r"显著提高",
    r"大幅提升",
    r"高并发",
    r"海量用户",
    r"生产环境验证",
    r"创新性地",
]


def collect_findings(text: str) -> list[str]:
    findings: list[str] = []
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                findings.append(f"line {index}: unresolved placeholder -> {stripped}")
                break

        for pattern in RISKY_PATTERNS:
            if re.search(pattern, stripped):
                findings.append(f"line {index}: review unsupported or exaggerated claim -> {stripped}")
                break

    if "系统" in text and "平台" in text:
        findings.append("global: mixed usage of '系统' and '平台' detected")

    if len(re.findall(r"因此|同时|此外|然后", text)) >= 8:
        findings.append("global: transitional wording may be repetitive; review prose variety")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to a Markdown chapter draft")
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    path = Path(args.input)
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        return 1

    text = path.read_text(encoding="utf-8")
    findings = collect_findings(text)
    if findings:
        output = "# Chapter Quality Check\n\n" + "\n".join(f"- {item}" for item in findings) + "\n"
    else:
        output = "# Chapter Quality Check\n\n- No obvious quality issues found.\n"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
