#!/usr/bin/env python3
"""Build conservative five-dimension gaokao risk assessments."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


DATA_INSUFFICIENT = "数据不足，不能判定冲稳保"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def risk(level: str, rationale: str, proof_gaps: list[str] | None = None) -> dict[str, Any]:
    return {
        "level": level,
        "rationale": rationale,
        "proof_gaps": proof_gaps or [],
    }


def comparable_history(profile: dict[str, Any], item: dict[str, Any], historical: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for record in historical:
        if record.get("province") != profile.get("province"):
            continue
        if record.get("batch") != item.get("batch"):
            continue
        if record.get("subject_category") != item.get("subject_category"):
            continue
        if record.get("institution_code") != item.get("institution_code"):
            continue
        item_group = item.get("major_group_code")
        if item_group and item_group != "不适用" and record.get("major_group_code") not in {item_group, None, ""}:
            continue
        item_major = item.get("major_code")
        if item_major and item_major != "不适用" and record.get("major_code") not in {item_major, None, ""}:
            continue
        if record.get("comparability_status") != "comparable":
            continue
        if record.get("continuity_status") != "stable":
            continue
        if record.get("change_flags"):
            continue
        if record.get("field_evidence_level") != "official_historical":
            continue
        matches.append(record)
    return matches


def int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def quantification_checks(item: dict[str, Any], matches: list[dict[str, Any]]) -> dict[str, Any]:
    historical_plan_counts = [count for record in matches if (count := int_or_none(record.get("plan_count"))) is not None]
    current_plan_count = int_or_none(item.get("plan_count"))
    plan_count_change_ratio = None
    stop_reasons: list[str] = []

    if len(matches) < 2:
        stop_reasons.append("可比官方历史位次少于 2 年")

    if current_plan_count is None:
        stop_reasons.append("缺少 2026 计划人数")
    elif historical_plan_counts:
        median_plan_count = statistics.median(historical_plan_counts)
        if median_plan_count:
            plan_count_change_ratio = abs(current_plan_count - median_plan_count) / median_plan_count
            if plan_count_change_ratio > 0.3:
                stop_reasons.append("2026 计划人数较可比历史中位数变化超过 30%")
    else:
        stop_reasons.append("缺少历史计划人数，不能判断计划变化")

    ranks = [int(record["minimum_rank"]) for record in matches if record.get("minimum_rank")]
    continuity_statuses = sorted({str(record.get("continuity_status") or "unknown") for record in matches})
    change_flags = sorted({flag for record in matches for flag in (record.get("change_flags") or [])})
    if any(status != "stable" for status in continuity_statuses):
        stop_reasons.append("可比历史记录未全部标记为 stable 连续性")
    if change_flags:
        stop_reasons.append("可比历史记录包含结构变化标记")
    if len(ranks) >= 2 and min(ranks) > 0:
        rank_volatility_ratio = (max(ranks) - min(ranks)) / min(ranks)
        if rank_volatility_ratio > 0.35:
            stop_reasons.append("可比历史位次波动超过 35%")
    else:
        rank_volatility_ratio = None

    return {
        "historical_sample_count": len(matches),
        "current_plan_count": current_plan_count,
        "historical_plan_count_count": len(historical_plan_counts),
        "plan_count_change_ratio": plan_count_change_ratio,
        "rank_volatility_ratio": rank_volatility_ratio,
        "continuity_statuses": continuity_statuses,
        "change_flags": change_flags,
        "stop_reasons": stop_reasons,
    }


def filing_risk(profile: dict[str, Any], item: dict[str, Any], historical: list[dict[str, Any]]) -> tuple[dict[str, Any], str, list[str], dict[str, Any]]:
    rank = profile.get("rank")
    if rank is None:
        return risk("unknown", "缺少考生位次，不能判断投档风险。", ["考生位次"]), DATA_INSUFFICIENT, [], {
            "historical_sample_count": 0,
            "current_plan_count": int_or_none(item.get("plan_count")),
            "historical_plan_count_count": 0,
            "plan_count_change_ratio": None,
            "rank_volatility_ratio": None,
            "continuity_statuses": [],
            "change_flags": [],
            "stop_reasons": ["缺少考生位次"],
        }

    matches = comparable_history(profile, item, historical)
    checks = quantification_checks(item, matches)
    if not matches:
        return (
            risk(
                "unknown",
                "缺少同省、同批次、同科类、同志愿单位且官方历史来源支持的可比位次。",
                ["可比历史位次", "专业组连续性", "计划人数变化"],
            ),
            DATA_INSUFFICIENT,
            [],
            checks,
        )

    if checks["stop_reasons"]:
        return (
            risk(
                "unknown",
                "；".join(checks["stop_reasons"]) + "，不能量化投档梯度。",
                checks["stop_reasons"],
            ),
            DATA_INSUFFICIENT,
            [],
            checks,
        )

    ranks = [int(record["minimum_rank"]) for record in matches]
    median_rank = statistics.median(ranks)
    ratio = rank / median_rank
    evidence_ids = [
        f"{record.get('year')}:{record.get('institution_code')}:{record.get('major_group_code') or 'nogroup'}:{record.get('major_code') or 'nomajor'}"
        for record in matches
    ]

    if ratio <= 0.9:
        return (
            risk(
                "low",
                f"考生位次 {rank} 优于可比历史最低位次中位数 {int(median_rank)} 约 10% 以上；这只支持投档维度较低风险，不等于保证录取。",
            ),
            "保",
            evidence_ids,
            checks,
        )
    if ratio <= 1.0:
        return (
            risk(
                "medium",
                f"考生位次 {rank} 不差于可比历史最低位次中位数 {int(median_rank)}，但仍需核验计划变化和热度波动。",
            ),
            "稳",
            evidence_ids,
            checks,
        )
    if ratio <= 1.08:
        return (
            risk(
                "high",
                f"考生位次 {rank} 略低于可比历史最低位次中位数 {int(median_rank)}，只能视为冲刺维度。",
            ),
            "冲",
            evidence_ids,
            checks,
        )
    return (
        risk(
            "high",
            f"考生位次 {rank} 明显低于可比历史最低位次中位数 {int(median_rank)}，投档风险高。",
        ),
        "冲",
        evidence_ids,
        checks,
    )


def qualification_risk(item: dict[str, Any]) -> dict[str, Any]:
    reasons = item.get("reasons") or []
    qualification_reasons = [reason for reason in reasons if any(marker in reason for marker in ("省份", "年份", "批次", "科类", "选科", "资格", "取消", "替换"))]
    if qualification_reasons:
        return risk("high", "；".join(qualification_reasons), [])
    gaps = [gap for gap in item.get("proof_gaps") or [] if any(marker in gap for marker in ("更正", "来源", "资格"))]
    if gaps:
        return risk("unknown", "资格和计划有效性仍有待核验证据。", gaps)
    return risk("low", "候选池过滤未发现省份、年份、批次、科类、选科或计划有效性硬性冲突。")


def major_adjustment_risk(profile: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(str(item.get(field) or "") for field in ("major_name", "project_type", "campus"))
    unacceptable = profile.get("unacceptable_outcomes") or []
    if any(marker and marker in text for marker in unacceptable):
        return risk("high", "专业、项目性质或校区触及用户不能接受结果。")
    if profile.get("adjustment_acceptance") in {"reject", "conditional"}:
        return risk(
            "unknown",
            "用户对调剂存在限制，仍需核验专业组内全部专业和高校 2026 招生章程的专业录取/调剂规则。",
            ["组内全部专业", "高校 2026 招生章程", "调剂范围"],
        )
    return risk("unknown", "尚未核验专业组内全部专业和 2026 调剂规则。", ["组内全部专业", "高校 2026 招生章程"])


def withdrawal_risk(profile: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    gaps = ["高校 2026 招生章程", "体检限制", "单科限制", "外语语种", "投档比例"]
    if profile.get("adjustment_acceptance") == "reject":
        return risk("high", "用户不服从调剂时，若专业录取不确定或章程存在退档条件，退档风险可能较高。", gaps)
    return risk("unknown", "未核验高校 2026 招生章程前，不能确认退档风险。", gaps)


def outcome_acceptability_risk(profile: dict[str, Any], item: dict[str, Any]) -> dict[str, Any]:
    if item.get("keep_status") == "剔除":
        reasons = item.get("reasons") or ["候选池过滤已剔除"]
        return risk("high", "；".join(reasons), item.get("proof_gaps") or [])
    if item.get("proof_gaps"):
        return risk("unknown", "费用、校区、项目性质或来源字段仍有待核验。", item.get("proof_gaps"))
    return risk("low", "候选池过滤未发现费用、校区、项目性质或用户底线冲突。")


def assess_item(profile: dict[str, Any], item: dict[str, Any], historical: list[dict[str, Any]]) -> dict[str, Any]:
    filing, gradient, evidence_ids, checks = filing_risk(profile, item, historical)
    if item.get("keep_status") == "剔除":
        gradient = "不适用"
        filing = risk("not_applicable", "候选池已剔除该条目，不进入投档梯度判断。")

    return {
        "candidate_item_id": item.get("candidate_item_id"),
        "qualification_risk": qualification_risk(item),
        "filing_risk": filing,
        "major_adjustment_risk": major_adjustment_risk(profile, item),
        "withdrawal_risk": withdrawal_risk(profile, item),
        "outcome_acceptability_risk": outcome_acceptability_risk(profile, item),
        "gradient_status": gradient,
        "quantification_checks": checks,
        "evidence_ids": evidence_ids,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--historical-ranks", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    try:
        profile = load_json(args.profile)
        candidate_pool = load_json(args.candidate_pool)
        historical = load_json(args.historical_ranks)
    except Exception as exc:  # noqa: BLE001
        print(f"build_risk_assessment: failed to load input: {exc}", file=sys.stderr)
        return 1

    if not isinstance(profile, dict):
        print("build_risk_assessment: profile must be an object", file=sys.stderr)
        return 1
    if not isinstance(candidate_pool, dict) or not isinstance(candidate_pool.get("items"), list):
        print("build_risk_assessment: candidate pool must contain items list", file=sys.stderr)
        return 1
    if not isinstance(historical, list) or not all(isinstance(item, dict) for item in historical):
        print("build_risk_assessment: historical ranks must be an array of objects", file=sys.stderr)
        return 1

    assessments = [assess_item(profile, item, historical) for item in candidate_pool["items"]]
    output_data = {
        "output_status": "研究草稿",
        "status_reason": "风险评估脚本不等于提交前核验；提交前仍需核验 2026 省级政策、招生计划及更正、考生位次、选科资格和高校招生章程。",
        "assessments": assessments,
    }
    output = json.dumps(output_data, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
