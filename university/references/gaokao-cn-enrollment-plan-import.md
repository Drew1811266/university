# gaokao-cn 招生计划导入规范

## 目的

把省级 2026 招生专业目录、计划更正、一分一段表、历史投档位次和用户上传的官方材料整理成可校验的数据。候选池只能从标准化招生计划条目生成；一分一段和历史位次只能用于资格、位次和风险分析。

## 来源等级

优先级从高到低：

1. 省级考试院 2026 招生专业目录原始 PDF、Excel、网页表格或官方系统字段。
2. 省级考试院 2026 计划更正、增补、取消、替换公告。
3. 省级考试院 2026 一分一段表、最低控制线和官方辅助系统。
4. 官方出版物或官方辅助系统导出。
5. 用户上传截图或转录材料：只能标 `user_supplied`，必须回官方来源核验。
6. 第三方志愿工具、论坛、媒体、学校官网专业页：只能作线索，不得进入候选池。

## 官方样本状态

本技能包含少量真实官方抽样数据，用于验证数据管道，不代表全量省份数据库：

- `references/gaokao-cn-score-segment-beijing-2026-official-sample.csv`：北京 2026 一分一段官方样本，可用 `scripts/normalize_score_segment_csv.py` 转 JSON。
- `references/gaokao-cn-enrollment-plan-beijing-2026-summary-official-sample.csv`：北京 2026 学校级招生计划汇总官方样本，只能用于确认官方计划来源和学校级计划数，不能生成专业组或专业候选池。
- `references/gaokao-cn-enrollment-plan-sichuan-2026-corrections-official-sample.csv`：四川 2026 招生计划更正官方样本，可用 `scripts/normalize_enrollment_plan_csv.py` 和 `scripts/resolve_plan_corrections.py` 测试更正逻辑。
- `references/gaokao-cn-historical-rank-guangdong-2025-official-sample.csv`：广东 2025 本科普通类投档位次官方样本，可用 `scripts/normalize_historical_rank_csv.py` 转 JSON。
- `references/gaokao-cn-official-data-sources.yaml`：记录上述样本和已确认但尚未抽取的官方来源。

标记为 `sampled` 的文件只能证明抽样行已核验，不能替代全量招生目录、全量一分一段或全量历史投档表。标记为 `source_verified_not_extracted` 的来源只能说明官方入口存在，不能直接生成候选池。

`references/gaokao-cn-official-data-sources.yaml` 必须为每个官方来源声明：

- `coverage_level`：例如 `sample_rows`、`school_level_summary`、`full_major_level`、`full_score_table`、`full_correction_notice`、`source_only`。
- `candidate_pool_eligible`：只有 `data_type=enrollment_plan`、`status=full_extracted`、`coverage_level=full_major_level` 的 2026 官方来源才能设为 `true`。

运行 `scripts/validate_official_data_sources.py references/gaokao-cn-official-data-sources.yaml` 检查覆盖等级，避免把样本或学校级汇总误用于候选池。

## 标准字段

导入后的每一行至少包含：

- `province`
- `year`
- `batch`
- `subject_category`
- `institution_code`
- `institution_name`
- `major_name`
- `plan_count`
- `source_file`

强烈建议同时补齐：

- `major_group_code`
- `major_code`
- `selected_subject_requirements`
- `tuition`
- `campus`
- `project_type`
- `remarks`
- `source_title`
- `source_type`
- `source_locator`
- `source_published_at`
- `source_url`
- `retrieved_at`
- `field_evidence_level`
- `coverage_level`
- `candidate_pool_eligible`
- `is_corrected`
- `correction_status`
- `replaces`
- `replaced_by`

标准化脚本会生成 `evidence_id`，用于把候选池、风险评估和报告中的具体条目追溯回字段级证据台账。

`coverage_level` 和 `candidate_pool_eligible` 是候选池硬门槛。学校级汇总、抽样行、入口级来源和未抽取 PDF 不得设为候选池可用。

## CSV 输入约定

`scripts/normalize_enrollment_plan_csv.py` 支持 UTF-8 CSV。表头使用 schema 字段名；`selected_subject_requirements` 用英文分号分隔，例如：

```csv
province,year,batch,subject_category,institution_code,institution_name,major_group_code,major_code,major_name,plan_count,selected_subject_requirements,tuition,campus,project_type,remarks,source_file,source_url,is_corrected,correction_status,replaces,replaced_by
广东,2026,本科批,物理类,10001,示例大学,201,01,计算机类,5,物理;化学,6000,主校区,普通类,示例备注,官方招生专业目录第10页,https://example.edu/plan.pdf,false,active,,
```

## 导入纪律

- 不要从大学官网专业列表补计划条目。
- 不要把截图 OCR 结果直接标为 `official_current`。
- 不要把缺失专业组代码的省份随意补 `000`；无专业组省份写空值或 `不适用`，并在候选池表说明。
- 学费、校区、项目性质和备注缺失时标 `待核验`，不要从往年或学校总览页补齐。
- 更正公告必须覆盖旧条目；`cancelled` 和 `replaced` 不得进入最终排序。

## 最小处理流程

1. 保存原始官方文件名、URL、发布日期和检索日期。
2. 转成 CSV 或结构化表格。
3. 对网页表格，可先运行 `scripts/extract_html_table.py` 抽取 CSV，再人工核对字段名和含义。
4. 对官方 PDF，可先运行 `scripts/extract_pdf_text.py 官方文件.pdf --output raw.txt` 抽取待审阅文本；PDF 文本不能直接当作标准表，必须人工重建表头、页码、专业组和备注对应关系。
5. 对官方 `.xlsx`，可先运行 `scripts/extract_xlsx_sheet.py 官方文件.xlsx --sheet 工作表名 --output raw.csv` 抽取 CSV；合并单元格、隐藏行、跨页表头和备注列必须人工复核。
6. 对已抽取的官方样本或结构化文件，可运行 `scripts/snapshot_sources.py raw.csv --output snapshot.json` 建立 SHA-256 快照；后续复核时用 `--manifest snapshot.json` 比较 `new/unchanged/changed/missing`。
7. 运行 `scripts/normalize_enrollment_plan_csv.py` 输出 JSON。
8. 需要证据台账时添加 `--evidence-output evidence.json`，输出每条计划记录对应的 `field_evidence_level`、来源类型、适用年份和检索日期。
9. 检查 `correction_status` 和替换关系。
10. 可运行 `scripts/resolve_plan_corrections.py` 生成有效计划视图，剔除 `cancelled` 和 `replaced`。
11. 可运行 `scripts/build_candidate_pool.py` 按候选人画像生成保留、剔除、待核验视图。
12. 一分一段表可运行 `scripts/normalize_score_segment_csv.py` 输出 `score-segment-item` JSON；历史投档位次可运行 `scripts/normalize_historical_rank_csv.py` 输出 `historical-rank-item` JSON。
13. 可运行 `scripts/build_gaokao_report.py` 汇总候选池、五维风险、研究排序和防越权门槛，但报告状态仍由证据完整性决定。
14. 需要把输出标为 `核验草案` 时，按 `references/gaokao-cn-submission-precheck-package.md` 为每个保留候选项构造防越权核验包，并运行 `scripts/validate_submission_precheck_package.py package.json`。
15. 进入报告写作时，仍需人工核验招生章程、体检、单科、外语、专业调剂和退档规则；没有通过候选项级防越权核验包时，脚本输出应保持 `研究草稿`。
