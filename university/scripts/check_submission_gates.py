#!/usr/bin/env python3
"""Check whether a gaokao-cn output may be marked submission-precheck."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


PASS = "pass"
FAIL = "fail"
PUBLISHED = {"published", "corrected"}
CORRECTION_PUBLISHED = {"published", "corrected", "none_found_current", "monitor_current"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def evidence_matches(evidence: list[dict[str, Any]], field: str, *, institution_code: str | None = None, levels: set[str] | None = None) -> list[dict[str, Any]]:
    accepted_levels = levels or {"official_current"}
    field_names = {field}
    if institution_code:
        field_names.add(f"{field}:{institution_code}")
    matches: list[dict[str, Any]] = []
    for item in evidence:
        if item.get("field") not in field_names:
            continue
        if str(item.get("applicable_year")) != "2026":
            continue
        if item.get("field_evidence_level") not in accepted_levels:
            continue
        matches.append(item)
    return matches


def gate(gate_id: str, status: str, reason: str, missing: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": gate_id,
        "status": status,
        "reason": reason,
        "missing": missing or [],
    }


def retained_items(candidate_pool: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in candidate_pool.get("items", [])
        if isinstance(item, dict) and item.get("keep_status") == "保留"
    ]


def check_provincial_policy(province_pack: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    volunteer_status = (province_pack.get("volunteer_filling") or {}).get("status")
    evidence_ok = bool(evidence_matches(evidence, "provincial_policy_2026"))
    missing: list[str] = []
    if volunteer_status not in PUBLISHED:
        missing.append("province_pack.volunteer_filling.status must be published/corrected")
    if not evidence_ok:
        missing.append("official_current evidence: provincial_policy_2026")
    status = PASS if not missing else FAIL
    reason = "2026 省级志愿政策证据已满足门槛。" if status == PASS else "缺少 2026 省级政策核验。"
    return gate("provincial_policy_2026", status, reason, missing)


def check_enrollment_plan(province_pack: dict[str, Any], candidate_pool: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    enrollment_status = (province_pack.get("enrollment_plan") or {}).get("status")
    correction_status = (province_pack.get("plan_corrections") or {}).get("status")
    retained = retained_items(candidate_pool)
    missing: list[str] = []
    if enrollment_status not in PUBLISHED:
        missing.append("province_pack.enrollment_plan.status must be published/corrected")
    if correction_status not in CORRECTION_PUBLISHED:
        missing.append("province_pack.plan_corrections.status must be published/corrected/none_found_current/monitor_current")
    if not evidence_matches(evidence, "enrollment_plan_2026"):
        missing.append("official_current evidence: enrollment_plan_2026")
    if not evidence_matches(evidence, "plan_corrections_2026"):
        missing.append("official_current evidence: plan_corrections_2026")
    if not retained:
        missing.append("candidate pool must contain at least one retained item")
    for item in retained:
        if item.get("proof_gaps"):
            missing.append(f"{item.get('candidate_item_id')}: candidate-pool proof_gaps unresolved")
    status = PASS if not missing else FAIL
    reason = "2026 招生计划及更正证据已满足门槛。" if status == PASS else "缺少 2026 招生计划或更正核验。"
    return gate("enrollment_plan_2026", status, reason, missing)


def check_candidate_rank(profile: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[str] = []
    if profile.get("rank") is None:
        missing.append("candidate profile rank is required")
    if profile.get("year") != 2026:
        missing.append("candidate profile year must be 2026")
    rank_evidence = evidence_matches(evidence, "candidate_rank", levels={"official_current", "user_supplied"})
    if not rank_evidence:
        missing.append("2026 evidence: candidate_rank")
    status = PASS if not missing else FAIL
    reason = "考生位次已存在并有 2026 证据。" if status == PASS else "缺少考生位次或位次证据。"
    return gate("candidate_rank", status, reason, missing)


def check_subject_qualification(profile: dict[str, Any], candidate_pool: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    missing: list[str] = []
    subject_profile = profile.get("subject_profile") or {}
    if not subject_profile.get("type"):
        missing.append("candidate subject_profile.type is required")
    if not evidence_matches(evidence, "subject_qualification"):
        missing.append("official_current evidence: subject_qualification")
    for item in retained_items(candidate_pool):
        for reason in item.get("reasons") or []:
            if any(marker in reason for marker in ("省份", "年份", "批次", "科类", "选科", "资格")):
                missing.append(f"{item.get('candidate_item_id')}: unresolved qualification reason {reason}")
    status = PASS if not missing else FAIL
    reason = "科类、选科、资格和批次条件已满足门槛。" if status == PASS else "缺少科类、选科、资格或批次核验。"
    return gate("subject_qualification", status, reason, missing)


def check_charter_restrictions(candidate_pool: dict[str, Any], risk_assessment: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    retained = retained_items(candidate_pool)
    risk_ids = {
        item.get("candidate_item_id")
        for item in risk_assessment.get("assessments", [])
        if isinstance(item, dict)
    }
    missing: list[str] = []
    for item in retained:
        institution_code = str(item.get("institution_code") or "")
        candidate_id = item.get("candidate_item_id")
        if candidate_id not in risk_ids:
            missing.append(f"{candidate_id}: missing risk assessment")
        if not evidence_matches(evidence, "charter_restrictions_2026", institution_code=institution_code):
            missing.append(f"{candidate_id}: official_current charter evidence for institution {institution_code}")
    status = PASS if not missing else FAIL
    reason = "保留候选项对应高校 2026 招生章程限制已满足门槛。" if status == PASS else "缺少高校 2026 招生章程限制核验。"
    return gate("charter_restrictions_2026", status, reason, missing)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--province-pack", type=Path, required=True)
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--risk-assessment", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        province_pack = load_yaml(args.province_pack)
        profile = load_json(args.profile)
        candidate_pool = load_json(args.candidate_pool)
        risk_assessment = load_json(args.risk_assessment)
        evidence = load_json(args.evidence)
    except Exception as exc:  # noqa: BLE001
        print(f"check_submission_gates: failed to load input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(profile, dict) or not isinstance(candidate_pool, dict) or not isinstance(risk_assessment, dict):
        print("check_submission_gates: profile, candidate-pool, and risk-assessment must be JSON objects", file=sys.stderr)
        return 1
    if not isinstance(evidence, list) or not all(isinstance(item, dict) for item in evidence):
        print("check_submission_gates: evidence must be a JSON array of objects", file=sys.stderr)
        return 1

    gates = [
        check_provincial_policy(province_pack, evidence),
        check_enrollment_plan(province_pack, candidate_pool, evidence),
        check_candidate_rank(profile, evidence),
        check_subject_qualification(profile, candidate_pool, evidence),
        check_charter_restrictions(candidate_pool, risk_assessment, evidence),
    ]
    guardrail_passed = all(item["status"] == PASS for item in gates)
    output_status = "核验草案" if guardrail_passed else "研究草稿"
    result = {
        "output_status": output_status,
        "guardrail_passed": guardrail_passed,
        "precheck_guard_status": "通过防越权检查" if guardrail_passed else "未通过防越权检查",
        "can_upgrade": guardrail_passed,
        "last_checked_at": date.today().isoformat(),
        "gates": gates,
        "final_system_check_required": "即使通过防越权检查，也必须在省级正式填报系统逐项核对代码、专业组、专业、计划人数、备注、费用、校区和确认状态；本脚本不生成可直接提交的志愿表。",
    }

    output = json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
