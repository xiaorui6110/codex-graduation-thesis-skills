---
name: graduation-thesis-adapter
description: Use this skill when Codex needs to adapt, scaffold, draft, rewrite, or normalize a Chinese undergraduate software engineering graduation thesis against different school templates or thesis outlines. Trigger for requests such as "根据学校模板补全毕业论文", "适配另一个毕业论文格式继续写", "从空模板生成目录和章节", "根据现有初稿重写成目标模板", "统一论文术语和章节结构", "审查草稿哪些保留哪些重写", or "先按模板抽取章节再逐章补全".
---

# Graduation Thesis Adapter

## Overview

Use this skill to handle generic graduation thesis completion across different templates, not just one repository-specific format.
Always adapt to the user's template first, then map project evidence to the template structure, and only then draft or rewrite thesis content.
For final-manuscript workflows, use adapter as planning gate before composer writing.

Companion flow:
1. `graduation-thesis-adapter`: template normalization, evidence mapping, rewrite boundaries
2. `graduation-thesis-composer`: chapter writing/rewrite and manuscript cleanup
3. `drawio`/equivalent: engineering diagram redraw when needed
4. runtime screenshot workflow: capture real page evidence when required

## Required Reading Order

1. Read `references/template-adaptation-rules.md`.
2. Read `references/template-semantic-mapping.md`.
3. Read `references/project-grounding-rules.md`.
4. Read `references/evidence-discovery-rules.md` before generating repository evidence outputs.
5. If the task involves an existing draft, read `references/draft-audit-rules.md`.
6. If the task involves direct chapter drafting, read `references/chapter-writing-guides.md`.
7. If the task involves global cleanup, read `references/terminology-normalization-rules.md`.
8. If the task is close to completion, read `references/final-readiness-rules.md`.
9. If the task involves similarity or AIGC report driven rewriting, read `references/detection-report-rewrite-playbook.md`.
10. If the task involves task assignment / opening report / mid-term material drafting, read `references/process-material-guides.md`.
11. If the task is a final-manuscript delivery plan, read `references/finalization-task-rules.md`.
12. If the task involves hand-edited draft continuation or partial replacement, read `references/draft-salvage-handoff-playbook.md`.
13. If the task involves figure/screenshot planning, read `references/figure-screenshot-planning-rules.md`.
14. When structure extraction, scaffold generation, repository evidence indexing, or draft auditing is repetitive, run the scripts under `scripts/` instead of rebuilding the same artifacts manually.

## Non-Negotiable Rules

- Treat the user-provided thesis template, sample, or heading structure as the formatting authority.
- Treat the repository, project docs, schema files, config, and user materials as the factual authority.
- Never invent features, experiment data, performance numbers, references, screenshots, deployment scale, or test conclusions.
- If the user has an existing draft, preserve supported content instead of rewriting blindly.
- Prefer explicit placeholders such as `[待补充]` over guessing.
- Keep chapter numbering, heading depth, and section order consistent with the user's target template.
- Keep terminology stable across the manuscript.
- For partial rewrite requests, define explicit replacement boundaries and protected sections.

## Workflow

### 1. Identify the task mode

Classify the request as one of:

- template scaffold
- chapter drafting
- draft rewrite
- terminology normalization
- final readiness check

### 2. Normalize the template structure

Before writing:

- identify the target heading hierarchy
- identify required front matter and back matter
- identify whether the template allows adding subsections
- convert the target structure into a normalized chapter map

When the heading structure is still unclear, run:

- `python graduation-thesis-adapter/scripts/template_outline_extractor.py --input <template.md>`

When the user first needs a paste-ready structure, run:

- `python graduation-thesis-adapter/scripts/thesis_scaffold.py --template <template.md>`

### 3. Ground the requested content

Before drafting or rewriting:

- inspect the repository and user materials
- collect evidence for the requested chapter or section
- remove unsupported claims from the draft plan

