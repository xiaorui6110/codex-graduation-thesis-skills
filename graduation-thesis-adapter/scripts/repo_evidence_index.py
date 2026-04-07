#!/usr/bin/env python3
"""Build a generic thesis evidence index with lightweight directory-role discovery."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path


IGNORE_DIRS = {
    ".agents",
    ".git",
    ".idea",
    ".next",
    ".nuxt",
    ".vscode",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
}

DOC_SUFFIXES = {".md", ".rst", ".txt", ".adoc"}
BACKEND_SUFFIXES = {".java", ".kt", ".groovy", ".py", ".go", ".rb", ".cs"}
FRONTEND_SUFFIXES = {".vue", ".ts", ".tsx", ".js", ".jsx", ".html", ".css", ".scss", ".less"}
DATABASE_SUFFIXES = {".sql"}
CONFIG_SUFFIXES = {".yml", ".yaml", ".properties", ".toml", ".json", ".xml", ".env"}
TEST_SUFFIXES = {".http", ".rest", ".feature"}

DIR_ROLE_KEYWORDS = {
    "docs": {"doc", "docs", "document", "guide", "wiki", "manual"},
    "backend": {"src", "server", "backend", "api", "service", "controller"},
    "frontend": {"web", "front", "frontend", "ui", "client", "page", "pages", "component", "components"},
    "database": {"db", "data", "schema", "migration", "migrations", "sql"},
    "config": {"config", "configs", "conf", "settings", "resource", "resources"},
    "test": {"test", "tests", "spec", "e2e", "qa"},
}


def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def categorize(rel_path: Path) -> str | None:
    rel = rel_path.as_posix().lower()
    suffix = rel_path.suffix.lower()
    name = rel_path.name.lower()

    if suffix in DATABASE_SUFFIXES or any(token in rel for token in ("schema", "migration", "ddl", "seed", "flyway", "liquibase")):
        return "database"
    if suffix in CONFIG_SUFFIXES or name in {"pom.xml", "package.json", "vite.config.ts", "tsconfig.json"}:
        return "config"
    if suffix in DOC_SUFFIXES:
        return "project_docs"
    if suffix in TEST_SUFFIXES or "test" in rel or "spec" in rel:
        return "test_assets"
    if suffix in FRONTEND_SUFFIXES:
        return "frontend_code"
    if suffix in BACKEND_SUFFIXES:
        return "backend_code"
    return None


def detect_role_by_name(dir_name: str) -> str | None:
    lowered = dir_name.lower()
    for role, keywords in DIR_ROLE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return role
    return None


def build_index(root: Path) -> tuple[dict[str, list[str]], dict[str, dict[str, int]]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    dir_role_stats: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for path in root.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue
        rel = path.relative_to(root)
        category = categorize(rel)
        if category:
            grouped[category].append(rel.as_posix())

        if rel.parts:
            top_dir = rel.parts[0]
            role_from_name = detect_role_by_name(top_dir)
            if role_from_name:
                dir_role_stats[top_dir][role_from_name] += 1
            if category:
                if category == "project_docs":
                    dir_role_stats[top_dir]["docs"] += 1
                elif category == "frontend_code":
                    dir_role_stats[top_dir]["frontend"] += 1
                elif category == "backend_code":
                    dir_role_stats[top_dir]["backend"] += 1
                elif category == "database":
                    dir_role_stats[top_dir]["database"] += 1
                elif category == "config":
                    dir_role_stats[top_dir]["config"] += 1
                elif category == "test_assets":
                    dir_role_stats[top_dir]["test"] += 1

    for paths in grouped.values():
        paths.sort()
    return dict(sorted(grouped.items())), dict(sorted(dir_role_stats.items()))


def infer_role_labels(stats: dict[str, int]) -> list[str]:
    if not stats:
        return []
    sorted_roles = sorted(stats.items(), key=lambda item: (-item[1], item[0]))
    labels: list[str] = []
    top_count = sorted_roles[0][1]
    for role, count in sorted_roles:
        if count <= 0:
            continue
        if count >= max(2, top_count // 3):
            labels.append(role)
    return labels


def render_markdown(index: dict[str, list[str]], dir_roles: dict[str, dict[str, int]]) -> str:
    lines = ["# Thesis Evidence Index", ""]

    lines.append("## Directory Role Candidates")
    lines.append("")
    if not dir_roles:
        lines.append("- No directory role candidates detected.")
    else:
        for directory, stats in dir_roles.items():
            labels = infer_role_labels(stats)
            if not labels:
                continue
            stats_text = ", ".join(f"{role}:{stats[role]}" for role in sorted(stats))
            lines.append(f"- `{directory}` -> `{', '.join(labels)}` ({stats_text})")
    lines.append("")

    if not index:
        lines.append("## Evidence Groups")
        lines.append("")
        lines.append("No likely thesis evidence files were detected.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Evidence Groups")
    lines.append("")
    for category, paths in index.items():
        lines.append(f"### {category}")
        lines.append("")
        for path in paths:
            lines.append(f"- `{path}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    index, dir_roles = build_index(root)
    output = render_markdown(index, dir_roles)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
