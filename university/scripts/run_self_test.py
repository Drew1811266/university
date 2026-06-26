#!/usr/bin/env python3
"""Run offline self-tests for the gaokao-cn data pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


def run(cmd: list[str], cwd: Path) -> None:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        message = [
            f"command failed: {' '.join(cmd)}",
            f"exit code: {completed.returncode}",
            "stdout:",
            completed.stdout,
            "stderr:",
            completed.stderr,
        ]
        raise RuntimeError("\n".join(message))


def run_expect_failure(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode == 0:
        message = [
            f"command unexpectedly succeeded: {' '.join(cmd)}",
            "stdout:",
            completed.stdout,
            "stderr:",
            completed.stderr,
        ]
        raise RuntimeError("\n".join(message))
    return completed


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_true(condition: bool, label: str) -> None:
    if not condition:
        raise AssertionError(label)


def write_minimal_xlsx(path: Path) -> None:
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
</Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="计划" sheetId="1" r:id="rId1"/></sheets>
</workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
</Relationships>""",
        "xl/worksheets/sheet1.xml": """<?xml version="1.0" encoding="UTF-8"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetData>
    <row r="1">
      <c r="A1" t="inlineStr"><is><t>学校代码</t></is></c>
      <c r="B1" t="inlineStr"><is><t>学校名称</t></is></c>
      <c r="C1" t="inlineStr"><is><t>计划招生数</t></is></c>
    </row>
    <row r="2">
      <c r="A2" t="inlineStr"><is><t>1021</t></is></c>
      <c r="B2" t="inlineStr"><is><t>北京大学</t></is></c>
      <c r="C2"><v>200</v></c>
    </row>
  </sheetData>
</worksheet>""",
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def write_minimal_pdf(path: Path) -> None:
    stream = b"BT /F1 12 Tf 72 720 Td (Peking University Plan Count 200) Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 612 792] /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(content))
        content.extend(f"{index} 0 obj\n".encode("ascii"))
        content.extend(obj)
        content.extend(b"\nendobj\n")
    xref_offset = len(content)
    content.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(bytes(content))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root).resolve()
    python = sys.executable

    try:
        run([python, "scripts/validate_data.py", "."], root)
        run([python, "scripts/run_behavior_checks.py", "--validate"], root)
        run([python, "scripts/validate_profile_library.py", "--strict"], root)
        run([python, "scripts/validate_official_data_sources.py", "references/gaokao-cn-official-data-sources.yaml"], root)

        with tempfile.TemporaryDirectory(prefix="university-skill-self-test-") as tmp:
            tmpdir = Path(tmp)
            plan_json = tmpdir / "plan.json"
            plan_evidence_json = tmpdir / "plan-evidence.json"
            active_plan_json = tmpdir / "active-plan.json"
            official_score_segments_json = tmpdir / "official-score-segments.json"
            official_corrections_json = tmpdir / "official-corrections.json"
            official_active_corrections_json = tmpdir / "official-active-corrections.json"
            official_historical_json = tmpdir / "official-historical.json"
            html_fixture = tmpdir / "official-table.html"
            html_table_csv = tmpdir / "official-table.csv"
            xlsx_fixture = tmpdir / "official-plan.xlsx"
            xlsx_table_csv = tmpdir / "official-plan.csv"
            pdf_fixture = tmpdir / "official-plan.pdf"
            pdf_text = tmpdir / "official-plan.txt"
            snapshot_fixture = tmpdir / "source-file.txt"
            snapshot_v1_json = tmpdir / "source-snapshot-v1.json"
            snapshot_same_json = tmpdir / "source-snapshot-same.json"
            snapshot_changed_json = tmpdir / "source-snapshot-changed.json"
            candidate_pool_json = tmpdir / "candidate-pool.json"
            historical_json = tmpdir / "historical.json"
            risk_json = tmpdir / "risk.json"
            gates_json = tmpdir / "gates.json"
            precheck_ok_json = tmpdir / "submission-precheck-ok.json"
            precheck_bad_json = tmpdir / "submission-precheck-bad.json"
            precheck_report_json = tmpdir / "submission-precheck-report.json"
            readiness_json = tmpdir / "province-readiness.json"
            province_status_md = tmpdir / "province-status.md"
            report_md = tmpdir / "gaokao-report.md"
            profile_queue_json = tmpdir / "profile-queue.json"
            overseas_plan_md = tmpdir / "overseas-plan.md"

            run(
                [
                    python,
                    "scripts/province_readiness.py",
                    ".",
                    "--output",
                    str(readiness_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/build_markdown.py",
                    ".",
                    "--write",
                    str(province_status_md),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/profile_maintenance_queue.py",
                    ".",
                    "--output",
                    str(profile_queue_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/build_overseas_plan.py",
                    "--country",
                    "英国",
                    "--pathway",
                    "高考成绩直申",
                    "--intake",
                    "2026 entry",
                    "--output",
                    str(overseas_plan_md),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/normalize_enrollment_plan_csv.py",
                    "references/gaokao-cn-enrollment-plan-sample.csv",
                    "--output",
                    str(plan_json),
                    "--evidence-output",
                    str(plan_evidence_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/normalize_score_segment_csv.py",
                    "references/gaokao-cn-score-segment-beijing-2026-official-sample.csv",
                    "--output",
                    str(official_score_segments_json),
                ],
                root,
            )
            html_fixture.write_text(
                """
                <table class="case">
                  <tr><td>序号</td><td>学校代码</td><td>学校名称</td><td>所在地区</td><td>录取批次</td><td>计划招生数</td></tr>
                  <tr><td>15</td><td>1021</td><td><a href="#">北京大学</a></td><td>北京</td><td>本科普通批</td><td>200</td></tr>
                  <tr><td>17</td><td>1023</td><td><a href="#">清华大学</a></td><td>北京</td><td>本科普通批</td><td>206</td></tr>
                </table>
                """,
                encoding="utf-8",
            )
            run(
                [
                    python,
                    "scripts/extract_html_table.py",
                    str(html_fixture),
                    "--table-index",
                    "0",
                    "--output",
                    str(html_table_csv),
                ],
                root,
            )
            write_minimal_xlsx(xlsx_fixture)
            run(
                [
                    python,
                    "scripts/extract_xlsx_sheet.py",
                    str(xlsx_fixture),
                    "--sheet",
                    "计划",
                    "--output",
                    str(xlsx_table_csv),
                ],
                root,
            )
            write_minimal_pdf(pdf_fixture)
            run(
                [
                    python,
                    "scripts/extract_pdf_text.py",
                    str(pdf_fixture),
                    "--output",
                    str(pdf_text),
                ],
                root,
            )
            snapshot_fixture.write_text("version 1\n", encoding="utf-8")
            run(
                [
                    python,
                    "scripts/snapshot_sources.py",
                    str(snapshot_fixture),
                    "--output",
                    str(snapshot_v1_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/snapshot_sources.py",
                    str(snapshot_fixture),
                    "--manifest",
                    str(snapshot_v1_json),
                    "--output",
                    str(snapshot_same_json),
                ],
                root,
            )
            snapshot_fixture.write_text("version 2\n", encoding="utf-8")
            run(
                [
                    python,
                    "scripts/snapshot_sources.py",
                    str(snapshot_fixture),
                    "--manifest",
                    str(snapshot_v1_json),
                    "--output",
                    str(snapshot_changed_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/normalize_enrollment_plan_csv.py",
                    "references/gaokao-cn-enrollment-plan-sichuan-2026-corrections-official-sample.csv",
                    "--output",
                    str(official_corrections_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/resolve_plan_corrections.py",
                    str(official_corrections_json),
                    "--output",
                    str(official_active_corrections_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/resolve_plan_corrections.py",
                    str(plan_json),
                    "--output",
                    str(active_plan_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/build_candidate_pool.py",
                    "--profile",
                    "references/gaokao-cn-candidate-profile-sample.json",
                    "--plan",
                    str(active_plan_json),
                    "--output",
                    str(candidate_pool_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/normalize_historical_rank_csv.py",
                    "references/gaokao-cn-historical-rank-sample.csv",
                    "--output",
                    str(historical_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/normalize_historical_rank_csv.py",
                    "references/gaokao-cn-historical-rank-guangdong-2025-official-sample.csv",
                    "--output",
                    str(official_historical_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/build_risk_assessment.py",
                    "--profile",
                    "references/gaokao-cn-candidate-profile-sample.json",
                    "--candidate-pool",
                    str(candidate_pool_json),
                    "--historical-ranks",
                    str(historical_json),
                    "--output",
                    str(risk_json),
                ],
                root,
            )
            run(
                [
                    python,
                    "scripts/check_submission_gates.py",
                    "--province-pack",
                    "references/gaokao-cn-province-guangdong-2026.yaml",
                    "--profile",
                    "references/gaokao-cn-candidate-profile-sample.json",
                    "--candidate-pool",
                    str(candidate_pool_json),
                    "--risk-assessment",
                    str(risk_json),
                    "--evidence",
                    "references/gaokao-cn-submission-evidence-sample.json",
                    "--output",
                    str(gates_json),
                ],
                root,
            )
            precheck_ok_json.write_text(
                json.dumps(
                    {
                        "province": "广东",
                        "year": 2026,
                        "candidate_profile": {
                            "province": "广东",
                            "year": 2026,
                            "subject_profile": {"type": "selected_subjects", "selected_subjects": ["物理", "化学"]},
                            "score": 600,
                            "rank": 30000,
                            "target_batch": "本科批",
                        },
                        "candidate_rank_evidence": {
                            "rank": 30000,
                            "rank_basis": "official_score_query",
                            "source_title": "广东省2026年普通高考成绩查询用户脱敏确认",
                            "source_url": "https://eea.gd.gov.cn/",
                            "applicable_year": 2026,
                            "field_evidence_level": "user_supplied",
                            "sensitive_info_redacted": True,
                            "retrieved_at": "2026-06-26",
                        },
                        "provincial_policy_evidence": {
                            "source_title": "广东省2026年普通高考志愿填报通知",
                            "source_url": "https://eea.gd.gov.cn/",
                            "applicable_year": 2026,
                            "field_evidence_level": "official_current",
                            "retrieved_at": "2026-06-26",
                        },
                        "plan_corrections_evidence": {
                            "status": "checked",
                            "source_title": "广东省2026年普通高校招生专业目录更正检查",
                            "source_url": "https://eea.gd.gov.cn/",
                            "applicable_year": 2026,
                            "field_evidence_level": "official_current",
                            "retrieved_at": "2026-06-26",
                        },
                        "candidate_items": [
                            {
                                "candidate_item_id": "广东|本科批|物理类|10001|201|01",
                                "plan_item": {
                                    "province": "广东",
                                    "year": 2026,
                                    "batch": "本科批",
                                    "subject_category": "物理类",
                                    "institution_code": "10001",
                                    "institution_name": "示例大学",
                                    "major_group_code": "201",
                                    "major_code": "01",
                                    "major_name": "计算机类",
                                    "plan_count": 5,
                                    "selected_subject_requirements": ["物理", "化学"],
                                    "source_file": "广东省2026年普通高校招生专业目录",
                                    "source_title": "广东省2026年普通高校招生专业目录",
                                    "source_type": "provincial_enrollment_plan",
                                    "source_url": "https://eea.gd.gov.cn/",
                                    "retrieved_at": "2026-06-26",
                                    "field_evidence_level": "official_current",
                                    "coverage_level": "full_major_level",
                                    "candidate_pool_eligible": True,
                                    "correction_status": "active",
                                },
                                "subject_qualification": {
                                    "status": "pass",
                                    "source_title": "广东省2026年普通高校招生专业目录选科要求",
                                    "source_url": "https://eea.gd.gov.cn/",
                                    "applicable_year": 2026,
                                    "field_evidence_level": "official_current",
                                    "matched_requirements": ["物理", "化学"],
                                    "retrieved_at": "2026-06-26",
                                },
                                "charter_restrictions": {
                                    "status": "pass",
                                    "institution_code": "10001",
                                    "source_title": "示例大学2026年本科招生章程",
                                    "source_url": "https://example.edu/charter-2026",
                                    "applicable_year": 2026,
                                    "field_evidence_level": "official_current",
                                    "retrieved_at": "2026-06-26",
                                    "rules": {
                                        "physical_exam": "按普通高等学校招生体检工作指导意见执行",
                                        "single_subject": "未见该专业单科硬性限制",
                                        "foreign_language": "不限外语语种",
                                        "filing_ratio": "平行志愿按省级投档规则执行",
                                        "major_admission": "分数优先",
                                        "adjustment_rule": "按院校专业组内规则调剂",
                                    },
                                },
                            }
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            precheck_bad = load_json(precheck_ok_json)
            del precheck_bad["candidate_items"][0]["charter_restrictions"]
            precheck_bad_json.write_text(json.dumps(precheck_bad, ensure_ascii=False) + "\n", encoding="utf-8")
            run(
                [
                    python,
                    "scripts/validate_submission_precheck_package.py",
                    str(precheck_ok_json),
                    "--output",
                    str(precheck_report_json),
                ],
                root,
            )
            failed_precheck = run_expect_failure(
                [
                    python,
                    "scripts/validate_submission_precheck_package.py",
                    str(precheck_bad_json),
                ],
                root,
            )
            assert_true("charter_restrictions" in failed_precheck.stderr, "precheck validator must fail without charter restrictions")
            run(
                [
                    python,
                    "scripts/build_gaokao_report.py",
                    "--profile",
                    "references/gaokao-cn-candidate-profile-sample.json",
                    "--candidate-pool",
                    str(candidate_pool_json),
                    "--risk-assessment",
                    str(risk_json),
                    "--gates",
                    str(gates_json),
                    "--output",
                    str(report_md),
                ],
                root,
            )

            candidate_pool = load_json(candidate_pool_json)
            readiness = load_json(readiness_json)
            plan_evidence = load_json(plan_evidence_json)
            profile_queue = load_json(profile_queue_json)
            official_plan_summary = load_csv(root / "references" / "gaokao-cn-enrollment-plan-beijing-2026-summary-official-sample.csv")
            html_rows = load_csv(html_table_csv)
            xlsx_rows = load_csv(xlsx_table_csv)
            pdf_text_content = pdf_text.read_text(encoding="utf-8")
            snapshot_v1 = load_json(snapshot_v1_json)
            snapshot_same = load_json(snapshot_same_json)
            snapshot_changed = load_json(snapshot_changed_json)
            official_score_segments = load_json(official_score_segments_json)
            official_active_corrections = load_json(official_active_corrections_json)
            official_historical = load_json(official_historical_json)
            assert_equal(readiness["summary"]["province_count"], 31, "province readiness province count")
            assert_equal(readiness["summary"]["submit_ready_count"], 0, "readiness must not mark any province submit-ready without full major-level plan data")
            assert_equal(readiness["summary"]["precheck_candidate_count"], 0, "readiness must expose precheck candidate count without submit-ready wording")
            assert_true(readiness["summary"]["source_ready_count"] >= 1, "readiness must expose source-ready provinces separately")
            assert_true("province_pack_status_counts" in readiness["summary"], "readiness must summarize province pack statuses separately from final output status")
            assert_true("final_output_status_counts" in readiness["summary"], "readiness must summarize final output statuses without using ambiguous draft_count")
            assert_true(
                len(readiness["summary"]["province_pack_status_counts"]) >= 2,
                "province pack statuses must not collapse every province into one draft label",
            )
            assert_true(
                "省级来源待补齐" not in readiness["summary"]["province_pack_status_counts"],
                "verified province packs must not remain in the default source-pending bucket",
            )
            assert_true(any(row["output_status"] == "研究草稿" for row in readiness["provinces"]), "readiness must expose draft provinces")
            beijing_readiness = next(row for row in readiness["provinces"] if row["province"] == "北京")
            assert_equal(
                beijing_readiness["province_pack_status"],
                "省级来源已核验，缺全量专业级计划",
                "Beijing province pack status",
            )
            assert_equal(beijing_readiness["readiness"]["provincial_policy_2026"], True, "Beijing provincial policy readiness")
            assert_equal(beijing_readiness["readiness"]["plan_corrections_2026"], True, "Beijing correction-monitor readiness")
            assert_equal(beijing_readiness["data_coverage"]["enrollment_plan_full_major_level_2026"], False, "Beijing must not claim full major-level plan coverage")
            assert_equal(beijing_readiness["submit_ready_possible_from_pack"], False, "Beijing must remain draft without full major-level plan data")
            assert_equal(beijing_readiness["precheck_candidate_from_pack"], False, "Beijing must expose non-submit wording for precheck candidacy")
            assert_true(not any(gap.startswith("volunteer_filling:") for gap in beijing_readiness["hard_gaps"]), "Beijing volunteer filling must not remain a hard gap")
            assert_true(not any(gap.startswith("plan_corrections:") for gap in beijing_readiness["hard_gaps"]), "Beijing correction monitoring must not remain a hard gap")
            assert_true(profile_queue["summary"]["B"] > 0, "profile maintenance queue must expose B-level entries")
            assert_true(profile_queue["priority_queue"], "profile maintenance queue must not be empty")
            assert_true("field_gaps" in profile_queue["priority_queue"][0], "profile maintenance queue must expose field gaps")
            assert_true("next_action" in profile_queue["priority_queue"][0], "profile maintenance queue must expose next action")
            assert_true(len(plan_evidence) >= 2, "plan normalization must emit evidence ledger rows")
            assert_true(all(item["field_evidence_level"] == "official_current" for item in plan_evidence), "sample plan evidence must be official_current")
            assert_true(len(official_plan_summary) >= 10, "official Beijing plan summary sample must contain rows")
            peking_plan = next(item for item in official_plan_summary if item["institution_name"] == "北京大学")
            tsinghua_plan = next(item for item in official_plan_summary if item["institution_name"] == "清华大学")
            assert_equal(peking_plan["plan_count"], "200", "official Beijing plan summary Peking plan count")
            assert_equal(tsinghua_plan["plan_count"], "206", "official Beijing plan summary Tsinghua plan count")
            assert_true("不得用于生成具体候选池" in peking_plan["notes"], "official Beijing plan summary must warn against candidate-pool use")
            assert_equal(html_rows[0]["学校名称"], "北京大学", "HTML table extractor school name")
            assert_equal(html_rows[0]["计划招生数"], "200", "HTML table extractor plan count")
            assert_equal(xlsx_rows[0]["学校名称"], "北京大学", "XLSX extractor school name")
            assert_equal(xlsx_rows[0]["计划招生数"], "200", "XLSX extractor plan count")
            assert_true("Peking University Plan Count 200" in pdf_text_content, "PDF extractor text")
            assert_equal(snapshot_v1["summary"]["new"], 1, "source snapshot first run new count")
            assert_equal(snapshot_same["summary"]["unchanged"], 1, "source snapshot unchanged count")
            assert_equal(snapshot_changed["summary"]["changed"], 1, "source snapshot changed count")
            assert_equal(official_score_segments[0]["province"], "北京", "official score segment province")
            assert_equal(official_score_segments[0]["year"], 2026, "official score segment year")
            assert_equal(official_score_segments[0]["cumulative_count"], 111, "official score segment first cumulative count")
            assert_equal(official_score_segments[-1]["score_min"], 120, "official score segment interval lower bound")
            assert_equal(official_score_segments[-1]["score_max"], 129, "official score segment interval upper bound")
            assert_true(all(item["field_evidence_level"] == "official_current" for item in official_score_segments), "official score segments must be current evidence")
            assert_equal(len(official_active_corrections), 3, "official Sichuan active correction count")
            assert_true(all(item["correction_status"] == "corrected" for item in official_active_corrections), "official active corrections must exclude cancelled rows")
            assert_equal(official_historical[0]["province"], "广东", "official historical province")
            assert_equal(official_historical[0]["year"], 2025, "official historical year")
            assert_equal(official_historical[0]["minimum_rank"], 28, "official historical first rank")
            assert_true(all(item["field_evidence_level"] == "official_historical" for item in official_historical), "official historical rank evidence level")

            assert_equal(candidate_pool["output_status"], "研究草稿", "candidate pool output status")
            assert_equal(candidate_pool["counts"]["保留"], 1, "candidate pool retained count")
            assert_equal(candidate_pool["counts"]["剔除"], 1, "candidate pool rejected count")
            retained = next(item for item in candidate_pool["items"] if item["keep_status"] == "保留")
            assert_equal(retained["evidence"]["coverage_level"], "full_major_level", "retained plan coverage level")
            assert_equal(retained["evidence"]["candidate_pool_eligible"], True, "retained plan candidate-pool eligibility")

            risk = load_json(risk_json)
            assessments = risk["assessments"]
            assert_equal(risk["output_status"], "研究草稿", "risk output status")
            assert_true("quantification_checks" in assessments[0], "risk output must expose quantification checks")
            assert_equal(assessments[0]["quantification_checks"]["historical_sample_count"], 2, "sample comparable history count")
            assert_equal(assessments[0]["quantification_checks"]["continuity_statuses"], ["stable"], "sample continuity status")
            assert_equal(assessments[0]["gradient_status"], "保", "first sample gradient")
            assert_true("不等于保证录取" in assessments[0]["filing_risk"]["rationale"], "risk rationale must reject guarantee wording")
            assert_equal(assessments[1]["gradient_status"], "不适用", "rejected sample gradient")

            gates = load_json(gates_json)
            assert_equal(gates["output_status"], "研究草稿", "gate output status")
            assert_equal(gates["can_upgrade"], False, "gate upgrade flag")
            enrollment_gate = next(item for item in gates["gates"] if item["id"] == "enrollment_plan_2026")
            assert_equal(enrollment_gate["status"], "fail", "enrollment gate status")
            precheck_report = load_json(precheck_report_json)
            assert_equal(precheck_report["output_status"], "核验草案", "submission precheck package output status")
            assert_equal(precheck_report["guardrail_passed"], True, "submission precheck package guardrail flag")
            assert_equal(precheck_report["summary"]["candidate_item_count"], 1, "submission precheck candidate item count")
            assert_true(
                "全量专业级招生计划" in precheck_report["summary"]["passed_gates"],
                "submission precheck must expose full major-level plan gate",
            )

            report_text = report_md.read_text(encoding="utf-8")
            province_status_text = province_status_md.read_text(encoding="utf-8")
            skill_text = (root / "SKILL.md").read_text(encoding="utf-8")
            output_status_text = (root / "references" / "gaokao-cn-output-status.md").read_text(encoding="utf-8")
            precheck_doc_text = (root / "references" / "gaokao-cn-submission-precheck-package.md").read_text(encoding="utf-8")
            gates_doc_text = (root / "references" / "gaokao-cn-submission-gates.md").read_text(encoding="utf-8")
            core_capabilities = "官方来源追踪、招生计划导入辅助、候选池过滤、防错清单、五维风险拆解、待核验项列表"
            assert_true(core_capabilities in skill_text, "SKILL.md must name the new gaokao-cn core capabilities")
            assert_true("默认输出状态是 `研究草稿` 或 `核验草案`" in output_status_text, "output status doc must default to draft/check-draft")
            assert_true("防越权检查" in precheck_doc_text, "precheck package doc must frame validator as anti-overclaim guardrail")
            assert_true("不是必须达成的产品目标" in precheck_doc_text, "precheck package doc must not frame submit-ready as product goal")
            assert_true("防越权检查" in gates_doc_text, "submission gates doc must frame gates as anti-overclaim checks")
            assert_true("省份包状态" in province_status_text, "province markdown must expose province pack status column")
            assert_true("省级来源已核验，缺全量专业级计划" in province_status_text, "province markdown must expose source-ready but data-incomplete status")
            assert_true("输出状态：研究草稿" in report_text, "report must expose output status")
            assert_true("五维风险表" in report_text, "report must include risk table")
            assert_true("排序状态：研究排序" in report_text, "report must include research ranking status")
            assert_true("建议序号" in report_text, "report must include ranking table")
            assert_true("防越权检查清单" in report_text, "report must include anti-overclaim checklist")
            assert_true("不是可直接提交的志愿表" in report_text, "report must clearly reject submit-ready positioning")

            overseas_text = overseas_plan_md.read_text(encoding="utf-8")
            assert_true("录取可行性" in overseas_text, "overseas planner must include admission section")
            assert_true("签证可行性" in overseas_text, "overseas planner must include visa section")
            assert_true("国内备选风险" in overseas_text, "overseas planner must include domestic backup section")

    except Exception as exc:  # noqa: BLE001
        print("run_self_test: failed", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    print("run_self_test: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
