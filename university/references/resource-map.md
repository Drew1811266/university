# University Resource Map

Use this file to choose the smallest useful reference set. Do not load every profile segment by default.

## gaokao-cn

Required for any China mainland gaokao volunteer filling task:

- `references/gaokao-cn-workflow.md`
- `references/gaokao-cn-source-authority.md`
- `references/gaokao-cn-output-status.md`
- `references/gaokao-cn-report-schema.md`
- Matching province pack, for example `references/gaokao-cn-province-guangdong-2026.yaml`

Required when generating candidate pools,志愿排序, or冲稳保/risk analysis:

- `references/gaokao-cn-candidate-pool.md`
- `references/gaokao-cn-risk-method.md`

Load when needed:

- `references/candidate-profile.schema.json`: when structuring a candidate profile.
- `references/gaokao-cn-candidate-profile-sample.json`: sample candidate profile for script testing only.
- `references/province-cycle.schema.json`: when editing a province pack.
- `references/official-data-source.schema.json`: when editing `gaokao-cn-official-data-sources.yaml` coverage metadata.
- `references/enrollment-plan-item.schema.json`: when normalizing招生计划.
- `references/score-segment-item.schema.json`: when structuring one-score-one-rank or 一分一段 data.
- `references/historical-rank-item.schema.json`: when structuring historical投档位次 or专业位次 data.
- `references/gaokao-cn-historical-rank-sample.csv`: sample historical rank data for script testing only.
- `references/gaokao-cn-official-data-sources.yaml`: when checking which bundled official samples are extracted and which official sources are only verified.
- `references/gaokao-cn-score-segment-beijing-2026-official-sample.csv`: Beijing 2026 official one-score-one-rank sample rows for pipeline testing only.
- `references/gaokao-cn-enrollment-plan-beijing-2026-summary-official-sample.csv`: Beijing 2026 official school-level plan summary sample rows for source tracking only; do not use as major-level candidate-pool data.
- `references/gaokao-cn-enrollment-plan-sichuan-2026-corrections-official-sample.csv`: Sichuan 2026 official plan-correction sample rows for pipeline testing only.
- `references/gaokao-cn-historical-rank-guangdong-2025-official-sample.csv`: Guangdong 2025 official filing-rank sample rows for historical-comparison testing only.
- `references/risk-assessment.schema.json`: when producing five-dimension risk output.
- `references/evidence.schema.json` and `references/source-evidence-ledger.md`: when a field needs source-level support.
- `references/gaokao-cn-submission-gates.md`: when deciding whether output can be treated as `核验草案` without overclaiming.
- `references/gaokao-cn-submission-precheck-package.md` and `references/submission-precheck-package.schema.json`: when building the optional candidate-item-level evidence package for anti-overclaim checking.
- `references/gaokao-cn-submission-evidence-sample.json`: sample evidence ledger for gate-script testing only.
- `references/gaokao-cn-enrollment-plan-import.md`: when converting official招生专业目录 into standard data.
- `references/gaokao-cn-plan-corrections.md`: when applying更正、增补、取消、替换关系.
- `references/gaokao-cn-province-pack-template.yaml`: when creating a new province pack.
- `references/gaokao-cn-province-pack-seeds.csv`: when batch-creating draft province packs.
- `references/gaokao-cn-behavior-cases.yaml`: when checking whether an answer overclaims.
- `references/gaokao-cn-forward-scenarios.yaml`: when forward-testing the skill.

Do not use for gaokao candidate-pool generation:

- `references/university-profiles-*.md`
- `references/university-profile-search-index.md`
- Rankings, profile summaries, forums, agent brochures, media reports, or school major pages that are not the candidate province's 2026 official enrollment plan.

## university-profile

Required for stable university background tasks:

- `references/university-profile-search-index.md`
- `references/university-profile-library.md`
- Exactly one matching segment file, such as `references/university-profiles-china-001-050.md`

Use only for:

- School history.
- Campus overview.
- Institutional type and positioning.
- Stable strengths or long-running characteristics.

Do not use profile files for:

- Provincial招生计划.
- Whether a major enrolls in a province in 2026.
- Codes, plan counts, tuition, deadlines, scholarships, admission risk, adjustment risk, or withdrawal risk.

## gaokao-overseas

Required for China gaokao candidates applying overseas:

- `references/china-gaokao-overseas-study-guide.md`
- `references/overseas-official-source-map.md`
- `references/source-evidence-ledger.md`
- `references/consultation-intake-profile.md`

Load when needed:

- `references/country-source-guide.md`: for country-level source routing.
- `references/report-schema.md`: for broader comparison reports.
- `references/university-profiles-international.md`: only for stable background if a non-China profile has been added.

## Maintenance References

- `references/development-roadmap.md`: development defects, planned capabilities, phases, and acceptance criteria.
- `references/sample-prompts.md`: small behavior examples.
- `references/research-workflow.md`: general university research flow outside gaokao-specific tasks.

## Scripts

Scripts are optional helpers. If the host Agent platform cannot execute scripts, follow the equivalent references and schemas manually.

