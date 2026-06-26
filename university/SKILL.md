---
name: university
description: "Self-contained university research skill for official-source university profiles, China mainland 2026 gaokao volunteer filling, and gaokao-to-overseas undergraduate application verification."
metadata:
  version: "0.2.0"
---

# university

## Role

Use this single skill for university-related research and advising. It contains three internal modes:

1. `gaokao-cn`: China mainland普通高考志愿填报, especially 2026 provincial policy,招生计划, 一分一段表, 院校专业组, 专业代码, 调剂, 退档, 征集志愿, 志愿表排序, and five-dimension risk analysis.
2. `university-profile`: stable university background, school introductions, institutional history, campus overview, positioning, and non-time-sensitive strengths.
3. `gaokao-overseas`: China gaokao candidates applying to overseas undergraduate programs, including admission, visa, funds, credential recognition, housing, safety, and domestic backup timing.

All resources needed by these modes live inside this `university/` skill directory. The structure is platform-neutral: `SKILL.md` contains routing and core instructions, `references/` contains domain knowledge and structured resources, and `scripts/` contains optional local validation helpers. Do not require sibling skills, vendor-specific metadata, platform-specific tools, or `../` paths.

Default output language is Chinese unless the user asks otherwise.

Use `references/resource-map.md` to choose the smallest relevant reference set before opening large bundled resources.

## Mode Selection

Choose the strictest relevant mode before doing detailed work:

- Use `gaokao-cn` when the request concerns China mainland gaokao volunteer filling, provincial undergraduate admissions, 院校专业组, 专业（类）+院校, 招生计划, 位次, 投档线, 调剂, 退档, 征集志愿, 冲稳保, or 2026 志愿方案.
- Use `university-profile` when the request is a school introduction, background summary, institutional profile, history, campus overview, or stable strengths.
- Use `gaokao-overseas` when a China gaokao candidate asks about overseas undergraduate admission, using gaokao scores abroad, foundation/bridge routes, visas, funds, recognition, housing, safety, deposits, agents, or domestic backups.
- If a task spans modes, run the higher-risk mode first. A gaokao志愿方案 that also needs school introductions starts with `gaokao-cn`; profile content is added only after the official candidate pool is built.

## gaokao-cn Rules

For China mainland gaokao volunteer filling:

- Read `references/gaokao-cn-workflow.md`, `references/gaokao-cn-source-authority.md`, `references/gaokao-cn-output-status.md`, and `references/gaokao-cn-report-schema.md`.
- For candidate pools,志愿排序, or冲稳保 analysis, also read `references/gaokao-cn-candidate-pool.md` and `references/gaokao-cn-risk-method.md`.
- Load the matching province pack before producing any recommendation, such as `references/gaokao-cn-province-guangdong-2026.yaml` or `references/gaokao-cn-province-sichuan-2026.yaml`.
- Core capabilities are 官方来源追踪、招生计划导入辅助、候选池过滤、防错清单、五维风险拆解、待核验项列表.
- Ask the user only for facts that official documents cannot provide: province, year, subject category or selected subjects, score, rank, batch, qualifications, physical-exam or single-subject limits, foreign language, budget, region and major preferences, adjustment bottom line, and unacceptable outcomes.
- Do not ask the candidate to supply volunteer mode,志愿数量, confirmation method, filling deadline, system entrance, or whether professional adjustment exists; verify those from provincial official documents.
- Generate candidate pools only from the candidate province's verified 2026 official enrollment plan and corrections.
- Static rankings and the profile library cannot create or expand a gaokao candidate pool.
- Show five separate risk dimensions: qualification risk, filing risk, major/adjustment risk, withdrawal risk, and outcome-acceptability risk.
- Default output status is `研究草稿` or `核验草案`. This skill does not target generating a directly submittable volunteer form.
- Keep submission-precheck package validation as an anti-overclaim guardrail. Passing it only means the draft has enough evidence for higher-confidence review; it is not a required product goal and does not replace the provincial official filling system.

Never state or imply `稳录`, `保录取`, `保专业`, or `一定录取`.

## university-profile Rules

For stable university background:

- Read `references/university-profile-search-index.md` first, then `references/university-profile-library.md`, then only the one segment file containing the target school.
- Treat `profile_source_status` as overall resource status, not field-level evidence.
- Use profile entries only for non-time-sensitive background: history, location, positioning, campus overview, and stable strengths.
- For B-level entries, write that the resource is based on official entry pages and public materials and that the precise profile page is pending. Do not write that the fact is fully verified by a precise source.
- For C-level entries, explicitly warn that the source needs recheck.
- Any admissions, provincial plan availability, major code, professional group code, tuition, plan count, admission risk, adjustment risk, or withdrawal risk must use current official sources, not the profile library.

## gaokao-overseas Rules

For gaokao-to-overseas undergraduate application:

- Read `references/china-gaokao-overseas-study-guide.md`, `references/overseas-official-source-map.md`, `references/source-evidence-ledger.md`, and `references/consultation-intake-profile.md`.
- Verify admission, student visa, funds, entry compliance, credential recognition, professional licensing, housing, safety, deposits, and domestic backup timing from separate official sources.
- Do not imply that an overseas offer guarantees a visa, entry permission, credential recognition, housing, employment rights, or future professional licensure.
- Treat agent brochures, forums, rankings, social posts, and third-party tools as leads only.

## Evidence Rules

