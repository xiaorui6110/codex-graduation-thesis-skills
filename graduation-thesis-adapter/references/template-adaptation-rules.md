# Template Adaptation Rules

## Goal

Adapt thesis writing to the user's target template before drafting or rewriting content.

## Required Checks

- Identify whether the template already contains fixed chapter names.
- Identify the heading numbering style.
- Identify required front matter such as Chinese abstract, English abstract, declaration, table of contents.
- Identify required back matter such as references, acknowledgements, appendix.
- Identify whether placeholder subsections may be replaced with project-specific modules.

## Adaptation Strategy

1. Extract the visible heading hierarchy from the target template.
2. Map template headings to normalized semantic categories such as introduction, requirements analysis, overall design, implementation, testing, and conclusion.
3. Keep the user's original heading text and numbering when generating output.
4. Add new subsections only when the template obviously allows expansion or includes placeholder headings.
5. When a template is ambiguous, preserve the structure and ask the model to write conservatively rather than inventing extra chapters.

## Output Requirement

Any scaffold or chapter draft should align with the target template rather than a hard-coded school format.
