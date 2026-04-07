#!/usr/bin/env python3
"""Build chapter evidence pack with two-stage discovery and explainable ranking."""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
import re


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

EXCLUDE_PATH_KEYWORDS = {
    "package-lock.json",
    "tsconfig.",
    "eslint.config",
    "openapi2ts.config",
    "env.example",
}

TEMP_DIR_NAMES = {
    "tmp",
    "temp",
    ".temp",
    ".tmp",
    ".cache",
    ".history",
    "logs",
    "log",
}

NOISE_PROFILES = {
    "relaxed": {
        "temp_path_penalty": 6,
        "impl_config_penalty": 2,
        "impl_docs_penalty": 1,
        "impl_config_group_limit": 6,
        "impl_docs_group_limit": 8,
        "design_config_group_limit": 8,
        "impl_config_min_score": 6,
        "design_config_min_score": 6,
    },
    "balanced": {
        "temp_path_penalty": 10,
        "impl_config_penalty": 4,
        "impl_docs_penalty": 2,
        "impl_config_group_limit": 4,
        "impl_docs_group_limit": 6,
        "design_config_group_limit": 6,
        "impl_config_min_score": 8,
        "design_config_min_score": 8,
    },
    "strict": {
        "temp_path_penalty": 14,
        "impl_config_penalty": 6,
        "impl_docs_penalty": 3,
        "impl_config_group_limit": 2,
        "impl_docs_group_limit": 4,
        "design_config_group_limit": 4,
        "impl_config_min_score": 10,
        "design_config_min_score": 10,
    },
}

GROUP_SUFFIXES = {
    "docs": {".md", ".rst", ".txt", ".adoc"},
    "database": {".sql"},
    "config": {".yml", ".yaml", ".properties", ".toml", ".json", ".xml", ".env"},
    "frontend": {".vue", ".ts", ".tsx", ".js", ".jsx", ".html", ".css", ".scss", ".less"},
}

SECTION_HINTS = {
    "abstract": ["readme", "overview", "intro", "project", "summary"],
    "introduction": ["readme", "background", "overview", "project"],
    "requirements": ["requirement", "user", "role", "flow", "page", "controller", "service"],
    "design": ["design", "architecture", "schema", "entity", "module", "database", "mapper"],
    "implementation": ["controller", "service", "impl", "page", "component", "store", "task", "chat"],
    "testing": ["test", "spec", "feature", "http", "rest", "login", "register"],
    "conclusion": ["readme", "roadmap", "improve", "summary", "project"],
}

DIR_ROLE_KEYWORDS = {
    "docs": {"doc", "docs", "document", "guide", "manual", "wiki"},
    "backend": {"src", "server", "backend", "api", "service", "controller"},
    "frontend": {"web", "front", "frontend", "ui", "client", "page", "pages", "component", "components"},
    "database": {"db", "data", "schema", "migration", "migrations", "sql"},
    "config": {"config", "configs", "conf", "settings", "resource", "resources"},
    "test": {"test", "tests", "spec", "e2e", "qa"},
}

SEMANTIC_ROLE_BOOSTS = {
    "abstract": {"docs": 8},
    "introduction": {"docs": 8},
    "requirements": {"docs": 6, "backend": 3, "frontend": 3},
    "design": {"docs": 8, "database": 9, "config": 4, "backend": 3},
    "implementation": {"backend": 8, "frontend": 8, "database": 2},
    "testing": {"test": 9, "backend": 4, "frontend": 3},
    "conclusion": {"docs": 6},
}

SEMANTIC_SUFFIX_BOOSTS = {
    "design": {".sql": 9, ".md": 5, ".yml": 3, ".yaml": 3, ".xml": 3, ".properties": 3},
    "implementation": {".java": 6, ".kt": 6, ".py": 6, ".go": 6, ".vue": 6, ".tsx": 6, ".jsx": 6, ".ts": 4, ".js": 4},
    "testing": {".feature": 8, ".http": 8, ".rest": 8},
}

