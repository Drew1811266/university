#!/usr/bin/env python3
"""Validate a candidate-item-level gaokao submission precheck package."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


OFFICIAL_CURRENT = "official_current"
RANK_EVIDENCE_LEVELS = {OFFICIAL_CURRENT, "user_supplied"}
PLAN_SOURCE_TYPES = {
    "provincial_enrollment_plan",
    "provincial_plan_correction",
    "official_auxiliary_system",
    "official_publication",
}
ACTIVE_CORRECTION_STATUSES = {"active", "added", "corrected"}
CORRECTION_CHECK_STATUSES = {"checked", "corrected", "none_found_current", "monitor_current"}
REQUIRED_CHARTER_RULES = {
    "physical_exam",
    "single_subject",
    "foreign_language",
    "filing_ratio",
    "major_admission",
    "adjustment_rule",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def add(errors: list[str], path: str, message: str) -> None:
    errors.append(f"{path}: {message}")


def required_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def missing_value(value: Any) -> bool:
    return value is None or value == ""


def evidence_common(
    evidence: Any,
    path: str,
    errors: list[str],
    *,
    accepted_levels: set[str],
    require_official_url: bool = True,
) -> None:
    if not isinstance(evidence, dict):
        add(errors, path, "must be an object")
        return
    for field in ("source_title", "applicable_year", "field_evidence_level", "retrieved_at"):
        if evidence.get(field) in {None, ""}:
            add(errors, f"{path}.{field}", "is required")
    if require_official_url and not required_text(evidence.get("source_url")):
        add(errors, f"{path}.source_url", "is required")
    if evidence.get("applicable_year") != 2026:
        add(errors, f"{path}.applicable_year", "must be 2026")
    if evidence.get("field_evidence_level") not in accepted_levels:
        add(errors, f"{path}.field_evidence_level", f"must be one of {sorted(accepted_levels)}")


def profile_subjects(profile: dict[str, Any]) -> set[str]:
    subject_profile = profile.get("subject_profile") or {}
    subjects = set(subject_profile.get("selected_subjects") or [])
    subject_type = subject_profile.get("type")
    mapping = {
        "physics": {"物理", "物理类", "physics"},
        "history": {"历史", "历史类", "history"},
        "science": {"理科", "science"},
        "arts": {"文科", "arts"},
    }
    subjects.update(mapping.get(subject_type, {subject_type} if subject_type else set()))
    return {str(subject) for subject in subjects if subject}


def validate_profile(profile: Any, errors: list[str]) -> dict[str, Any]:
    if not isinstance(profile, dict):
        add(errors, "candidate_profile", "must be an object")
        return {}
    for field in ("province", "year", "subject_profile", "rank", "target_batch"):
        if missing_value(profile.get(field)):
            add(errors, f"candidate_profile.{field}", "is required")
    if profile.get("year") != 2026:
        add(errors, "candidate_profile.year", "must be 2026")
    if not isinstance(profile.get("rank"), int) or profile.get("rank", 0) < 1:
        add(errors, "candidate_profile.rank", "must be a positive integer")
    if not isinstance(profile.get("subject_profile"), dict) or not profile["subject_profile"].get("type"):
        add(errors, "candidate_profile.subject_profile.type", "is required")
    return profile


def validate_candidate_rank(package: dict[str, Any], profile: dict[str, Any], errors: list[str]) -> None:
    evidence = package.get("candidate_rank_evidence")
    evidence_common(evidence, "candidate_rank_evidence", errors, accepted_levels=RANK_EVIDENCE_LEVELS)
    if not isinstance(evidence, dict):
        return
    if evidence.get("rank") != profile.get("rank"):
        add(errors, "candidate_rank_evidence.rank", "must match candidate_profile.rank")
    if evidence.get("rank_basis") not in {"official_score_query", "one_score_one_rank", "official_user_export"}:
        add(errors, "candidate_rank_evidence.rank_basis", "must identify the official rank basis")
    if evidence.get("sensitive_info_redacted") is not True:
        add(errors, "candidate_rank_evidence.sensitive_info_redacted", "must be true")


def validate_policy_and_corrections(package: dict[str, Any], errors: list[str]) -> None:
    evidence_common(
        package.get("provincial_policy_evidence"),
        "provincial_policy_evidence",
        errors,
        accepted_levels={OFFICIAL_CURRENT},
    )
    corrections = package.get("plan_corrections_evidence")
    evidence_common(
        corrections,
        "plan_corrections_evidence",
        errors,
        accepted_levels={OFFICIAL_CURRENT},
    )
    if isinstance(corrections, dict) and corrections.get("status") not in CORRECTION_CHECK_STATUSES:
        add(errors, "plan_corrections_evidence.status", f"must be one of {sorted(CORRECTION_CHECK_STATUSES)}")


def validate_plan_item(
    item: dict[str, Any],
    index: int,
    profile: dict[str, Any],
    errors: list[str],
) -> None:
    path = f"candidate_items[{index}].plan_item"
    plan = item.get("plan_item")
    if not isinstance(plan, dict):
        add(errors, path, "is required")
        return
    required_fields = {
        "province",
        "year",
        "batch",
        "subject_category",
        "institution_code",
        "institution_name",
        "major_name",
        "plan_count",
        "source_file",
        "source_url",
        "source_type",
        "field_evidence_level",
        "coverage_level",
        "candidate_pool_eligible",
        "correction_status",
    }
    for field in sorted(required_fields):
        if missing_value(plan.get(field)):
            add(errors, f"{path}.{field}", "is required")
    if plan.get("province") != profile.get("province"):
        add(errors, f"{path}.province", "must match candidate profile province")
    if plan.get("year") != 2026:
        add(errors, f"{path}.year", "must be 2026")
    if plan.get("batch") != profile.get("target_batch"):
        add(errors, f"{path}.batch", "must match candidate target_batch")
    if plan.get("source_type") not in PLAN_SOURCE_TYPES:
        add(errors, f"{path}.source_type", f"must be one of {sorted(PLAN_SOURCE_TYPES)}")
    if plan.get("field_evidence_level") != OFFICIAL_CURRENT:
        add(errors, f"{path}.field_evidence_level", "must be official_current")
    if plan.get("coverage_level") != "full_major_level":
        add(errors, f"{path}.coverage_level", "must be full_major_level")
    if plan.get("candidate_pool_eligible") is not True:
        add(errors, f"{path}.candidate_pool_eligible", "must be true")
    if plan.get("correction_status") not in ACTIVE_CORRECTION_STATUSES:
        add(errors, f"{path}.correction_status", f"must be one of {sorted(ACTIVE_CORRECTION_STATUSES)}")
    if not isinstance(plan.get("plan_count"), int) or plan.get("plan_count", -1) < 0:
        add(errors, f"{path}.plan_count", "must be a non-negative integer")


def validate_subject_qualification(
    item: dict[str, Any],
    index: int,
    profile: dict[str, Any],
    errors: list[str],
) -> None:
    path = f"candidate_items[{index}].subject_qualification"
    subject = item.get("subject_qualification")
    evidence_common(subject, path, errors, accepted_levels={OFFICIAL_CURRENT})
    if not isinstance(subject, dict):
        return
    if subject.get("status") != "pass":
        add(errors, f"{path}.status", "must be pass")
    plan = item.get("plan_item") if isinstance(item.get("plan_item"), dict) else {}
    required = {
        str(value)
        for value in (plan.get("selected_subject_requirements") or [])
        if str(value) and str(value) != "不限"
    }
    matched = {str(value) for value in (subject.get("matched_requirements") or [])}
    candidate_subjects = profile_subjects(profile)
    if not required.issubset(candidate_subjects):
        add(errors, f"{path}.matched_requirements", "candidate subjects do not satisfy plan selected_subject_requirements")
    if not required.issubset(matched):
        add(errors, f"{path}.matched_requirements", "must include every non-unlimited plan selected_subject_requirement")
    if subject.get("proof_gaps"):
        add(errors, f"{path}.proof_gaps", "must be empty for submission precheck")


def validate_charter_restrictions(item: dict[str, Any], index: int, errors: list[str]) -> None:
    path = f"candidate_items[{index}].charter_restrictions"
    charter = item.get("charter_restrictions")
    evidence_common(charter, path, errors, accepted_levels={OFFICIAL_CURRENT})
    if not isinstance(charter, dict):
        return
    if charter.get("status") != "pass":
        add(errors, f"{path}.status", "must be pass")
    plan = item.get("plan_item") if isinstance(item.get("plan_item"), dict) else {}
    if charter.get("institution_code") != plan.get("institution_code"):
        add(errors, f"{path}.institution_code", "must match plan_item.institution_code")
    rules = charter.get("rules")
    if not isinstance(rules, dict):
        add(errors, f"{path}.rules", "must be an object")
        return
    for rule in sorted(REQUIRED_CHARTER_RULES):
        if not required_text(rules.get(rule)):
            add(errors, f"{path}.rules.{rule}", "is required")
    if charter.get("proof_gaps"):
        add(errors, f"{path}.proof_gaps", "must be empty for submission precheck")


def validate_candidate_items(package: dict[str, Any], profile: dict[str, Any], errors: list[str]) -> int:
    items = package.get("candidate_items")
    if not isinstance(items, list) or not items:
        add(errors, "candidate_items", "must be a non-empty array")
        return 0
    seen_ids: set[str] = set()
    for index, item in enumerate(items):
        path = f"candidate_items[{index}]"
        if not isinstance(item, dict):
            add(errors, path, "must be an object")
            continue
        candidate_id = item.get("candidate_item_id")
        if not required_text(candidate_id):
            add(errors, f"{path}.candidate_item_id", "is required")
        elif candidate_id in seen_ids:
            add(errors, f"{path}.candidate_item_id", "must be unique")
        else:
            seen_ids.add(candidate_id)
        validate_plan_item(item, index, profile, errors)
        validate_subject_qualification(item, index, profile, errors)
        validate_charter_restrictions(item, index, errors)
    return len(items)


def build_report(errors: list[str], candidate_item_count: int) -> dict[str, Any]:
    guardrail_passed = not errors
    return {
        "output_status": "核验草案" if guardrail_passed else "研究草稿",
        "guardrail_passed": guardrail_passed,
        "precheck_guard_status": "通过防越权检查" if guardrail_passed else "未通过防越权检查",
        "can_upgrade": guardrail_passed,
        "last_checked_at": date.today().isoformat(),
        "summary": {
            "candidate_item_count": candidate_item_count,
            "passed_gates": [
                "2026省级政策",
                "全量专业级招生计划",
                "招生计划更正检查",
                "考生位次",
                "选科资格",
                "高校招生章程限制",
            ] if guardrail_passed else [],
            "failed_gate_count": len(errors),
        },
        "gaps": errors,
        "final_system_check_required": "本校验只用于防越权检查；通过后仍必须在省级正式填报系统逐项核对代码、专业组、专业、计划人数、备注、费用、校区和确认状态，不能把结果称为可直接提交的志愿表。",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        package = load_json(args.package)
    except Exception as exc:  # noqa: BLE001
        print(f"validate_submission_precheck_package: failed to load input: {exc}", file=sys.stderr)
        return 2
    if not isinstance(package, dict):
        print("validate_submission_precheck_package: package must be a JSON object", file=sys.stderr)
        return 2

    errors: list[str] = []
    if not required_text(package.get("province")):
        add(errors, "province", "is required")
    if package.get("year") != 2026:
        add(errors, "year", "must be 2026")
    profile = validate_profile(package.get("candidate_profile"), errors)
    if profile and package.get("province") != profile.get("province"):
        add(errors, "province", "must match candidate_profile.province")
    validate_candidate_rank(package, profile, errors)
    validate_policy_and_corrections(package, errors)
    candidate_item_count = validate_candidate_items(package, profile, errors)
    report = build_report(errors, candidate_item_count)

    output = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    if errors:
        print("validate_submission_precheck_package: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        if not args.output:
            print(output)
        return 1
    if not args.output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
