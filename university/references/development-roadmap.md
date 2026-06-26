# University Skill Development Roadmap

## 目录

- [定位](#定位)
- [安装与结构原则](#安装与结构原则)
- [当前缺陷](#当前缺陷)
- [需要新增的能力](#需要新增的能力)
- [数据与接口计划](#数据与接口计划)
- [执行阶段](#执行阶段)
- [验收标准](#验收标准)
- [维护规则](#维护规则)

## 定位

`university` 必须保持为一个可安装的通用 Agent Skill。用户只安装 `university/` 目录，就能使用三类能力：

1. `gaokao-cn`：中国大陆普通高考志愿决策辅助，优先支持 2026 志愿填报。
2. `university-profile`：院校背景、历史、定位、校区和稳定特色核验。
3. `gaokao-overseas`：中国高考生海外本科申请、签证、资金、认证和国内备选路径核验。

当前核心升级目标不是“保证录取”或“生成可提交志愿表”，而是把技能建设为可审计、可复核、可停止越权推断的志愿决策辅助系统。最高优先级仍是 `gaokao-cn`，但后续优化重点放在用户材料导入、官方来源审计和报告可读性，不追求全量省份数据闭环作为必须完成的产品目标。

## 安装与结构原则

- 保持单一技能入口：`university/SKILL.md` 是唯一入口，不拆成同级可安装子技能。
- 保持平台中立：不依赖 Codex、OpenAI 或某个 Agent 平台的专属 metadata、工具名、绝对路径或父目录引用。
- 资源只放在标准资源目录：`references/` 存放说明、schema、样例、结构化数据；`scripts/` 存放可选验证和生成脚本。
- `SKILL.md` 只保留路由、硬规则和资源入口；细节放入 `references/`，避免上下文膨胀。
- 所有开发说明也必须服务于技能维护本身；不要新增 `README.md`、`CHANGELOG.md`、安装教程等非技能运行资源。
- 脚本必须是可选增强；当宿主 Agent 不能执行脚本时，仍可按 `SKILL.md` 和 `references/` 手动执行同一流程。

## 当前缺陷

### 1. 省级 2026 实时闭环仍不完整

现状已经有 31 个省级 province pack，但多数关键门槛仍是 `partial`、`needs_recheck` 或 `monitor`。真实高考志愿场景仍需要持续补齐成绩发布、复核截止、最低控制线、一分一段表、志愿填报时间、招生专业目录、计划更正、系统入口和最后检查时间。

风险：Agent 可能知道“应该查什么”，但无法形成“当前省份哪些关键文件已经发布、哪些仍缺失、哪些发生更正”的闭环。

优化方向：

- 维护 31 个省级 `gaokao-cn-province-*-2026.yaml`，并使用 `scripts/province_readiness.py` 暴露每个省的来源缺口和防越权门槛缺口。
- `province_readiness.py` 必须把 `province_pack_status` 和最终 `output_status` 分开：前者表达省级来源核验进度，后者只表达输出是 `研究草稿` 还是 `核验草案`。
- 每个 pack 必须有 `published_at`、`last_checked_at`、`status`、`source_url`、`source_type`。
- 计划更正必须支持 `cancelled`、`replaced`、`added`、`count_changed`、`code_changed`。
  - `detect_source_changes.py` 负责状态汇总；`scripts/snapshot_sources.py` 负责本地官方抽取文件的 SHA-256 内容摘要对比，发现 `changed` 或 `missing` 后必须回到官方来源复核。

### 2. 招生计划数据结构存在，但缺少导入能力

`enrollment-plan-item.schema.json` 已定义基本字段，`scripts/normalize_enrollment_plan_csv.py` 已支持 CSV 标准化和 `--evidence-output` 证据台账输出；仍缺少直接从 PDF、Excel、网页、用户上传截图转换为标准数据的稳定导入器。

风险：候选池原则上要求来自 2026 官方招生专业目录，但当前技能还没有稳定机制把目录转成可筛选集合。

优化方向：

- 新增招生计划导入规范：PDF、Excel、CSV、网页表格、截图 OCR 的来源等级和人工复核规则。
- 已有 CSV 标准化脚本；后续增加 PDF/Excel/网页表格导入适配器。
- 增加重复代码、缺失代码、组内专业缺失、学费缺失、校区缺失、备注缺失的校验。
- 对用户上传截图含考生号、手机号、身份证号、验证码的情况，先提醒遮挡敏感信息。

### 3. 风险分析仍偏规则化，缺少可执行判定框架

技能已经要求五维风险，`scripts/build_risk_assessment.py` 已加入历史样本数、计划人数变化和位次波动的量化检查；后续仍需补强专业组连续性、拆分合并、新增专业组和异常波动的真实数据映射。

风险：Agent 可能把“投档风险低”误写成整体低风险，忽略专业/调剂、退档或结果不可接受风险。

优化方向：

- 固定五维风险输出：报考资格、投档、专业录取或调剂、退档、结果可接受度。
- 为每一维定义所需证据、可判定条件、停止量化条件和输出模板。
- 新增历史位次数据结构，记录年份、批次、科类、院校专业组、专业、最低位次、计划人数、是否可比。
- 处理计划人数大幅变化、专业组拆分合并、专业迁移、校区变化、项目性质变化。
- 明确“数据不足，不能判定冲稳保”的触发条件。

### 4. 候选池生成仍缺少端到端工作流

技能已禁止用排名库生成高考候选池，但目前缺少从 2026 招生计划到候选池、再到五维风险、再到排序建议的中间表结构。

风险：Agent 可能绕过候选池核验表，直接给出学校推荐。

优化方向：

- 新增“候选池核验表”模板。
- 候选池必须先经过省份、年份、批次、科类或选科、资格、费用、校区、项目性质、用户底线过滤。
- 排序建议必须引用候选池核验表条目，不得凭学校声誉或排名补充。
- 最终输出前检查 `研究草稿` 或 `核验草案` 状态门槛。

### 5. 院校库仍是大体量 Markdown，维护和验证成本高

中国院校库按 50 校分段存放，便于人工查阅，但不利于机器校验字段级来源、重复项、B/C 等级措辞和更名信息。

风险：B 级条目虽然已经有较谨慎措辞，但仍可能因为内容写得具体而被误用为精确核验事实。

优化方向：

- 保留 Markdown 作为可读背景库，但建立结构化源数据或索引。
- 新增 profile library 校验脚本，检查 `profile_source_status`、`history_evidence`、`campus_evidence`、`institution_type_evidence`、`strengths_evidence`、`source_url`。
- B 级条目不得出现“精确简介页核验”“已确认”等强断言。
- C 级条目必须输出“来源需复核”。
- 软科 2026 只可说明入库覆盖范围，不得进入高考候选池、排序或风险判断。

### 6. 来源权威规则仍分散

`gaokao-cn-source-authority.md` 和 `source-evidence-ledger.md` 已按字段定义权威来源，但旧通用报告和部分资源文件仍保留“2025 年及以后”口径，容易让 Agent 在 2026 高考最终填报任务中误用历史信息。

风险：不同引用文件之间出现隐性冲突，尤其是普通院校资料和高考志愿资料混用时。

优化方向：

- 所有高考最终填报结论统一采用“2026 官方来源”口径。
- 2025 或更早数据只允许作为历史比较、趋势参考、待核验背景。
- 普通院校背景可以使用当前官方简介，但不得替代招生计划。
- 海外申请按目标入学季和当前官方政策处理，不能套用中国高考 2026 规则。

### 7. 行为测试还不是可执行回归测试

`gaokao-cn-behavior-cases.yaml` 已列出关键行为，但没有脚本对输出进行最小断言，也没有把错误话术和必须出现的状态门槛转成可跑检查。

风险：技能修订后无法自动发现回归，例如重新出现“保证录取”“缺少计划也生成可提交志愿表”等问题。

优化方向：

- 为行为用例补充 machine-checkable checks。
- 新增行为检查脚本，支持列出用例、校验用例结构、对样例输出执行 must/must-not 断言。
- 后续增加真实前向测试 transcript，覆盖广东、四川和一个数据不足省份。

### 8. 脚本依赖和跨平台说明不足

当前脚本依赖 Python 3 和 PyYAML，但技能没有集中说明依赖、失败降级路径和平台限制。

风险：不同 Agent 平台安装后，用户以为脚本是强依赖；或脚本失败时 Agent 不知道可以回到手动 schema 检查。

优化方向：

- 在资源地图中集中列出脚本用途、依赖和失败降级路径。
- 脚本错误信息保持明确，不把依赖失败写成技能不可用。
- `validate_data.py` 增加对关键维护文件存在性的检查。

### 9. 海外申请能力仍偏防错清单

海外申请已覆盖录取、签证、资金、认证、住宿、安全和国内备选，`scripts/build_overseas_plan.py` 已能按国家/地区、路径和入学季生成核验计划；后续仍需把国家模板扩展为更细的时间轴、材料清单和状态表。

风险：用户得到的是“需要核验什么”，而不是可执行的申请计划。

优化方向：

- 建立国家/地区模板：英国、美国、加拿大、澳大利亚、日本、韩国、新加坡、香港、澳门。
- 固定输出：录取可行性、语言路径、签证资金、学历认证、住宿安全、押金退费、国内志愿冲突。
- 把 offer、签证、入境、认证、就业和执业资格明确拆成独立证据。

### 10. 普通院校资料能力缺少更新队列

院校库已有 A/B/C 和复核规则，`scripts/profile_maintenance_queue.py` 已能输出 B/C 和来源待补充条目的维护队列；后续还需要接入“用户最近查询”和官网栏目变化监控。

风险：维护精力继续消耗在大规模补齐静态简介，而不是优先修复用户实际会查的高风险条目。

优化方向：

- 增加 profile 更新优先级规则。
- 对发生更名、合并、转设、校区迁移、办学性质变化的学校建立复核队列。
- 允许未收录学校走“官网实时核验”，不强制扩库后再回答。

## 需要新增的能力

### A. Province Pack Builder

目标：为 31 个省级 2026 pack 提供统一模板、字段检查和状态更新方式。

能力：

- 从省份名生成标准文件名。
- 校验必填 gate。
- 输出“缺失关键来源”清单。
- 生成当日检查摘要。

### B. Enrollment Plan Importer

目标：把省级招生专业目录和更正文件整理成候选池可用数据。

当前实现：

- 已支持官方招生计划或计划更正 CSV 标准化到 `enrollment-plan-item` JSON。
- 已支持官方网页表格抽取为 CSV，先复核再标准化。
- 已支持官方 PDF 抽取为待审阅文本；仍需人工重建表格结构后才能标准化。
- 已支持官方 XLSX 工作表抽取为 CSV，先复核再标准化。
- 已支持本地官方抽取文件快照，便于发现样本、抽取结果或来源文件被替换后未复核的情况。
- 已内置四川 2026 招生计划更正官方抽样数据，覆盖删除项和更正项。
- 已内置北京 2026 学校级招生计划汇总官方抽样数据；该数据不含专业组和专业代码，不能生成候选池。
- 已记录北京 2026 招生专业目录官方入口，但尚未抽取专业组级全量计划。

能力：

- 支持 PDF、Excel、CSV、网页表格和用户上传截图。
- 记录每个字段的来源文件、页码或表格位置。
- 标记更正状态和替换关系。
- 输出标准 `enrollment-plan-item` 列表。

### C. Plan Correction Resolver

目标：确保旧计划被更正后不会继续进入排序。

能力：

- 识别新增、取消、替换、代码变化、计划人数变化。
- 建立 `replaces` 和 `replaced_by` 关系。
- 输出最终有效计划视图。

### D. Historical Rank Comparator

目标：支持同省、同批次、同科类、同院校专业组或专业的历史位次比较。

当前实现：

- 已支持官方历史投档位次 CSV 标准化到 `historical-rank-item` JSON。
- 已内置广东 2025 本科普通类历史类、物理类官方投档位次抽样数据。
- 已明确历史位次只能作为同口径比较，不能替代 2026 招生计划、章程和更正核验。

能力：

- 记录历史投档最低位次、专业最低位次、计划人数、批次、科类、选科。
- 判断专业组连续性。
- 标记拆分合并、新增、历史不可比、异常波动。
- 数据不足时停止冲稳保量化。

### D2. Score Segment Normalizer

目标：支持省级 2026 一分一段表结构化，供位次确认和报告引用。

当前实现：

- 已新增 `score-segment-item.schema.json`。
- 已新增 `scripts/normalize_score_segment_csv.py`。
- 已内置北京 2026 一分一段官方抽样数据，覆盖高分段、本科控制线附近和区间分数段。

能力：

- 记录省份、年份、科类、分数或分数区间、本段人数、累计人数、来源 URL 和证据等级。
- 支持抽样数据和后续全量数据共用同一结构。
- 禁止用第三方位次换算表替代省级官方一分一段。

### E. Five-Dimension Risk Engine

目标：把单一风险标签改成五维风险矩阵。

能力：

- 每一维输出风险等级、证据、触发原因、待核验项和用户底线影响。
- 支持“投档风险低但调剂风险高”的混合结论。
- 阻止“整体低风险”覆盖具体风险。

### F. Candidate Pool Review Table

目标：在志愿排序前先生成可审计候选池。

能力：

- 每个候选项显示可填依据、代码、组内专业、计划人数、选科、费用、校区、备注、更正状态。
- 显示过滤原因：资格不符、费用超限、校区不可接受、项目性质不可接受、缺少 2026 证据。
- 排序建议只能引用通过核验的候选项。

### G. Executable Behavior Eval

目标：让行为用例可执行。

能力：

- 校验用例结构。
- 对示例输出执行 must-contain 和 must-not-contain 检查。
- 为后续前向测试保存失败原因。

### H. Profile Library Validator

目标：防止静态院校库继续产生强断言和字段证据混淆。

能力：

- 统计 A/B/C 条目数量。
- 检查 B/C 等级措辞。
- 检查字段级证据是否缺失。
- 标记旧时效口径和高考场景冲突。

### I. Resource Map

目标：让不同 Agent 平台能快速找到该读哪些引用文件。

能力：

- 按任务类型列出必读、可选和禁止误用文件。
- 列出脚本用途、依赖和降级路径。
- 明确大文件加载策略。

### J. Overseas Application Planner

目标：把海外申请从防错清单升级为可执行计划。

能力：

- 国家/地区模板。
- 时间轴和材料清单。
- 录取、签证、资金、认证、住宿、安全、国内备选的独立状态。

## 数据与接口计划

必须保持在单一 skill 内：

```text
university/
├── SKILL.md
├── references/
│   ├── resource-map.md
│   ├── development-roadmap.md
│   ├── gaokao-cn-province-*-2026.yaml
│   ├── *.schema.json
│   ├── gaokao-cn-*.md
│   ├── gaokao-cn-*.yaml
│   └── university-profiles-*.md
└── scripts/
    ├── validate_data.py
    ├── check_links.py
    ├── detect_source_changes.py
    ├── snapshot_sources.py
    ├── extract_html_table.py
    ├── extract_pdf_text.py
    ├── extract_xlsx_sheet.py
    ├── province_readiness.py
    ├── build_markdown.py
    ├── build_gaokao_report.py
    ├── run_behavior_checks.py
    ├── validate_official_data_sources.py
    ├── validate_profile_library.py
    ├── profile_maintenance_queue.py
    └── build_overseas_plan.py
```

新增文件必须满足：

- 所有路径从 skill 根目录相对引用。
- 不引用父目录。
- 不要求平台专属工具。
- 不把 Markdown 当作唯一长期结构化数据源；关键字段要有 JSON schema、YAML 或脚本校验入口。

## 执行阶段

### Phase 1: 结构和可维护性

- 新增 `references/development-roadmap.md`。
- 新增 `references/resource-map.md`。
- 更新 `SKILL.md`，要求复杂任务先读资源地图。
- 新增 `scripts/run_behavior_checks.py`。
- 新增 `scripts/validate_profile_library.py`。
- 扩展 `validate_data.py`，检查资源地图、开发路线图和行为用例 checks。
- 新增 `references/gaokao-cn-candidate-pool.md`、`references/gaokao-cn-risk-method.md` 和 `references/historical-rank-item.schema.json`。
- 新增 `references/gaokao-cn-province-pack-template.yaml`、`references/gaokao-cn-province-pack-seeds.csv`、`scripts/create_province_pack.py` 和 `scripts/create_all_province_packs.py`。
- 新增 `references/gaokao-cn-enrollment-plan-import.md`、`references/gaokao-cn-plan-corrections.md`、`scripts/normalize_enrollment_plan_csv.py` 和 `scripts/resolve_plan_corrections.py`。
- 生成 31 省 `needs_recheck` 草稿 province pack 覆盖，并新增 `references/gaokao-cn-candidate-profile-sample.json` 与 `scripts/build_candidate_pool.py`。
- 新增 `references/gaokao-cn-historical-rank-sample.csv`、`scripts/normalize_historical_rank_csv.py` 和 `scripts/build_risk_assessment.py`，用于可比历史位次和五维风险评估。
- 新增 `references/gaokao-cn-submission-gates.md`、`references/gaokao-cn-submission-evidence-sample.json` 和 `scripts/check_submission_gates.py`，用于五项防越权门禁。
- 新增 `scripts/run_self_test.py`，用于离线跑通样例数据链路并断言关键安全行为。
- 新增 `scripts/province_readiness.py`，用于把 31 省 pack 的关键门槛拆成可计算 readiness。
- 扩展 `scripts/province_readiness.py`，输出 `province_pack_status_counts`、`province_pack_status`、`source_gate_ready_count` 和 `freshness_status`，避免 31 个省份包在维护视图里全部塌缩为同一个 `研究草稿` 标签。
- 新增 `scripts/build_gaokao_report.py`，用于从候选池、五维风险和门禁结果生成保守 Markdown 报告。
- 新增 `scripts/profile_maintenance_queue.py`，用于输出院校库 B/C 和来源待补充条目的复核队列。
- 新增 `scripts/build_overseas_plan.py`，用于生成高考生海外本科申请核验计划。
- 新增 `references/official-data-source.schema.json`、`references/score-segment-item.schema.json`、`scripts/validate_official_data_sources.py` 和 `scripts/normalize_score_segment_csv.py`，用于区分样本、入口、学校级汇总和专业级全量数据。
- 新增 `scripts/extract_html_table.py`，用于把官方网页表格先抽取为 CSV，再进入人工复核和标准化流程。
- 新增 `scripts/extract_pdf_text.py`，用于把官方 PDF 先抽取为待审阅文本；不得直接把 PDF 文本当作候选池数据。
- 新增 `scripts/extract_xlsx_sheet.py`，用于无第三方依赖地把官方 XLSX 工作表抽取为 CSV，再进入人工复核和标准化流程。
- 新增 `scripts/snapshot_sources.py`，用于对本地官方抽取文件建立 SHA-256 快照并对比 `new/unchanged/changed/missing` 状态。
- 扩展 `scripts/province_readiness.py`，拆分 `source_ready_from_pack` 与 `precheck_candidate_from_pack`，防止官方入口发布被误判为全量候选池可用；旧字段 `submit_ready_possible_from_pack` 仅为兼容保留。
- 扩展 `scripts/build_markdown.py`，使用 readiness 逻辑生成包含省份包状态、最终状态、已核验门槛和今日复核状态的 Markdown 表。
- 扩展 `scripts/build_gaokao_report.py`，在报告中输出保守“研究排序”，并保持 `研究草稿` 状态门槛。
- 扩展 `scripts/profile_maintenance_queue.py`，输出 `field_gaps` 和 `next_action`，让 B/C 院校库复核可批处理。

### Phase 2: 高考核心数据闭环

- 扩展省级 pack 模板。
- 补齐更多省份的 2026 pack。
- 增加招生计划导入规范和样例。
- 增加计划更正 resolver 的数据约定。

### Phase 3: 风险引擎

- 增加历史位次 schema。
- 增加专业组连续性判断规则。
- 增加五维风险输出模板和停止量化条件。
- 增加候选池核验表模板。

### Phase 4: 行为评测和前向测试

- 为 10 个行为用例补全可执行 checks。
- 增加 2-3 个真实场景输出 fixture。
- 脚本检查越权话术、缺失状态门槛和风险混淆。

### Phase 5: 院校库结构化维护

- 从 Markdown 分段生成结构化索引。
- 统计 A/B/C 状态。
- 检查 B/C 措辞。
- 建立更名、转设、合并、校区迁移复核队列。

### Phase 6: 海外申请计划化

- 增加国家/地区申请模板。
- 增加 offer、签证、资金、认证、住宿、安全和国内备选状态表。
- 增加防中介误导和押金退费核验模板。

## 验收标准

基础规范：

- `SKILL.md` frontmatter 只有 `name` 和 `description`。
- skill 目录名、frontmatter name 均为 `university`。
- 不包含 `.DS_Store`、`README.md`、平台专属必需文件或父目录引用。
- 官方 Agent Skills 验证通过。
- 本地 quick validator 通过。

高考能力：

- 缺少 2026 招生计划时，最终状态只能是 `研究草稿`。
- 缺少位次时，不输出具体录取判断。
- 计划被更正时，旧条目不得进入最终排序。
- 新增专业组无历史数据时，不伪造冲稳保。
- 任何输出不得承诺保证录取。
- 五维风险必须分开展示。

院校库能力：

- B 级条目不得写成精确简介页已核验。
- C 级条目必须提示来源需复核。
- 院校库不得用于招生计划、代码、计划人数、费用或录取风险。

跨平台能力：

- 脚本失败时，Agent 仍可按 references 手动执行。
- 所有资源路径相对 skill 根目录。
- 不要求 Codex、OpenAI、MCP 或本机绝对路径。

## 维护规则

- 每次新增 province pack 后运行 `scripts/validate_data.py`。
- 每次修改行为用例后运行 `scripts/run_behavior_checks.py --validate`.
- 每次修改院校库后运行 `scripts/validate_profile_library.py`.
- 每次修改链接密集文件后运行 `scripts/check_links.py`，网络不可用时记录未执行，不把未检查写成已通过。
- 每次修改 `SKILL.md` 后运行官方 Agent Skills validator 和本地 quick validator。
- 高考志愿窗口内，省级来源的 `last_checked_at` 必须按实际核验日期更新；不能把旧检查日期当作当前事实。