SEMANTIC_FILE_BOOSTS = {
    "design": {"design", "architecture", "schema", "entity", "mapper", "module", "table"},
    "implementation": {"controller", "service", "impl", "page", "component", "task", "chat", "app", "user"},
    "testing": {"test", "spec", "login", "register", "health", "verify"},
    "requirements": {"requirement", "design", "module", "user", "app"},
}

SEMANTIC_FILE_PENALTIES = {
    "design": {"tsconfig", "eslint", "openapi", "env.example", "vite.config", "main.ts", "index.ts", "index.js"},
    "implementation": {
        "tsconfig",
        "eslint",
        "openapi",
        "env.example",
        "typings.d.ts",
        "index.ts",
        "package.json",
        "package-lock.json",
        ".prettierrc",
    },
    "requirements": {"tsconfig", "eslint", "openapi"},
}

CN_SECTION_HINTS = {
    "abstract": ["摘要"],
    "introduction": ["绪论", "引言"],
    "requirements": ["需求"],
    "design": ["设计", "架构", "数据库"],
    "implementation": ["实现", "详细设计", "模块"],
    "testing": ["测试"],
    "conclusion": ["结论", "展望", "总结"],
}


@dataclass
class FileCandidate:
    rel_path: str
    group: str
    dir_role: str | None
    suffix: str
    file_name: str
    path_parts_lower: tuple[str, ...]