When the repository is large or the writing target spans multiple modules, run:

- `python graduation-thesis-adapter/scripts/repo_evidence_index.py --root .`
- `python graduation-thesis-adapter/scripts/section_evidence_pack.py --section "<chapter title>" --root .`
- if chapter focus is known, add `--focus "keyword1,keyword2"` or `--focus-file <keywords.txt>` to narrow candidates

### 4. Decide how much to preserve

If an existing draft is present:

- audit which parts can be kept
- mark which parts should be rewritten
- identify placeholders, template residue, and unsupported statements

When the audit is repetitive, run:

- `python graduation-thesis-adapter/scripts/draft_audit.py --input <draft.md>`

### 5. Draft conservatively

When writing:

- follow the target template headings exactly
- write with Chinese undergraduate thesis tone unless the section explicitly requires English
- bind each major statement to project evidence or explicit user input
- mark unresolved facts with `[待补充]`

### 6. Normalize and self-check

Before returning output:

- ensure terminology is stable
- ensure headings match the target template
- ensure no generic filler or unsupported novelty claims remain
- ensure the result is ready to paste into the user's draft

### 7. Build downstream handoff package

When the output is for composer or finalization:

- include keep/rewrite/delete scope
- include forbidden claims and mandatory removals
- include figure/screenshot retain/redraw/capture plan
- include partial replacement boundaries (if any)

## Output Modes

### Template Scaffold

Use when the user needs a paste-ready thesis skeleton matching a school template.

### Chapter Draft

Use when the user asks for one or more chapters to be drafted or expanded.

### Draft Audit

Use when the user asks which parts of an existing thesis to keep, rewrite, or delete.

### Normalization Pass

Use when the user asks to unify terms, chapter names, numbering, or structure.

## References To Load As Needed

- `references/template-adaptation-rules.md`
- `references/template-semantic-mapping.md`
- `references/project-grounding-rules.md`
- `references/evidence-discovery-rules.md`
- `references/draft-audit-rules.md`
- `references/chapter-writing-guides.md`
- `references/terminology-normalization-rules.md`
- `references/final-readiness-rules.md`
- `references/detection-report-rewrite-playbook.md`
- `references/process-material-guides.md`
- `references/finalization-task-rules.md`
- `references/draft-salvage-handoff-playbook.md`
- `references/figure-screenshot-planning-rules.md`

## Bundled Scripts

- `scripts/template_outline_extractor.py`: extract Markdown heading structure into a normalized outline report
- `scripts/thesis_scaffold.py`: generate a clean Markdown scaffold from the target thesis template
- `scripts/repo_evidence_index.py`: scan the repository and group likely thesis evidence files by writing purpose
- `scripts/section_evidence_pack.py`: build a chapter-focused evidence pack from generic path and keyword heuristics, including configurable `--noise-profile` suppression and explainable `score_sources`
- `scripts/draft_audit.py`: emit keep / rewrite / delete oriented audit findings for a thesis draft
- `scripts/chapter_quality_check.py`: inspect one chapter for placeholders, risky claims, and terminology drift
- `scripts/final_readiness_check.py`: inspect the whole draft for remaining placeholder, template, and consistency issues
- `scripts/adapter_handoff_bundle.py`: generate adapter-to-composer handoff artifacts (`normalized_outline`, `section_semantic_map`, `replace_boundaries`, evidence packs, and manifest)

## Example Prompts

- `使用 $graduation-thesis-adapter 先抽取我这个学校论文模板的目录结构，再生成论文骨架。`
- `使用 $graduation-thesis-adapter 按目标模板继续补全“系统测试”章节，不要编造数据。`
- `使用 $graduation-thesis-adapter 审查当前毕业论文初稿，给出 keep / rewrite / delete 建议。`
- `使用 $graduation-thesis-adapter 将现有论文改写到新的学校模板，并统一“系统/平台/模块”等术语。`
