# university

[![版本](https://img.shields.io/github/v/release/Drew1811266/university?label=%E7%89%88%E6%9C%AC)](https://github.com/Drew1811266/university/releases)
[![许可证](https://img.shields.io/github/license/Drew1811266/university?label=%E8%AE%B8%E5%8F%AF%E8%AF%81)](LICENSE)
[![技能](https://img.shields.io/badge/%E6%8A%80%E8%83%BD-university-blue)](university/SKILL.md)

`university` 是一个平台中立的高校研究类智能体技能，用于院校背景整理、官方来源核验、中国大陆 2026 高考志愿研究，以及中国高考生海外本科申请核验。

当前版本：`0.2.0`

这个仓库的可安装技能包是 [`university/`](university/)。用户只安装这一份技能，就可以使用院校背景研究、高考志愿防错和高考生海外申请核验三类能力。

## 目录

- [为什么需要这个技能](#为什么需要这个技能)
- [它能做什么](#它能做什么)
- [它不做什么](#它不做什么)
- [安装方式](#安装方式)
- [快速开始](#快速开始)
- [仓库结构](#仓库结构)
- [数据状态](#数据状态)
- [可选脚本](#可选脚本)
- [来源规则](#来源规则)
- [版本](#版本)

## 为什么需要这个技能

高校咨询最容易出错的地方，不是“缺少学校介绍”，而是把不同性质的信息混在一起：

- 把学校官网的专业页面误当成某省当年招生计划。
- 把往年投档位次误当成今年录取承诺。
- 把第三方志愿工具或论坛经验当成官方规则。
- 把海外大学录取通知误当成签证、入境、学历认证或执照资格保证。

`university` 的设计目标是把这些边界固定下来：稳定背景可以用资源库辅助，招生、费用、代码、计划、签证、认证等高影响信息必须回到当年官方来源核验。

## 它能做什么

| 模式 | 适用场景 | 输出 |
| --- | --- | --- |
| `gaokao-cn` | 中国大陆 2026 高考志愿研究、招生计划核验、候选池过滤、五维风险拆解 | `研究草稿` / `核验草案`、候选池核验表、风险表、待核验项 |
| `university-profile` | 大学简介、历史、办学定位、校区概况、稳定优势方向 | 学校背景摘要、来源质量提示、可复核资料路径 |
| `gaokao-overseas` | 中国高考生申请海外本科、签证、资金、认证、住宿、安全和国内备选 | 分项核验计划、风险清单、官方来源路径 |

### `gaokao-cn` 核心能力

- 官方来源追踪：31 个 2026 省份包用于记录政策、成绩、一分一段、招生计划和更正状态。
- 招生计划导入辅助：支持从 CSV、网页表格、PDF 文本和 XLSX 抽取材料进入人工复核和标准化流程。
- 候选池过滤：候选项只能来自考生所在省 2026 官方招生计划及更正，不能来自排名或院校库。
- 五维风险拆解：报考资格、投档、专业/调剂、退档、结果可接受度分别呈现。
- 防越权检查：通过检查也只表示材料适合更谨慎复核，不表示可直接提交或保证录取。
- 待核验项列表：缺少当年来源、位次、选科资格、章程限制或更正检查时，必须暴露缺口。

## 它不做什么

`university` 不承诺也不生成：

- 可直接提交的最终志愿表。
- `稳录`、`保录取`、`保专业`、`一定录取` 等结论。
- 省级正式填报系统的替代品。
- 签证、入境、学历认证、就业权利或职业执照保证。
- 用第三方排名、论坛、媒体汇总或经验帖支撑最终结论。

高考志愿场景默认输出状态只有：

- `研究草稿`：信息仍缺关键官方来源，或只能用于研究。
- `核验草案`：五项关键证据已覆盖，适合进入更谨慎的人工复核，但仍不是可提交志愿表。

## 安装方式

### 通用智能体技能安装

把 [`university/`](university/) 文件夹作为一个完整技能目录安装到兼容智能体技能规范的平台。

```text
university/
├── SKILL.md
├── references/
└── scripts/
```

不要把 `gaokao-cn`、`university-profile` 或 `gaokao-overseas` 拆成多个独立技能。它们是由 `university/SKILL.md` 路由的内部模式。

### 本地复制

```bash
git clone https://github.com/Drew1811266/university.git
```

然后让你的智能体平台指向 `university/` 子目录，或把这个文件夹复制到平台的技能目录中。

脚本只是可选增强。如果平台不能运行脚本，技能仍可依靠 [`SKILL.md`](university/SKILL.md)、[`references/`](university/references/) 和内置 schema 手动执行同一套流程。

## 快速开始

直接用自然语言提问即可。技能会自动进入对应内部模式。

### 院校背景

```text
请介绍一下浙江大学，重点看学校历史、校区和稳定优势方向。不要涉及录取判断。
```

### 高考志愿研究

```text
我是 2026 年广东物理类考生，612 分，位次 28000，想看计算机或电子信息方向。
不接受中外合作和高收费项目。请先做研究草稿，列出需要核验的官方来源和五维风险。
```

### 上传官方材料

```text
我上传了某省 2026 招生专业目录、一分一段表和计划更正公告。
请按 university 技能生成候选池核验表，不要直接生成可提交志愿表。
```

### 高考生海外申请

```text
我是中国高考生，想用高考成绩申请澳大利亚本科。
请分别核验大学录取、签证、资金、学历认证、住宿和国内志愿备选风险。
```

## 仓库结构

```text
.
├── README.md
├── LICENSE
└── university/
    ├── SKILL.md
    ├── references/
    │   ├── resource-map.md
    │   ├── gaokao-cn-*.md / *.yaml / *.csv
    │   ├── university-profile-*.md
    │   ├── *schema.json
    │   └── overseas / report / evidence references
    └── scripts/
        ├── validate_data.py
        ├── run_self_test.py
        ├── build_candidate_pool.py
        ├── build_risk_assessment.py
        └── import, validation, monitoring helpers
```

重要文件：

- [`university/SKILL.md`](university/SKILL.md)：技能入口和路由规则。
- [`university/references/resource-map.md`](university/references/resource-map.md)：帮助智能体选择最小必要 reference 集合。
- [`university/references/gaokao-cn-output-status.md`](university/references/gaokao-cn-output-status.md)：`研究草稿` / `核验草案` 输出状态规则。
- [`university/references/gaokao-cn-source-authority.md`](university/references/gaokao-cn-source-authority.md)：字段级官方来源权威规则。
- [`university/references/gaokao-cn-candidate-pool.md`](university/references/gaokao-cn-candidate-pool.md)：候选池过滤规则。
- [`university/references/gaokao-cn-risk-method.md`](university/references/gaokao-cn-risk-method.md)：五维风险判定方法。
- [`university/references/university-profile-search-index.md`](university/references/university-profile-search-index.md)：院校背景库检索索引。

## 数据状态

当前内置数据保持保守定位：

- 已包含 31 个中国大陆 2026 省份包。
- 省份包用于追踪官方来源状态和缺口。
- 内置官方样本是管道测试用 fixture，不是全国全量招生数据库。
- 院校背景库只用于学校背景摘要，不能生成高考候选池。

涉及高影响决策时，用户仍必须核验省级正式填报系统、当年招生计划、计划更正、考生位次、选科资格和高校招生章程限制。

## 可选脚本

脚本用于可重复的校验、导入和维护。

```bash
python3 university/scripts/validate_data.py university
python3 university/scripts/run_self_test.py university
python3 university/scripts/run_behavior_checks.py university
python3 university/scripts/validate_official_data_sources.py university/references/gaokao-cn-official-data-sources.yaml
python3 university/scripts/validate_profile_library.py university --strict
```

常用辅助脚本：

- `extract_html_table.py`：把官方网页表格抽取为待复核 CSV。
- `extract_pdf_text.py`：抽取官方 PDF 文本，供人工重建表格。
- `extract_xlsx_sheet.py`：把官方 XLSX 工作表抽取为 CSV。
- `normalize_enrollment_plan_csv.py`：把官方招生计划 CSV 标准化为结构化 JSON。
- `resolve_plan_corrections.py`：剔除已取消或已替换的招生计划条目。
- `build_candidate_pool.py`：按考生画像过滤招生计划条目。
- `build_risk_assessment.py`：生成保守的五维风险输出。
- `check_submission_gates.py`：运行防越权门禁检查。
- `province_readiness.py`：汇总 31 个省份包的就绪度和时效状态。

## 来源规则

字段级权威来源必须分开处理：

- 2026 省级招生计划及官方更正，是院校代码、专业组代码、专业代码、计划人数、学费、校区和备注的最高依据。
- 2026 省级教育考试院文件，是志愿模式、批次、填报时间、确认规则、投档规则和征集志愿规则的最高依据。
- 2026 高校招生章程与省级计划备注共同核验体检、单科、语种、投档比例、专业录取办法和调剂限制。
- 大学简介页面只用于稳定背景，不得替代招生计划。
- 第三方工具、排名、论坛和经验帖只能作为线索。

## 版本

当前发布版：[`v0.2.0`](https://github.com/Drew1811266/university/releases/tag/v0.2.0)

`0.2.0` 的重点是强化 `gaokao-cn` 的安全边界和研究流程：

- 单一可安装的 `university` 技能。
- 平台中立结构。
- 31 个省份包覆盖。
- 候选池和风险 schema。
- 导入与校验脚本。
- 防越权门禁。
- 行为测试和院校库校验。

## 许可证

见 [`LICENSE`](LICENSE)。
