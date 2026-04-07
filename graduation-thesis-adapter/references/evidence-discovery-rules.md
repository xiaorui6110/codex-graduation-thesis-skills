# Evidence Discovery Rules

## Goal

Keep evidence discovery generic across different repositories.

## Mandatory Constraints

- Do not hard-code project-specific directories such as `materials/`, `doc/`, `db/`, or any repository-private path.
- Do not hard-code project-specific module names, table names, or page names.
- Use generic signals:
  - file suffix
  - file name semantics
  - directory role inference
  - chapter semantic type

## Two-Stage Process

1. Discovery stage:
   - discover candidate files
   - infer coarse directory roles
   - classify files into evidence groups
2. Ranking stage:
   - score candidates by chapter semantic type
   - apply optional user focus keywords
   - filter low-value noise files

## Output Requirement

Evidence pack output should remain explainable:

- target section
- inferred semantic type
- optional focus keywords
- grouped candidates with scores
