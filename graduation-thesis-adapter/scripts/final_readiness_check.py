#!/usr/bin/env python3
"""Check a thesis draft for final-readiness issues before delivery."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
PLACEHOLDER_PATTERNS = [r"\.\.\.", r"\[待补充\]", r"\[待撰写\]", r"\bTODO\b", r"\bTBD\b"]
INSTRUCTION_PATTERNS = [
    r"^\s*>?\s*此为.*模板",
    r"^\s*>?\s*说明：",
    r"请在此",
    r"请根据.*替换",
    r"本节仅保留",
    r"填写说明",
]


def collect_findings(text: str) -> list[str]:
    findings: list[str] = []
    headings: list[str] = []

    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            headings.append(heading_match.group(2))
            if "..." in heading_match.group(2):
                findings.append(f"line {index}: placeholder heading remains -> {heading_match.group(2)}")

        for pattern in PLACEHOLDER_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                findings.append(f"line {index}: placeholder content remains -> {stripped}")
                break

        for pattern in INSTRUCTION_PATTERNS:
            if re.search(pattern, stripped):
                findings.append(f"line {index}: template instruction text remains -> {stripped}")
                break

    if "参考文献" in text and "[待" in text:
        findings.append("global: references section still contains placeholders")

    if "系统" in text and "平台" in text:
        findings.append("global: terminology may still be mixed between '系统' and '平台'")

    seen: set[str] = set()
    duplicates: list[str] = []
    for heading in headings:
        if heading in seen:
            duplicates.append(heading)
        seen.add(heading)
    for heading in sorted(set(duplicates)):
        findings.append(f"global: duplicate heading detected -> {heading}")

    return findings


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
    findings = collect_findings(text)
    if findings:
        output = "# Final Readiness Check\n\n" + "\n".join(f"- {item}" for item in findings) + "\n"
    else:
        output = "# Final Readiness Check\n\n- No obvious final-readiness issues found.\n"

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
