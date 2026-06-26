# university

[![Version](https://img.shields.io/github/v/release/Drew1811266/university?label=version)](https://github.com/Drew1811266/university/releases)
[![License](https://img.shields.io/github/license/Drew1811266/university)](LICENSE)
[![Skill](https://img.shields.io/badge/Agent%20Skill-university-blue)](university/SKILL.md)

`university` is a platform-neutral Agent Skill for university research, official-source verification, China mainland 2026 gaokao volunteer-filling research, and gaokao-to-overseas undergraduate application checks.

当前版本：`0.2.0`

这个仓库的可安装技能包是 [`university/`](university/)。用户只安装这一份 skill，就可以使用院校背景研究、高考志愿防错和高考生海外申请核验三类能力。

## Contents

- [Why This Skill Exists](#why-this-skill-exists)
- [What It Can Do](#what-it-can-do)
- [What It Does Not Do](#what-it-does-not-do)
- [Install](#install)
- [Quick Start](#quick-start)
- [Repository Layout](#repository-layout)
- [Data Status](#data-status)
- [Optional Scripts](#optional-scripts)
- [Source Policy](#source-policy)
- [Version](#version)

## Why This Skill Exists

高校咨询最容易出错的地方，不是“缺少学校介绍”，而是把不同性质的信息混在一起：

- 把学校官网的专业页面误当成某省当年招生计划。
- 把往年投档位次误当成今年录取承诺。
- 把第三方志愿工具或论坛经验当成官方规则。
- 把海外大学 offer 误当成签证、入境、学历认证或执照资格保证。

`university` 的设计目标是把这些边界固定下来：稳定背景可以用资源库辅助，招生、费用、代码、计划、签证、认证等高影响信息必须回到当年官方来源核验。

## What It Can Do

| Mode | Use For | Output |
| --- | --- | --- |
| `gaokao-cn` | 中国大陆 2026 高考志愿研究、招生计划核验、候选池过滤、五维风险拆解 | `研究草稿` / `核验草案`、候选池核验表、风险表、待核验项 |
| `university-profile` | 大学简介、历史、办学定位、校区概况、稳定优势方向 | 学校背景摘要、来源质量提示、可复核资料路径 |
| `gaokao-overseas` | 中国高考生申请海外本科、签证、资金、认证、住宿、安全和国内备选 | 分项核验计划、风险清单、官方来源路径 |

### gaokao-cn Core Capabilities

- 官方来源追踪：31 个 2026 省份包用于记录政策、成绩、一分一段、招生计划和更正状态。
- 招生计划导入辅助：支持从 CSV、网页表格、PDF 文本和 XLSX 抽取材料进入人工复核和标准化流程。
- 候选池过滤：候选项只能来自考生所在省 2026 官方招生计划及更正，不能来自排名或院校库。
- 五维风险拆解：报考资格、投档、专业/调剂、退档、结果可接受度分别呈现。
- 防越权检查：通过检查也只表示材料适合更谨慎复核，不表示可直接提交或保证录取。
- 待核验项列表：缺少当年来源、位次、选科资格、章程限制或更正检查时，必须暴露缺口。

## What It Does Not Do

`university` 不承诺也不生成：

- 可直接提交的最终志愿表。
- `稳录`、`保录取`、`保专业`、`一定录取` 等结论。
- 省级正式填报系统的替代品。
- 签证、入境、学历认证、就业权利或职业执照保证。
- 用第三方排名、论坛、媒体汇总或经验帖支撑最终结论。

高考志愿场景默认输出状态只有：

- `研究草稿`：信息仍缺关键官方来源或只能用于研究。
- `核验草案`：五项关键证据已覆盖，适合进入更谨慎的人工复核，但仍不是可提交志愿表。

## Install

### Generic Agent Skill Install

Install the [`university/`](university/) folder as one skill directory in any Agent Skills-compatible platform.

```text
university/
├── SKILL.md
├── references/
└── scripts/
```

Do not split `gaokao-cn`, `university-profile`, or `gaokao-overseas` into separate skills. They are internal modes routed by `university/SKILL.md`.

### Local Copy

```bash
git clone https://github.com/Drew1811266/university.git
```

Then point your agent platform at the `university/` subdirectory, or copy that folder into the platform's skills directory.

Scripts are optional accelerators. If a platform cannot run scripts, the skill still works from [`SKILL.md`](university/SKILL.md), [`references/`](university/references/), and the bundled schemas.

## Quick Start

Ask natural-language questions. The skill routes to the right internal mode.

### School Background

```text
请介绍一下浙江大学，重点看学校历史、校区和稳定优势方向。不要涉及录取判断。
```

### Gaokao Volunteer Research

```text
我是 2026 年广东物理类考生，612 分，位次 28000，想看计算机或电子信息方向。
不接受中外合作和高收费项目。请先做研究草稿，列出需要核验的官方来源和五维风险。
```

### Uploaded Official Materials

```text
我上传了某省 2026 招生专业目录、一分一段表和计划更正公告。
请按 university 技能生成候选池核验表，不要直接生成可提交志愿表。
```

### Gaokao-to-Overseas

```text
我是中国高考生，想用高考成绩申请澳大利亚本科。
请分别核验大学录取、签证、资金、学历认证、住宿和国内志愿备选风险。
```

## Repository Layout

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

Important files:

- [`university/SKILL.md`](university/SKILL.md): skill entrypoint and routing rules.
- [`university/references/resource-map.md`](university/references/resource-map.md): how agents choose the smallest relevant reference set.
- [`university/references/gaokao-cn-output-status.md`](university/references/gaokao-cn-output-status.md): `研究草稿` / `核验草案` rules.
- [`university/references/gaokao-cn-source-authority.md`](university/references/gaokao-cn-source-authority.md): field-level official source authority.
- [`university/references/gaokao-cn-candidate-pool.md`](university/references/gaokao-cn-candidate-pool.md): candidate-pool filtering rules.
- [`university/references/gaokao-cn-risk-method.md`](university/references/gaokao-cn-risk-method.md): five-dimension risk method.
- [`university/references/university-profile-search-index.md`](university/references/university-profile-search-index.md): school-profile lookup index.

## Data Status

Current bundled data is intentionally conservative:

- 31 China mainland 2026 province packs are present.
- The province packs track official-source status and gaps.
- Bundled official samples are pipeline fixtures, not full national enrollment databases.
- The school profile library is background-only and must not generate gaokao candidate pools.

For final high-impact decisions, users must still verify the official provincial filling system, current enrollment plan, plan corrections, candidate rank, subject eligibility, and university charter restrictions.

## Optional Scripts

The scripts are designed for deterministic checks and repeatable maintenance.

```bash
python3 university/scripts/validate_data.py university
python3 university/scripts/run_self_test.py university
python3 university/scripts/run_behavior_checks.py university
python3 university/scripts/validate_official_data_sources.py university/references/gaokao-cn-official-data-sources.yaml
python3 university/scripts/validate_profile_library.py university --strict
```

Common helper scripts:

- `extract_html_table.py`: extract official webpage tables into CSV for review.
- `extract_pdf_text.py`: extract official PDF text before manual table reconstruction.
- `extract_xlsx_sheet.py`: extract official XLSX worksheets into CSV.
- `normalize_enrollment_plan_csv.py`: normalize official plan CSV into structured JSON.
- `resolve_plan_corrections.py`: remove cancelled/replaced plan items.
- `build_candidate_pool.py`: filter plan items by candidate profile.
- `build_risk_assessment.py`: produce conservative five-dimension risk output.
- `check_submission_gates.py`: run anti-overclaim gate checks.
- `province_readiness.py`: summarize 31 province-pack readiness and freshness.

## Source Policy

Field-level authority matters:

- 2026 provincial enrollment plan and official corrections are highest authority for institution code, major group code, major code, plan count, tuition, campus, and remarks.
- 2026 provincial education examination authority files are highest authority for volunteer mode, batches, filling time, confirmation rules, filing rules, and 征集志愿.
- 2026 university admission charters and provincial plan remarks jointly verify physical exam, single-subject, language, filing ratio, professional admission, and adjustment restrictions.
- University profile pages are only for stable background.
- Third-party tools, rankings, forums, and experience posts are leads only.

## Version

Current release: [`v0.2.0`](https://github.com/Drew1811266/university/releases/tag/v0.2.0)

`0.2.0` focuses on the gaokao-cn safety and research workflow:

- single installable `university` skill;
- platform-neutral structure;
- 31 province-pack coverage;
- candidate-pool and risk schemas;
- import and validation scripts;
- anti-overclaim gates;
- behavior tests and profile-library validation.

## License

See [`LICENSE`](LICENSE).
