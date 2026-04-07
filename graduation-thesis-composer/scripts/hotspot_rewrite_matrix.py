#!/usr/bin/env python3
"""Generate rewrite hotspot matrix template from detection report page specs."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re


PAGE_RE = re.compile(r"\d+")


@dataclass(frozen=True)
class HotspotRow:
    page: int
    risk_type: str
    rewrite_intensity: str
    status: str


def parse_page_spec(spec: str) -> list[int]:
    pages: list[int] = []
    for part in (item.strip() for item in spec.split(",") if item.strip()):
        if "-" in part:
            left, right = part.split("-", 1)
            start = int(left.strip())
            end = int(right.strip())
            if start > end:
                raise ValueError(f"invalid range: {part}")
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


def parse_report_text_to_pages(text: str) -> list[int]:
    pages = [int(match.group(0)) for match in PAGE_RE.finditer(text)]
    return sorted(set(page for page in pages if page > 0))


def build_rows(pages: list[int], risk_type: str, intensity: str) -> list[HotspotRow]:
    return [HotspotRow(page=page, risk_type=risk_type, rewrite_intensity=intensity, status="TODO") for page in pages]


def render_markdown(rows: list[HotspotRow]) -> str:
    lines = [
        "# Hotspot Rewrite Matrix",
        "",
        "| report_page | mapped_section | risk_type | rewrite_intensity | strategy | status | notes |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row.page} | [待映射] | {row.risk_type} | {row.rewrite_intensity} | [整段重构/句法重排/术语替换] | {row.status} | [待补充] |"
        )
    lines.extend(
        [
            "",
            "## Usage Notes",
            "",
            "- `mapped_section` should point to thesis heading number (e.g. 3.2, 4.1.3).",
            "- Prefer heavy rewrites for repeated hotspot pages; avoid deleting technical facts.",
            "- Keep unsupported claims removed instead of weakened.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", default="", help="Page spec, e.g. 5,8-10")
    parser.add_argument("--report-file", help="Optional plain-text detection report extract")
    parser.add_argument("--risk-type", default="similarity", choices=["similarity", "aigc", "mixed"])
    parser.add_argument("--intensity", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--output", required=True, help="Output markdown path")
    args = parser.parse_args()

    pages: list[int] = []
    if args.pages:
        pages.extend(parse_page_spec(args.pages))
    if args.report_file:
        report_text = Path(args.report_file).read_text(encoding="utf-8")
        pages.extend(parse_report_text_to_pages(report_text))

    deduped_pages = sorted(set(pages))
    if not deduped_pages:
        raise SystemExit("no hotspot pages found; use --pages or --report-file")

    rows = build_rows(deduped_pages, args.risk_type, args.intensity)
    content = render_markdown(rows)
    Path(args.output).write_text(content + "\n", encoding="utf-8")
    print(f"Hotspot rewrite matrix generated: {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

