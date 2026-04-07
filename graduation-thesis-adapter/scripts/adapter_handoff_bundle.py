#!/usr/bin/env python3
"""Generate adapter-to-composer handoff artifacts in one run."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
CHAPTER_NO_RE = re.compile(r"^\s*(\d+)(?:[.\s].*)?$")


def extract_headings(template_text: str) -> list[dict[str, object]]:
    headings: list[dict[str, object]] = []
    for line in template_text.splitlines():
        match = HEADING_RE.match(line)
        if not match:
            continue
        headings.append(
            {
                "level": len(match.group(1)),
                "title": match.group(2).strip(),
            }
        )
    return headings


def normalize_semantic(title: str) -> str:
    lowered = title.lower()
    if "abstract" in lowered or "摘要" in title:
        return "abstract"
    if "introduction" in lowered or "绪论" in title or "引言" in title:
        return "introduction"
    if "requirement" in lowered or "需求" in title:
        return "requirements"
    if "implementation" in lowered or "实现" in title or "详细设计" in title:
        return "implementation"
    if "design" in lowered or "architecture" in lowered or "设计" in title or "架构" in title:
        return "design"
    if "test" in lowered or "testing" in lowered or "测试" in title:
        return "testing"
    if "conclusion" in lowered or "结论" in title or "展望" in title or "总结" in title:
        return "conclusion"
    if "reference" in lowered or "参考文献" in title:
        return "references"
    if "acknowledgement" in lowered or "致谢" in title:
        return "acknowledgements"
    return "generic"


def slugify(text: str) -> str:
    lowered = text.lower().strip()
    slug = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", lowered).strip("-")
    return slug or "section"


def chapter_no_from_title(title: str) -> int | None:
    match = CHAPTER_NO_RE.match(title.strip())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def write_outline(headings: list[dict[str, object]], output_path: Path) -> None:
    lines = ["# Normalized Outline", ""]
    for item in headings:
        level = int(item["level"])
        title = str(item["title"])
        indent = "  " * (level - 1)
        lines.append(f"{indent}- L{level}: {title}")
    lines.append("")
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_semantic_map(headings: list[dict[str, object]], output_path: Path) -> list[dict[str, object]]:
    mapped: list[dict[str, object]] = []
    for idx, item in enumerate(headings, start=1):
        title = str(item["title"])
        mapped.append(
            {
                "id": idx,
                "level": int(item["level"]),
                "title": title,
                "semantic_type": normalize_semantic(title),
                "slug": slugify(f"{idx}-{title}"),
            }
        )
    output_path.write_text(json.dumps({"sections": mapped}, ensure_ascii=False, indent=2), encoding="utf-8")
    return mapped


def write_replace_boundaries(mapped_sections: list[dict[str, object]], output_path: Path) -> list[dict[str, object]]:
    boundaries: list[dict[str, object]] = []
    for idx, section in enumerate(mapped_sections):
        current_title = str(section["title"])
        current_level = int(section["level"])

        end_before_title: str | None = None
        for next_section in mapped_sections[idx + 1 :]:
            next_level = int(next_section["level"])
            if next_level <= current_level:
                end_before_title = str(next_section["title"])
                break

        boundaries.append(
            {
                "section_id": int(section["id"]),
                "slug": str(section["slug"]),
                "title": current_title,
                "semantic_type": str(section["semantic_type"]),
                "chapter_no": chapter_no_from_title(current_title),
                "start_anchor": {
                    "heading_text": current_title,
                    "match": "exact",
                },
                "end_anchor": {
                    "before_heading_text": end_before_title,
                    "fallback": "end_of_document" if end_before_title is None else "next_same_or_higher_level_heading",
                },
            }
        )

    payload = {
        "strategy": "body_heading_boundaries",
        "notes": [
            "Use body heading text as anchors.",
            "Do not use TOC lines as replacement anchors.",
        ],
        "boundaries": boundaries,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return boundaries


def run_script(script_path: Path, args: list[str]) -> None:
    command = [sys.executable, str(script_path), *args]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Script failed: {script_path.name}\n{result.stderr}")


def build_handoff(
    root: Path,
    template_path: Path,
    output_dir: Path,
    draft_path: Path | None,
    section_limit: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    template_text = template_path.read_text(encoding="utf-8")
    headings = extract_headings(template_text)

    outline_file = output_dir / "normalized_outline.md"
    semantic_map_file = output_dir / "section_semantic_map.json"
    replace_boundaries_file = output_dir / "replace_boundaries.json"
    evidence_index_file = output_dir / "repo_evidence_index.md"
    scaffold_file = output_dir / "thesis_scaffold.md"
    draft_audit_file = output_dir / "draft_audit_report.md"
    manifest_file = output_dir / "handoff_manifest.json"

    write_outline(headings, outline_file)
    mapped_sections = write_semantic_map(headings, semantic_map_file)
    write_replace_boundaries(mapped_sections, replace_boundaries_file)

    scripts_dir = Path(__file__).resolve().parent
    run_script(
        scripts_dir / "repo_evidence_index.py",
        ["--root", str(root), "--output", str(evidence_index_file)],
    )
    run_script(
        scripts_dir / "thesis_scaffold.py",
        ["--template", str(template_path), "--output", str(scaffold_file)],
    )

    section_files: list[str] = []
    for item in mapped_sections:
        semantic = str(item["semantic_type"])
        if semantic in {"generic", "references", "acknowledgements"}:
            continue
        title = str(item["title"])
        slug = str(item["slug"])
        section_file = output_dir / f"section_evidence_pack_{slug}.md"
        run_script(
            scripts_dir / "section_evidence_pack.py",
            [
                "--section",
                title,
                "--root",
                str(root),
                "--limit",
                str(section_limit),
                "--output",
                str(section_file),
            ],
        )
        section_files.append(section_file.name)

    if draft_path and draft_path.exists():
        run_script(
            scripts_dir / "draft_audit.py",
            ["--input", str(draft_path), "--output", str(draft_audit_file)],
        )

    manifest = {
        "template": str(template_path),
        "root": str(root),
        "outputs": {
            "normalized_outline": outline_file.name,
            "section_semantic_map": semantic_map_file.name,
            "replace_boundaries": replace_boundaries_file.name,
            "repo_evidence_index": evidence_index_file.name,
            "thesis_scaffold": scaffold_file.name,
            "draft_audit_report": draft_audit_file.name if draft_audit_file.exists() else None,
            "section_evidence_packs": section_files,
        },
    }
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root")
    parser.add_argument("--template", required=True, help="Template markdown file")
    parser.add_argument("--output-dir", required=True, help="Output directory for handoff artifacts")
    parser.add_argument("--draft", help="Optional draft markdown path for audit")
    parser.add_argument("--section-limit", type=int, default=12, help="Max files per section evidence group")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    template = Path(args.template).resolve()
    output_dir = Path(args.output_dir).resolve()
    draft = Path(args.draft).resolve() if args.draft else None

    if not template.exists():
        print(f"Template file not found: {template}", file=sys.stderr)
        return 1

    build_handoff(root, template, output_dir, draft, args.section_limit)
    print(f"Handoff bundle generated: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