- Use `references/source-evidence-ledger.md` for high-impact or time-sensitive fields.
- Use field-specific authority. For gaokao plan fields, provincial 2026 enrollment plan and official corrections are highest authority; university webpages cannot replace them.
- For 2026 gaokao final filling conclusions, 2025 or older sources are historical comparison only.
- Mark missing, conflicting, login-only, outdated, or unclear facts as `待核验`.
- Do not invent requirements, deadlines, tuition, scholarships, program names, policy details, source titles, URLs, dates, or admission outcomes.

## Bundled Resources

- `references/resource-map.md`: route tasks to the smallest required reference set.
- `references/development-roadmap.md`: maintenance roadmap, defects, planned capabilities, phases, and acceptance criteria.
- `references/gaokao-cn-province-*-2026.yaml`: province packs for 2026 gaokao status tracking.
- `references/gaokao-cn-official-data-sources.yaml`: official-source extraction ledger for bundled 2026/2025 gaokao samples and source-only entries.
- `references/*.schema.json`: structured schemas for candidate profiles, province cycles, official data sources, enrollment plan items, score segments, historical ranks, risk assessments, evidence, and submission precheck packages.
- `references/gaokao-cn-candidate-pool.md` and `references/gaokao-cn-risk-method.md`: candidate-pool and five-dimension risk rules.
- `references/gaokao-cn-submission-gates.md`: anti-overclaim gates for deciding whether a draft may be treated as `核验草案`.
- `references/gaokao-cn-submission-precheck-package.md`: candidate-item-level evidence package for optional anti-overclaim checking.
- `references/gaokao-cn-enrollment-plan-import.md` and `references/gaokao-cn-plan-corrections.md`: enrollment-plan, one-score-one-rank, historical-rank import, and correction handling rules.
- `references/gaokao-cn-score-segment-beijing-2026-official-sample.csv`: official Beijing 2026 one-score-one-rank sample rows for pipeline testing, not a full province database.
- `references/gaokao-cn-enrollment-plan-beijing-2026-summary-official-sample.csv`: official Beijing 2026 school-level enrollment-plan summary sample rows, not professional-group or major-level candidate-pool data.
- `references/gaokao-cn-enrollment-plan-sichuan-2026-corrections-official-sample.csv`: official Sichuan 2026 plan-correction sample rows for correction-resolution testing, not the full correction notice.
- `references/gaokao-cn-historical-rank-guangdong-2025-official-sample.csv`: official Guangdong 2025 filing-rank sample rows for historical comparison testing, not 2026 final evidence.
- `references/gaokao-cn-behavior-cases.yaml` and `references/gaokao-cn-forward-scenarios.yaml`: behavior cases that prevent overclaiming.
- `scripts/validate_data.py`: validate structured data and behavior fixtures.
- `scripts/validate_official_data_sources.py`: validate official-source coverage level and candidate-pool eligibility metadata.
- `scripts/extract_html_table.py`: extract official webpage tables into CSV for review before normalization.
- `scripts/extract_pdf_text.py`: extract review text from official PDFs before manual table reconstruction and normalization.
- `scripts/extract_xlsx_sheet.py`: extract official XLSX worksheets into CSV without third-party dependencies before normalization.
- `scripts/create_province_pack.py`: create draft province packs from the bundled template.
- `scripts/create_all_province_packs.py`: batch-create draft province packs from the province seed table.
- `scripts/normalize_enrollment_plan_csv.py`: normalize official enrollment-plan CSV data into JSON records.
- `scripts/resolve_plan_corrections.py`: filter corrected enrollment-plan records into an active-plan view.
- `scripts/build_candidate_pool.py`: filter normalized enrollment-plan records by candidate profile before report writing.
- `scripts/normalize_score_segment_csv.py`: normalize official one-score-one-rank CSV rows into JSON records.
- `scripts/normalize_historical_rank_csv.py`: normalize official historical rank CSV data into JSON records.
- `scripts/build_risk_assessment.py`: build conservative five-dimension risk assessments from candidate-pool and historical-rank JSON.
- `scripts/check_submission_gates.py`: check whether all five anti-overclaim gates are satisfied before presenting a higher-confidence `核验草案`.
- `scripts/validate_submission_precheck_package.py`: validate a candidate-item-level package containing full major-level plan items, candidate rank evidence, subject qualification evidence, plan-correction evidence, and university charter restrictions as an optional anti-overclaim guardrail.
- `scripts/province_readiness.py`: summarize 2026 province-pack source status, daily freshness, full-data coverage, and final report gating separately.
- `scripts/build_gaokao_report.py`: assemble a conservative Markdown report with candidate pool, five-dimension risk, research ranking, and gate JSON outputs.
- `scripts/run_self_test.py`: run offline sample-pipeline self-tests.
- `scripts/run_behavior_checks.py`: validate behavior cases and simple output assertions.
- `scripts/validate_profile_library.py`: check profile-library wording and source-status hygiene.
- `scripts/profile_maintenance_queue.py`: build a profile-library recheck queue for B/C and unstable entries.
- `scripts/build_overseas_plan.py`: generate a gaokao-to-overseas application verification plan.
- `scripts/check_links.py`: check URLs embedded in structured data and references.
- `scripts/detect_source_changes.py`: summarize province-pack freshness and monitoring status.
- `scripts/snapshot_sources.py`: create SHA-256 snapshots for local official extraction files and compare them against a previous manifest.
- `scripts/build_markdown.py`: generate Markdown status tables from structured data.

Scripts are optional helpers. If the host Agent platform cannot execute scripts, follow the same schemas and reference files manually.