Portability rule: the skill does not require Codex/OpenAI-specific tools. Python scripts are optional accelerators; the core workflow is `SKILL.md` plus `references/` instructions and schemas. If Python, PyYAML, or network access is unavailable, do the same checks manually and keep the output at `研究草稿` until the five gates are proven.

- `scripts/validate_data.py`: validates schemas, province packs, behavior cases, and core maintenance files. Requires Python 3 and PyYAML.
- `scripts/validate_official_data_sources.py`: validates `coverage_level`, `candidate_pool_eligible`, extraction files, and source status for official data sources. Requires Python 3 and PyYAML.
- `scripts/check_links.py`: checks URLs embedded in Markdown, YAML, and JSON files. Requires Python 3 and network access.
- `scripts/extract_html_table.py`: extracts official HTML tables from a local file or URL into CSV for review before normalization. Requires Python 3; network is needed only for URL input.
- `scripts/extract_pdf_text.py`: extracts review text from official PDFs. It uses `pdftotext` when installed and otherwise falls back to simple uncompressed/Flate PDF text streams. Requires Python 3; output must be manually checked before reconstructing CSV tables.
- `scripts/extract_xlsx_sheet.py`: extracts an official XLSX worksheet into CSV without third-party dependencies. Requires Python 3; manually verify merged cells, hidden rows, and header meanings before normalization.
- `scripts/detect_source_changes.py`: summarizes province pack freshness and monitoring status. Requires Python 3 and PyYAML.
- `scripts/snapshot_sources.py`: creates SHA-256 snapshots for local official extraction files, then compares against a previous manifest to flag `new`, `unchanged`, `changed`, or `missing` files. Requires Python 3; PyYAML is required only when reading `gaokao-cn-official-data-sources.yaml`. A changed digest means the local extracted source needs review; it does not by itself prove the official policy changed.
- `scripts/province_readiness.py`: computes per-province `province_pack_status`, final `output_status`, daily freshness, source-gate readiness, and full-data coverage readiness separately. Requires Python 3 and PyYAML.
- `scripts/build_markdown.py`: generates Markdown status tables from province packs using the same readiness logic, including province-pack status and final report status. Requires Python 3 and PyYAML.
- `scripts/build_gaokao_report.py`: assembles candidate-pool, risk, research ranking, and gate JSON into a conservative Markdown report. Requires Python 3.
- `scripts/create_province_pack.py`: creates a draft province pack from `references/gaokao-cn-province-pack-template.yaml`. Requires Python 3.
- `scripts/create_all_province_packs.py`: batch-creates draft province packs from `references/gaokao-cn-province-pack-seeds.csv`. Requires Python 3.
- `scripts/normalize_enrollment_plan_csv.py`: converts official enrollment-plan CSV rows into JSON records matching `enrollment-plan-item.schema.json`, and can emit evidence ledger rows with `--evidence-output`. Requires Python 3.
- `scripts/resolve_plan_corrections.py`: removes cancelled/replaced plan items and reports unresolved correction states. Requires Python 3.
- `scripts/build_candidate_pool.py`: filters normalized plan JSON by candidate profile into retain/reject/recheck rows. It does not produce冲稳保 or a submit-ready志愿表. Requires Python 3.
- `scripts/normalize_score_segment_csv.py`: converts official one-score-one-rank CSV rows into JSON records matching `score-segment-item.schema.json`. Requires Python 3.
- `scripts/normalize_historical_rank_csv.py`: converts official historical rank CSV rows into JSON records matching `historical-rank-item.schema.json`. Requires Python 3.
- `scripts/build_risk_assessment.py`: builds conservative five-dimension risk output. It only assigns冲/稳/保 when comparable official historical ranks exist and quantification checks pass. Requires Python 3.
- `scripts/check_submission_gates.py`: checks the five anti-overclaim gates before presenting a higher-confidence `核验草案`. Requires Python 3 and PyYAML.
- `scripts/validate_submission_precheck_package.py`: validates the stricter candidate-item-level anti-overclaim package: full major-level plan item, candidate rank evidence, subject qualification, plan-correction evidence, and 2026 university charter restrictions. Requires Python 3.
- `scripts/run_self_test.py`: runs the offline sample pipeline and asserts core safety gates. Requires Python 3 and PyYAML.
- `scripts/run_behavior_checks.py`: validates behavior cases and can run simple text assertions against sample outputs. Requires Python 3 and PyYAML.
- `scripts/validate_profile_library.py`: checks profile-library wording and source-status hygiene. Requires Python 3.
- `scripts/profile_maintenance_queue.py`: builds a B/C and unstable-entry recheck queue for profile-library maintenance. Requires Python 3.
- `scripts/build_overseas_plan.py`: generates a structured overseas application verification plan by country/pathway/intake. Requires Python 3.

## Loading Discipline

- For gaokao tasks, load policy, source authority, output status, report schema, and the matching province pack before recommending anything.
- For profile tasks, search the index first and then open only the target segment.
- For overseas tasks, keep admission, visa, funds, credential recognition, housing, safety, and domestic backup evidence separate.
- If sources are missing, outdated, conflicting, login-only, screenshot-only, or third-party-only, mark the result as `待核验` or `研究草稿`.
