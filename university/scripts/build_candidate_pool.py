#!/usr/bin/env python3
"""Filter normalized enrollment-plan JSON into a candidate-pool review view."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


INACTIVE_STATUSES = {"cancelled", "replaced"}
HIGH_FEE_MARKERS = {"中外合作", "高收费", "国际课程", "合作办学"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_id(item: dict[str, Any]) -> str:
    parts = [
        item.get("province"),
        item.get("batch"),
        item.get("subject_category"),
        item.get("institution_code"),
        item.get("major_group_code") or "nogroup",
        item.get("major_code") or item.get("major_name"),
    ]
    return "|".join(str(part) for part in parts if part is not None)


def normalize_subject_type(subject_type: str) -> list[str]:
    mapping = {
        "physics": ["物理", "物理类", "理科"],
        "history": ["历史", "历史类", "文科"],
        "science": ["理科"],
        "arts": ["文科"],
    }
    return mapping.get(subject_type, [subject_type])


def profile_subjects(profile: dict[str, Any]) -> set[str]:
    subject_profile = profile.get("subject_profile") or {}
    subjects = set(subject_profile.get("selected_subjects") or [])
    for subject in normalize_subject_type(subject_profile.get("type", "")):
        if subject:
            subjects.add(subject)
    return subjects


def subject_category_matches(profile: dict[str, Any], item: dict[str, Any]) -> bool:
    category = str(item.get("subject_category") or "")
    subjects = profile_subjects(profile)
    if "物理" in category and not {"物理", "物理类", "physics"} & subjects:
        return False
    if "历史" in category and not {"历史", "历史类", "history"} & subjects:
        return False
    if "理科" in category and not {"理科", "science"} & subjects:
        return False
    if "文科" in category and not {"文科", "arts"} & subjects:
        return False
    return True


def selected_subjects_match(profile: dict[str, Any], item: dict[str, Any]) -> bool:
    required = set(item.get("selected_subject_requirements") or [])
    required.discard("不限")
    if not required:
        return True
    return required.issubset(profile_subjects(profile))


def tuition_value(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def contains_any(text: str, markers: set[str] | list[str]) -> bool:
    return any(marker and marker in text for marker in markers)


def evaluate_item(profile: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    proof_gaps: list[str] = []
    status = item.get("correction_status", "unknown")

    if item.get("province") != profile.get("province"):
        reasons.append("省份不符")
    if item.get("year") != profile.get("year"):
        reasons.append("年份不符")
    if item.get("batch") != profile.get("target_batch"):
        reasons.append("批次不符")
    if not subject_category_matches(profile, item):
        reasons.append("科类不符")
    if not selected_subjects_match(profile, item):
        reasons.append("选科不符")
    if status in INACTIVE_STATUSES:
        reasons.append("计划已取消或被替换")
    if status == "unknown":
        proof_gaps.append("更正状态待核验")

    source_file = item.get("source_file")
    if not source_file:
        proof_gaps.append("缺少来源文件")
    if not item.get("source_url"):
        proof_gaps.append("缺少来源 URL")
    if item.get("field_evidence_level") not in {"official_current"}:
        proof_gaps.append("招生计划字段证据不是 2026 当前官方精确来源")
    coverage_level = item.get("coverage_level") or "missing"
    if coverage_level != "full_major_level":
        reasons.append("招生计划不是专业组/专业级全量数据")
    if item.get("candidate_pool_eligible") is not True:
        reasons.append("招生计划来源未标记为可生成候选池")

    budget = profile.get("budget") or {}
    max_tuition = budget.get("max_annual_tuition")
    tuition = tuition_value(item.get("tuition"))
    if max_tuition is not None and tuition is not None and tuition > max_tuition:
        reasons.append("学费超过预算")
    if max_tuition is not None and tuition is None:
        proof_gaps.append("学费待核验")

    project_text = " ".join(
        str(item.get(field) or "")
        for field in ("project_type", "remarks", "major_name")
    )
    if budget.get("accept_high_fee_programs") is False and contains_any(project_text, HIGH_FEE_MARKERS):
        reasons.append("项目性质触及高收费或合作办学底线")
    if contains_any(project_text, profile.get("unacceptable_outcomes") or []):
        reasons.append("触及用户不能接受结果")

    major_excluded = (profile.get("major_preferences") or {}).get("excluded") or []
    if contains_any(str(item.get("major_name") or ""), major_excluded):
        reasons.append("专业触及排除偏好")

    if reasons:
        keep_status = "剔除"
    elif proof_gaps:
        keep_status = "待核验"
    else:
        keep_status = "保留"

    return {
        "candidate_item_id": candidate_id(item),
        "institution_code": item.get("institution_code"),
        "institution_name": item.get("institution_name"),
        "major_group_code": item.get("major_group_code") or "不适用",
        "major_code": item.get("major_code") or "不适用",
        "major_name": item.get("major_name"),
        "plan_count": item.get("plan_count"),
        "batch": item.get("batch"),
        "subject_category": item.get("subject_category"),
        "selected_subject_requirements": item.get("selected_subject_requirements") or [],
        "tuition": item.get("tuition"),
        "campus": item.get("campus"),
        "project_type": item.get("project_type"),
        "correction_status": status,
        "keep_status": keep_status,
        "reasons": reasons,
        "proof_gaps": proof_gaps,
        "evidence": {
            "evidence_id": item.get("evidence_id"),
            "source_file": source_file,
            "source_title": item.get("source_title"),
            "source_url": item.get("source_url"),
            "source_type": item.get("source_type"),
            "field_evidence_level": item.get("field_evidence_level"),
            "coverage_level": item.get("coverage_level"),
            "candidate_pool_eligible": item.get("candidate_pool_eligible"),
            "retrieved_at": item.get("retrieved_at"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True, help="candidate profile JSON")
    parser.add_argument("--plan", type=Path, required=True, help="normalized enrollment-plan JSON array")
    parser.add_argument("--output", type=Path, help="write JSON output")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        profile = load_json(args.profile)
        plan = load_json(args.plan)
    except Exception as exc:  # noqa: BLE001
        print(f"build_candidate_pool: failed to load input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(profile, dict):
        print("build_candidate_pool: profile must be a JSON object", file=sys.stderr)
        return 1
    if not isinstance(plan, list) or not all(isinstance(item, dict) for item in plan):
        print("build_candidate_pool: plan must be a JSON array of objects", file=sys.stderr)
        return 1
    if profile.get("rank") is None:
        print("build_candidate_pool: candidate rank is required before candidate-pool filtering", file=sys.stderr)
        return 1

    rows = [evaluate_item(profile, item) for item in plan]
    summary = {
        "output_status": "研究草稿",
        "status_reason": "候选池过滤不等于提交前核验；仍需核验 2026 省级政策、招生计划及更正、考生位次、选科资格和高校招生章程。",
        "counts": {
            "保留": sum(1 for row in rows if row["keep_status"] == "保留"),
            "待核验": sum(1 for row in rows if row["keep_status"] == "待核验"),
            "剔除": sum(1 for row in rows if row["keep_status"] == "剔除"),
        },
        "items": rows,
    }
    output = json.dumps(summary, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
