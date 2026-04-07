#!/usr/bin/env python3
"""Generate batch chapter draft skeletons from adapter handoff artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


HEADING_RE = re.compile(r"^##\s+([a-z_]+)\s*$")
ITEM_RE = re.compile(r"^- `([^`]+)`")
CHAPTER_NO_RE = re.compile(r"^\s*(\d+)(?:[.\s].*)?$")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_evidence_pack(path: Path, per_group: int) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    evidence: list[str] = []
    current_group: str | None = None
    count_in_group = 0
    for line in lines:
        heading = HEADING_RE.match(line.strip())
        if heading:
            current_group = heading.group(1)
            count_in_group = 0
            continue
        item = ITEM_RE.match(line.strip())
        if item and current_group:
            if count_in_group < per_group:
                evidence.append(item.group(1))
                count_in_group += 1
    return evidence


def draft_paragraph(title: str, semantic: str, evidence: list[str]) -> str:
    if evidence:
        refs = "；".join(evidence[:4])
    else:
        refs = "[待补充证据]"

    if semantic == "abstract":
        return (
            f"本节围绕“{title}”进行概述。结合项目现有实现与资料，可归纳系统目标、核心能力与技术路径。"
            f"当前可优先参考以下材料：{refs}。对于尚未明确的数据与结论，统一标记为[待补充]。"
        )
    if semantic == "introduction":
        return (
            f"围绕“{title}”，本节应说明研究背景、选题意义与论文组织。为确保叙述与项目事实一致，"
            f"建议优先依据以下证据展开：{refs}。不具备明确依据的结论不直接下判断。"
        )
    if semantic in {"requirements", "design", "implementation", "testing"}:
        return (
            f"本节对应“{title}”的核心写作任务是将项目实现事实转化为论文叙述。当前可优先使用的证据包括：{refs}。"
            f"建议按“问题背景-设计或实现路径-结果与约束”的结构展开，并对缺失事实使用[待补充]。"
        )
    if semantic == "conclusion":
        return (
            f"本节用于总结“{title}”相关工作与后续展望。建议基于已实现功能与可验证结果进行归纳，"
            f"可参考：{refs}。不应扩展到无证据支撑的性能或创新结论。"
        )
    return (
        f"本节“{title}”先基于现有证据形成可编辑初稿。可参考：{refs}。"
        f"后续由人工或模型按模板与语义要求继续补全。"
    )


def chapter_no_from_title(title: str) -> int | None:
    match = CHAPTER_NO_RE.match(title.strip())
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def parse_chapter_range(raw: str) -> tuple[int, int] | None:
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


def build_draft(
    handoff_dir: Path,
    output_path: Path,
    per_group: int,
    semantics: set[str] | None,
    chapter_range: tuple[int, int] | None,
) -> None:
    manifest = load_json(handoff_dir / "handoff_manifest.json")
    semantic_map = load_json(handoff_dir / manifest["outputs"]["section_semantic_map"])
    pack_files = set(manifest["outputs"].get("section_evidence_packs", []))

    lines = ["# Composer Batch Draft", ""]
    for section in semantic_map.get("sections", []):
        semantic = section.get("semantic_type", "generic")
        if semantics and semantic not in semantics:
            continue

        slug = section.get("slug")
        title = section.get("title")
        chapter_no = chapter_no_from_title(str(title))
        if chapter_range and chapter_no is not None:
            if chapter_no < chapter_range[0] or chapter_no > chapter_range[1]:
                continue
        pack_name = f"section_evidence_pack_{slug}.md"
        if pack_name not in pack_files:
            continue

        pack_path = handoff_dir / pack_name
        evidence = parse_evidence_pack(pack_path, per_group=per_group)

        level = int(section.get("level", 2))
        heading_marks = "#" * max(2, min(6, level))
        lines.append(f"{heading_marks} {title}")
        lines.append("")
        lines.append(draft_paragraph(str(title), str(semantic), evidence))
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff-dir", required=True, help="Adapter handoff directory")
    parser.add_argument("--output", required=True, help="Output markdown for batch draft")
    parser.add_argument("--per-group", type=int, default=2, help="Evidence files to use per group")
    parser.add_argument(
        "--semantics",
        default="",
        help="Optional comma-separated semantic types to include (e.g. design,implementation,testing)",
    )
    parser.add_argument(
        "--chapter-range",
        default="",
        help="Optional chapter number range, e.g. 3-5 or 4",
    )
    args = parser.parse_args()

    handoff_dir = Path(args.handoff_dir).resolve()
    output = Path(args.output).resolve()
    semantic_filter = {item.strip() for item in args.semantics.split(",") if item.strip()} or None
    try:
        chapter_range = parse_chapter_range(args.chapter_range)
    except ValueError as exc:
        parser.error(str(exc))

    build_draft(handoff_dir, output, args.per_group, semantic_filter, chapter_range)
    print(f"Batch draft generated: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
