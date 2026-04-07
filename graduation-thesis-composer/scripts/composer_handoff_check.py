#!/usr/bin/env python3
"""Validate adapter handoff package for composer usage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REQUIRED_OUTPUT_KEYS = [
    "normalized_outline",
    "section_semantic_map",
    "replace_boundaries",
    "repo_evidence_index",
    "thesis_scaffold",
    "section_evidence_packs",
]


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(output_dir: Path, manifest: dict) -> list[str]:
    findings: list[str] = []
    outputs = manifest.get("outputs", {})

    for key in REQUIRED_OUTPUT_KEYS:
        if key not in outputs:
            findings.append(f"missing key in manifest.outputs: {key}")

    for key in ("normalized_outline", "section_semantic_map", "replace_boundaries", "repo_evidence_index", "thesis_scaffold"):
        value = outputs.get(key)
        if not value:
            findings.append(f"missing required artifact value: {key}")
            continue
        if not (output_dir / value).exists():
            findings.append(f"artifact file not found: {value}")

    packs = outputs.get("section_evidence_packs", [])
    if not isinstance(packs, list) or len(packs) == 0:
        findings.append("section_evidence_packs is empty")
    else:
        for file_name in packs:
            if not (output_dir / file_name).exists():
                findings.append(f"section evidence pack not found: {file_name}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff-dir", required=True, help="Adapter handoff output directory")
    parser.add_argument("--output", help="Optional report output path")
    args = parser.parse_args()

    handoff_dir = Path(args.handoff_dir).resolve()
    manifest_path = handoff_dir / "handoff_manifest.json"
    if not manifest_path.exists():
        print(f"handoff_manifest.json not found in {handoff_dir}", file=sys.stderr)
        return 1

    manifest = load_manifest(manifest_path)
    findings = validate_manifest(handoff_dir, manifest)

    lines = ["# Composer Handoff Check", ""]
    if findings:
        lines.append("## Issues")
        lines.append("")
        for item in findings:
            lines.append(f"- {item}")
    else:
        lines.append("- Handoff package is valid for composer input.")
    lines.append("")

    report = "\n".join(lines)
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
    else:
        print(report, end="")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
