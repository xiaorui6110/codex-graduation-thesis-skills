#!/usr/bin/env python3
"""Generate section-level rewrite scope draft from adapter replace_boundaries.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_range(raw: str) -> tuple[int, int] | None:
    if not raw.strip():
        return None
    if "-" not in raw:
        value = int(raw.strip())
        return value, value
    left, right = raw.split("-", 1)
    start = int(left.strip())
    end = int(right.strip())
    if start > end:
        raise ValueError("chapter range start must be <= end")
    return start, end


def in_range(chapter_no: int | None, chapter_range: tuple[int, int] | None) -> bool:
    if chapter_range is None:
        return True
    if chapter_no is None:
        return False
    return chapter_range[0] <= chapter_no <= chapter_range[1]


def build_rows(
    boundaries: list[dict],
    chapter_range: tuple[int, int] | None,
    semantics: set[str] | None,
) -> list[dict]:
    rows: list[dict] = []
    for item in boundaries:
        semantic = str(item.get("semantic_type", "generic"))
        chapter_no = item.get("chapter_no")
        if semantics and semantic not in semantics:
            continue
        if isinstance(chapter_no, int):
            chapter_no_int = chapter_no
        else:
            chapter_no_int = None
        if not in_range(chapter_no_int, chapter_range):
            continue

        start_anchor = item.get("start_anchor", {})
        end_anchor = item.get("end_anchor", {})
        rows.append(
            {
                "section_id": item.get("section_id"),
                "slug": item.get("slug"),
                "title": item.get("title"),
                "semantic_type": semantic,
                "chapter_no": chapter_no_int,
                "rewrite_action": "rewrite_or_verify",
                "priority": "P1" if semantic in {"requirements", "design", "implementation", "testing"} else "P2",
                "start_heading": start_anchor.get("heading_text"),
                "end_before_heading": end_anchor.get("before_heading_text"),
                "boundary_fallback": end_anchor.get("fallback"),
                "notes": "[待补充]",
            }
        )
    return rows


def render_markdown(rows: list[dict]) -> str:
    lines = [
        "# Section Rewrite Scope Draft",
        "",
        "| section_id | chapter_no | title | semantic_type | rewrite_action | priority | start_heading | end_before_heading | boundary_fallback | notes |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {section_id} | {chapter_no} | {title} | {semantic_type} | {rewrite_action} | {priority} | {start_heading} | {end_before_heading} | {boundary_fallback} | {notes} |".format(
                **{
                    key: ("" if value is None else str(value).replace("|", "\\|"))
                    for key, value in row.items()
                }
            )
        )
    lines.extend(
        [
            "",
            "## Rules",
            "",
            "- Keep replacement anchors aligned to body headings.",
            "- Do not use TOC text as replacement anchors.",
            "- Fill `notes` with user constraints such as preserve/skip/restore instructions.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundaries", required=True, help="Path to replace_boundaries.json")
    parser.add_argument("--output", required=True, help="Output path (.md or .json)")
    parser.add_argument("--chapter-range", default="", help="Optional chapter range, e.g. 3-5 or 4")
    parser.add_argument("--semantics", default="", help="Optional semantic type filter, comma-separated")
    parser.add_argument("--format", default="md", choices=["md", "json"], help="Output format")
    args = parser.parse_args()

    boundaries_path = Path(args.boundaries).resolve()
    if not boundaries_path.exists():
        raise SystemExit(f"replace boundaries file not found: {boundaries_path}")

    payload = json.loads(boundaries_path.read_text(encoding="utf-8"))
    boundaries = payload.get("boundaries", [])
    if not isinstance(boundaries, list):
        raise SystemExit("invalid replace_boundaries json: boundaries must be list")

    try:
        chapter_range = parse_range(args.chapter_range)
    except ValueError as exc:
        parser.error(str(exc))
        return 2

    semantic_filter = {item.strip() for item in args.semantics.split(",") if item.strip()} or None
    rows = build_rows(boundaries, chapter_range, semantic_filter)

    output_path = Path(args.output).resolve()
    if args.format == "json":
        output_path.write_text(json.dumps({"rewrite_scope": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        output_path.write_text(render_markdown(rows).rstrip() + "\n", encoding="utf-8")
    print(f"Rewrite scope draft generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
