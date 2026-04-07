# Adapter Output Contract

## Goal

Define the minimum handoff artifacts required by `graduation-thesis-composer`.

## Required Artifacts

- `handoff_manifest.json`
- `normalized_outline.md`
- `section_semantic_map.json`
- `replace_boundaries.json`
- `repo_evidence_index.md`
- `thesis_scaffold.md`
- one or more `section_evidence_pack_<slug>.md`

## Optional Artifacts

- `draft_audit_report.md`

## Contract Rule

- Composer should consume adapter outputs first.
- If required artifacts are missing, composer should either:
  - request missing artifacts, or
  - proceed in conservative fallback mode and mark assumptions.
