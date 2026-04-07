# Detection Report Rewrite Playbook

## Goal

Use similarity or AIGC detection reports as rewrite-priority signals, not as project-fact sources.

## Input

- latest detection report (PDF, screenshot, or extracted text)
- current thesis draft
- target threshold if provided by the user

## Workflow

1. Extract hotspot pages and sections from the report.
2. Map hotspots to thesis headings.
3. Classify rewrite intensity per section:
   - `light`: wording cleanup
   - `medium`: sentence logic rebuild
   - `heavy`: paragraph-level restructure
4. Preserve project facts while rewriting expression.
5. Re-run checks on revised sections, then continue iteratively.

## Rewrite Constraints

- Do not fabricate project evidence.
- Do not remove core technical meaning only to chase score.
- Prefer high-yield hotspot sections first.
- Keep references, chapter order, and figure/table intent stable unless unsupported.
