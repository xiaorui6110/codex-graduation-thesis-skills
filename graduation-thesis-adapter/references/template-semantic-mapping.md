# Template Semantic Mapping

## Goal

Map different school-specific chapter names to a stable internal semantic type before drafting.

## Common Semantic Types

- `abstract_zh`
- `abstract_en`
- `introduction`
- `requirements_analysis`
- `overall_design`
- `detailed_design_and_implementation`
- `system_testing`
- `conclusion`
- `references`
- `acknowledgements`

## Typical Mapping Examples

- `摘要` -> `abstract_zh`
- `ABSTRACT` -> `abstract_en`
- `绪论`, `引言` -> `introduction`
- `需求分析`, `系统分析` -> `requirements_analysis`
- `系统概要设计`, `总体设计`, `架构设计` -> `overall_design`
- `系统详细设计与实现`, `详细设计`, `系统实现` -> `detailed_design_and_implementation`
- `系统测试`, `测试与验证` -> `system_testing`
- `结论与展望`, `总结与展望` -> `conclusion`
- `参考文献` -> `references`
- `致谢` -> `acknowledgements`

## Usage Rule

Keep the user's original heading text in output.
Use semantic mapping only to choose how to collect evidence and how to write the section.