def should_skip(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def should_exclude(rel_path: str) -> bool:
    lowered = rel_path.lower()
    return any(keyword in lowered for keyword in EXCLUDE_PATH_KEYWORDS)


def is_temp_path(parts_lower: tuple[str, ...]) -> bool:
    return any(part in TEMP_DIR_NAMES for part in parts_lower[:-1])


def parse_focus_keywords(raw: str, focus_file: str | None) -> list[str]:
    keywords: list[str] = []
    if raw:
        keywords.extend(item.strip().lower() for item in raw.split(",") if item.strip())
    if focus_file:
        content = Path(focus_file).read_text(encoding="utf-8")
        keywords.extend(line.strip().lower() for line in content.splitlines() if line.strip())
    deduped: list[str] = []
    seen = set()
    for keyword in keywords:
        if keyword not in seen:
            deduped.append(keyword)
            seen.add(keyword)
    return deduped


def normalize_section(section: str) -> tuple[str, list[str]]:
    lowered = section.strip().lower()
    tokens = [token for token in re.split(r"[\s\-_./:：()（）]+", lowered) if token]

    if "abstract" in lowered or any(x in section for x in CN_SECTION_HINTS["abstract"]):
        return "abstract", tokens
    if "introduction" in lowered or any(x in section for x in CN_SECTION_HINTS["introduction"]):
        return "introduction", tokens
    if "requirement" in lowered or any(x in section for x in CN_SECTION_HINTS["requirements"]):
        return "requirements", tokens
    if "implementation" in lowered or any(x in section for x in CN_SECTION_HINTS["implementation"]):
        return "implementation", tokens
    if "design" in lowered or "architecture" in lowered or any(x in section for x in CN_SECTION_HINTS["design"]):
        return "design", tokens
    if "test" in lowered or "testing" in lowered or any(x in section for x in CN_SECTION_HINTS["testing"]):
        return "testing", tokens
    if "conclusion" in lowered or any(x in section for x in CN_SECTION_HINTS["conclusion"]):
        return "conclusion", tokens
    return "generic", tokens


def infer_dir_role(name: str) -> str | None:
    lowered = name.lower()
    for role, keywords in DIR_ROLE_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return role
    return None


def classify_group(suffix: str) -> str:
    for group, suffixes in GROUP_SUFFIXES.items():
        if suffix in suffixes:
            return group
    return "backend"


def discover_candidates(root: Path) -> list[FileCandidate]:
    candidates: list[FileCandidate] = []
    for path in root.rglob("*"):
        if path.is_dir() or should_skip(path):
            continue
        rel = path.relative_to(root).as_posix()
        if should_exclude(rel):
            continue

        suffix = path.suffix.lower()
        file_name = path.name.lower()
        group = classify_group(suffix)
        rel_parts = path.relative_to(root).parts
        rel_parts_lower = tuple(part.lower() for part in rel_parts)
        top_dir = rel_parts[0] if rel_parts else ""
        dir_role = infer_dir_role(top_dir) if top_dir else None

        candidates.append(
            FileCandidate(
                rel_path=rel,
                group=group,
                dir_role=dir_role,
                suffix=suffix,
                file_name=file_name,
                path_parts_lower=rel_parts_lower,
            )
        )
    return candidates


def semantic_suffix_boost(semantic: str, suffix: str) -> int:
    return SEMANTIC_SUFFIX_BOOSTS.get(semantic, {}).get(suffix, 0)


def min_score_for_group(semantic: str, group: str, profile: dict[str, int]) -> int:
    if semantic == "design":
        if group == "config":
            return int(profile["design_config_min_score"])
        if group == "frontend":
            return 6
    if semantic == "implementation" and group == "config":
        return int(profile["impl_config_min_score"])
    return 1


def group_limit(semantic: str, group: str, base_limit: int, profile: dict[str, int]) -> int:
    if semantic == "implementation" and group == "config":
        return min(int(profile["impl_config_group_limit"]), base_limit)
    if semantic == "design" and group == "config":
        return min(int(profile["design_config_group_limit"]), base_limit)
    if semantic == "implementation" and group == "docs":
        return min(int(profile["impl_docs_group_limit"]), base_limit)
    return base_limit


def rank_candidates(
    candidates: list[FileCandidate],
    semantic: str,
    tokens: list[str],
    focus_keywords: list[str],
    limit: int,
    noise_profile: dict[str, int],
) -> dict[str, list[tuple[int, str, str]]]:
    grouped: dict[str, list[tuple[int, str, str]]] = defaultdict(list)

    for candidate in candidates:
        path_lower = candidate.rel_path.lower()
        score = 0
        reasons: list[str] = []
        breakdown: dict[str, int] = defaultdict(int)

        if is_temp_path(candidate.path_parts_lower):
            temp_penalty = int(noise_profile["temp_path_penalty"])
            reasons.append(f"penalty:temp-path-{temp_penalty}")
            score -= temp_penalty
            breakdown["penalty_temp_path"] -= temp_penalty

        for hint in SECTION_HINTS.get(semantic, []):
            if hint in path_lower:
                score += 3
                reasons.append(f"hint:{hint}+3")
                breakdown["hint_match"] += 3

        for token in tokens:
            if len(token) >= 2 and token in path_lower:
                score += 2
                reasons.append(f"token:{token}+2")
                breakdown["section_token_match"] += 2

        suffix_score = semantic_suffix_boost(semantic, candidate.suffix)
        if suffix_score:
            score += suffix_score
            reasons.append(f"suffix:{candidate.suffix}+{suffix_score}")
            breakdown["semantic_suffix"] += suffix_score

        role_boost = SEMANTIC_ROLE_BOOSTS.get(semantic, {})
        if candidate.dir_role and candidate.dir_role in role_boost:
            role_score = role_boost[candidate.dir_role]
            score += role_score
            reasons.append(f"role:{candidate.dir_role}+{role_score}")
            breakdown["dir_role"] += role_score

        for keyword in SEMANTIC_FILE_BOOSTS.get(semantic, set()):
            if keyword in candidate.file_name:
                score += 3
                reasons.append(f"name:{keyword}+3")
                breakdown["semantic_name"] += 3

        for keyword in focus_keywords:
            if keyword in path_lower:
                score += 8
                reasons.append(f"focus:{keyword}+8")
                breakdown["focus_keyword"] += 8

        for keyword in SEMANTIC_FILE_PENALTIES.get(semantic, set()):
            if keyword in path_lower:
                score -= 7
                reasons.append(f"penalty:{keyword}-7")
                breakdown["semantic_penalty"] -= 7

        if candidate.file_name in {"index.ts", "index.js", "main.ts", "main.js", "app.vue"}:
            score -= 3
            reasons.append("penalty:generic-entry-3")
            breakdown["generic_entry_penalty"] -= 3

        if semantic == "implementation" and candidate.group == "config":
            impl_config_penalty = int(noise_profile["impl_config_penalty"])
            score -= impl_config_penalty
            reasons.append(f"penalty:impl-config-{impl_config_penalty}")
            breakdown["impl_config_penalty"] -= impl_config_penalty
        if semantic == "implementation" and candidate.group == "docs":
            impl_docs_penalty = int(noise_profile["impl_docs_penalty"])
            score -= impl_docs_penalty
            reasons.append(f"penalty:impl-docs-{impl_docs_penalty}")
            breakdown["impl_docs_penalty"] -= impl_docs_penalty

        if score < min_score_for_group(semantic, candidate.group, noise_profile):
            continue

        source_fields = [f"total={score}"]
        for key in sorted(breakdown):
            source_fields.append(f"{key}={breakdown[key]}")
        source_summary = " | ".join(source_fields)
        reason_summary = "; ".join(reasons) if reasons else "base-score"
        grouped[candidate.group].append((score, candidate.rel_path, f"{source_summary} || {reason_summary}"))

    trimmed: dict[str, list[tuple[int, str, str]]] = {}
    for group, items in grouped.items():
        items.sort(key=lambda item: (-item[0], item[1]))
        trimmed[group] = items[: group_limit(semantic, group, limit, noise_profile)]
    return dict(sorted(trimmed.items()))


def render(
    section: str,
    semantic: str,
    groups: dict[str, list[tuple[int, str, str]]],
    focus_keywords: list[str],
    noise_profile_name: str,
) -> str:
    lines = [
        "# Section Evidence Pack",
        "",
        f"- target_section: `{section}`",
        f"- semantic_type: `{semantic}`",
        f"- noise_profile: `{noise_profile_name}`",
    ]
    if focus_keywords:
        lines.append(f"- focus_keywords: `{', '.join(focus_keywords)}`")
    lines.append("")

    if not groups:
        lines.append("No candidate evidence files found.")
        lines.append("")
        return "\n".join(lines)

    for group, items in groups.items():
        lines.append(f"## {group}")
        lines.append("")
        for score, rel, reason in items:
            lines.append(f"- `{rel}` (score={score})")
            lines.append(f"  - score_sources: `{reason}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--section", required=True, help="Target chapter or subsection title")
    parser.add_argument("--root", default=".", help="Repository root to scan")
    parser.add_argument("--limit", type=int, default=12, help="Max items per evidence group")
    parser.add_argument("--focus", default="", help="Comma-separated focus keywords")
    parser.add_argument("--focus-file", help="Path to focus keyword file (one per line)")
    parser.add_argument(
        "--noise-profile",
        default="balanced",
        choices=sorted(NOISE_PROFILES.keys()),
        help="Noise suppression profile for config/temp/docs candidates",
    )
    parser.add_argument("--output", help="Optional output file path")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    semantic, tokens = normalize_section(args.section)
    focus_keywords = parse_focus_keywords(args.focus, args.focus_file)
    noise_profile = NOISE_PROFILES[args.noise_profile]

    discovered = discover_candidates(root)
    groups = rank_candidates(discovered, semantic, tokens, focus_keywords, args.limit, noise_profile)
    output = render(args.section, semantic, groups, focus_keywords, args.noise_profile)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
