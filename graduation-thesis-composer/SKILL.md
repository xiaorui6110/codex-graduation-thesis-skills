---
name: graduation-thesis-composer
description: Use this skill when Codex needs to draft, expand, rewrite, or normalize Chinese undergraduate software engineering thesis content based on adapter outputs and project evidence. Trigger for requests such as "根据 adapter 的章节证据包写正文", "按目标模板补全某一章", "对已有章节做学术化重写", "根据草稿审计结果批量改写", "统一全文术语和叙述风格", "根据检测报告热点重写段落", or "生成定稿前质量检查结果".
---

# Graduation Thesis Composer

## Overview

Use this skill to generate and rewrite thesis prose after structure and evidence planning is done.
Treat `graduation-thesis-adapter` outputs as upstream inputs, and keep writing grounded in project facts and target template structure.
When final-manuscript delivery is required, this skill executes writing + cleanup + readiness checks on a working draft.

## Required Reading Order

1. Read `references/chapter-writing-guides.md`.
2. Read `references/terminology-normalization-rules.md`.
3. Read `references/final-readiness-rules.md`.
4. Read `references/adapter-output-contract.md`.
5. If rewriting hotspots from detection reports, read `references/detection-report-rewrite-playbook.md`.
6. If generating process-stage materials, read `references/process-material-guides.md`.
7. If the user asks for style-level rewrite, read `references/rewrite-style-guides.md`.
8. If the task is final-manuscript delivery, read `references/finalization-task-rules.md`.
9. If the task continues a hand-edited draft or needs runtime screenshots, read `references/docx-draft-salvage-and-runtime-screenshot-playbook.md`.
10. For operation order control in live draft edits, read `references/thesis-revision-operation-checklist.md`.

## Required Inputs

Prefer receiving these adapter outputs before large drafting tasks:

- `normalized_outline`
- `section_semantic_map`
- `section_evidence_pack`
- `draft_audit_report`
- `rewrite_scope`

If upstream outputs are missing, do a conservative fallback draft and explicitly mark assumptions.

## Non-Negotiable Rules

- Follow the user-provided template headings and numbering exactly.
- Bind major statements to project evidence or user-confirmed facts.
- Do not invent metrics, references, test conclusions, deployment scale, or innovation claims.
- Keep unsupported or missing facts as `[待补充]` instead of guessing.
- Preserve meaning while rewriting; do not remove technical substance just to alter wording.
- For user-requested partial replacement, only edit the requested chapter range.

## Workflow

### 1. Confirm writing mode

Classify task as:

- chapter draft
- section rewrite
- terminology normalization
- hotspot rewrite
- final readiness pass

### 2. Load upstream context

Use adapter outputs first. If unavailable, gather the minimum evidence required from repository files.

Before batch drafting from a handoff package, run:

- `python graduation-thesis-composer/scripts/composer_handoff_check.py --handoff-dir <handoff_dir>`

### 2A. Confirm working draft safety

- if editing an existing draft file, keep protected backup path
- if user requests in-place continuation, keep edits within requested section scope

### 3. Draft or rewrite

For each target section:

- match heading semantics to the section purpose
- convert evidence into thesis-style narrative
- keep paragraph logic explicit and conservative
- avoid generic filler and marketing language

When repeated multi-section drafting is needed, run:

- `python graduation-thesis-composer/scripts/batch_chapter_draft_from_handoff.py --handoff-dir <handoff_dir> --output <draft.md>`

### 4. Normalize globally

When user asks for full-manuscript consistency:

- unify core nouns (`系统`, `平台`, `模块`, `功能`)
- align chapter title style and terminology
- remove template residue and placeholder instructions

### 5. Self-check before output

- heading alignment: pass
- evidence grounding: pass
- unsupported claims: removed or marked
- terminology consistency: pass
- ready-to-paste quality: pass
- operation checklist: pass

## Output Modes

### Chapter Draft

Generate one or more requested sections using adapter evidence packs.

### Rewrite Result

Rewrite existing paragraphs while preserving facts and structure intent.

### Normalization Result

Produce terminology and style harmonization for selected chapters or full draft.

### Final Readiness Report

Summarize unresolved issues before final delivery.

## References To Load As Needed

- `references/chapter-writing-guides.md`
- `references/terminology-normalization-rules.md`
- `references/final-readiness-rules.md`
- `references/adapter-output-contract.md`
- `references/detection-report-rewrite-playbook.md`
- `references/process-material-guides.md`
- `references/rewrite-style-guides.md`
- `references/finalization-task-rules.md`
- `references/docx-draft-salvage-and-runtime-screenshot-playbook.md`
- `references/thesis-revision-operation-checklist.md`

## Bundled Scripts

- `scripts/composer_handoff_check.py`: validate adapter handoff package completeness before large drafting tasks
- `scripts/batch_chapter_draft_from_handoff.py`: generate editable multi-section draft text from adapter handoff artifacts, supporting `--chapter-range` selective output
- `scripts/hotspot_rewrite_matrix.py`: generate hotspot-page rewrite matrix templates from report pages for similarity/AIGC rewrite loops
- `scripts/rewrite_scope_from_boundaries.py`: generate section-level rewrite scope draft directly from adapter `replace_boundaries.json`
- `scripts/markdown_to_template_docx.py`: render Markdown thesis content into a target DOCX template while preserving template page settings/styles
- `scripts/docx_layout_refine.py`: perform thesis-oriented DOCX layout normalization (heading/body spacing, paragraph indent, and visual noise cleanup)

## Example Prompts

- `使用 $graduation-thesis-composer 根据 adapter 的“第4章证据包”生成“4.2 功能模块设计”正文。`
- `使用 $graduation-thesis-composer 按草稿审计结果重写 3.2 和 4.3，保留技术事实。`
- `使用 $graduation-thesis-composer 统一当前论文中“系统/平台/模块”术语并给出改写稿。`
- `使用 $graduation-thesis-composer 按检测报告热点重写第 1 章和第 5 章的高风险段落。`
