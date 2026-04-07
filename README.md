# Codex Graduation Thesis Skills

面向 Codex / Codex CLI 的毕业设计论文辅助 Skill 仓库，用于处理常见的本科毕业设计论文规划、模板适配、正文撰写、局部修订与终稿整理任务。

## 来源说明

本仓库基于公开项目的思路整理、调整并扩展而来，当前版本结合毕业设计论文场景，对 Skill 命名、工作流拆分、参考规则与配套脚本做了重新组织。

- 上游参考项目：[`lishix520/academic-paper-skills`](https://github.com/lishix520/academic-paper-skills/)、[AAASS554/codex-academic-paper-skills](https://github.com/AAASS554/codex-academic-paper-skills)
- 当前仓库并非对原项目的逐字镜像，而是结合实际使用需求做了结构化改造
- 若继续分发或二次修改本仓库，建议保留此来源说明

感谢原项目提供的公开思路与基础材料。

## 项目概览

这个仓库当前提供两个可组合使用的 Skill：

| Skill | 作用 | 适合阶段 |
| --- | --- | --- |
| `graduation-thesis-adapter` | 模板适配、目录归一、证据梳理、保留/重写边界划分 | 前期规划、结构调整、初稿审查 |
| `graduation-thesis-composer` | 正文生成、局部改写、术语统一、终稿检查与整理 | 中后期撰写、修订、收尾 |

推荐工作流：

1. 先用 `graduation-thesis-adapter` 读取学校模板、抽取章节结构并建立证据映射。
2. 再用 `graduation-thesis-composer` 基于结构和证据生成正文、执行重写和终稿检查。

## 快速开始

### 1. 安装 Skill

```bash
这部分有由于版本迭代迅速，建议查看官方文档：https://developers.openai.com/codex/skills
```

### 2. 先做结构规划

```text
请使用 $graduation-thesis-adapter 基于我当前项目仓库、学校论文模板和现有初稿，输出论文目录骨架、章节证据映射、保留/重写建议，以及后续交给 composer 的 handoff 内容。
```

### 3. 再做正文补写或改写

```text
请使用 $graduation-thesis-composer 根据 adapter 生成的章节证据包，补写“第4章 系统详细设计”中的 4.2 和 4.3，不要编造实验数据或运行指标。
```

## 解决的问题

本仓库主要面向以下场景：

- 根据学校模板或示例论文快速生成可补写的论文骨架
- 从真实项目仓库中提取可写入论文的章节证据
- 审查现有初稿，区分可保留内容与应重写内容
- 按查重报告或 AIGC 报告对高风险段落做定向修订
- 统一整篇论文中的术语、章节命名和叙述口径
- 在终稿前检查占位符、模板残留、一致性和基础版式问题

## 仓库结构

```text
.
├─ graduation-thesis-adapter/
│  ├─ SKILL.md
│  ├─ agents/
│  ├─ references/
│  └─ scripts/
├─ graduation-thesis-composer/
│  ├─ SKILL.md
│  ├─ agents/
│  ├─ references/
│  └─ scripts/
└─ README.md
```

每个 Skill 目录通常包含：

- `SKILL.md`：Skill 的入口说明、工作流和硬性约束
- `agents/openai.yaml`：Agent 元数据与默认提示配置
- `references/`：模板适配、章节写作、终稿检查等规则文档
- `scripts/`：处理目录抽取、证据索引、审查与 handoff 的辅助脚本

## Skill 说明

### graduation-thesis-adapter

负责前置规划与结构适配，重点是“先搞清楚该怎么写，再决定写哪些内容”。

典型任务：

- 抽取学校模板目录结构
- 生成论文骨架
- 从项目仓库中收集章节证据
- 审查初稿中的保留区、重写区、删除区
- 产出交给 `composer` 的 handoff 材料

内置脚本示例：

- `template_outline_extractor.py`
- `thesis_scaffold.py`
- `repo_evidence_index.py`
- `section_evidence_pack.py`
- `draft_audit.py`
- `adapter_handoff_bundle.py`

### graduation-thesis-composer

负责正文生成、局部改写与终稿整理，重点是“在已知结构和证据前提下，稳定地产出可粘贴内容”。

典型任务：

- 根据 adapter 产出的证据包撰写章节正文
- 对指定章节或段落做保守型重写
- 统一全文术语与叙述风格
- 按检测报告热点重写高风险内容
- 执行终稿前的完整性检查与基础排版整理

内置脚本示例：

- `composer_handoff_check.py`
- `batch_chapter_draft_from_handoff.py`
- `hotspot_rewrite_matrix.py`
- `rewrite_scope_from_boundaries.py`
- `markdown_to_template_docx.py`
- `docx_layout_refine.py`

## 使用方式

如果你维护的是自己的 Skills 仓库，也可以直接把这两个目录并入现有结构。

### 典型流程

1. 用 `graduation-thesis-adapter` 读取模板并生成规范化目录。
2. 用 `graduation-thesis-adapter` 收集项目证据并形成章节映射。
3. 如果已有初稿，先做保留/重写审查，避免整篇盲改。
4. 将结构、证据包和重写边界交给 `graduation-thesis-composer`。
5. 用 `graduation-thesis-composer` 生成正文、执行局部改写并统一术语。
6. 在接近终稿时完成完整性检查与基础文档整理。

## Prompt 示例

### 先做模板适配与论文规划

```text
请使用 $graduation-thesis-adapter 基于我当前项目仓库、学校论文模板和现有初稿，输出论文目录骨架、章节证据映射、保留/重写建议，以及后续交给 composer 的 handoff 内容。
```

### 根据证据包补写章节

```text
请使用 $graduation-thesis-composer 根据 adapter 生成的章节证据包，补写“第4章 系统详细设计”中的 4.2 和 4.3，不要编造实验数据或运行指标。
```

### 按检测报告处理高风险段落

```text
请使用 $graduation-thesis-composer 根据最新查重报告，对第1章和第5章的高风险段落做定向改写，保留原有技术事实，并标记仍需人工补充的内容。
```

### 先审查已有初稿

```text
请使用 $graduation-thesis-adapter 审查我当前毕业论文初稿，区分哪些段落可以保留、哪些需要重写、哪些属于模板残留，并输出后续改写边界。
```

## 设计原则

- 以学校模板为格式约束，以项目仓库和用户材料为事实依据
- 先做结构适配和证据映射，再做正文生成和重写
- 对已有初稿采用保守式改写，尽量保留可验证内容
- 对缺失事实使用明确占位，而不是凭空补造
- 优先处理高风险章节和高收益修改点，减少整篇返工
- 在终稿阶段显式检查术语、编号、占位符和格式残留

## License

本仓库使用 `MIT License`。
