#!/usr/bin/env python3
"""Build a conservative gaokao-cn Markdown report from pipeline JSON outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def cell(value: Any) -> str:
    if value is None or value == "":
        return "待核验"
    if isinstance(value, list):
        return "、".join(str(item) for item in value) if value else "无"
    return str(value).replace("\n", " ")


def risk_cell(value: dict[str, Any] | None) -> str:
    if not isinstance(value, dict):
        return "待核验"
    gaps = value.get("proof_gaps") or []
    suffix = f"；缺口：{cell(gaps)}" if gaps else ""
    return f"{value.get('level', 'unknown')}：{cell(value.get('rationale'))}{suffix}"


def gate_status(gates: dict[str, Any]) -> str:
    return str(gates.get("output_status") or ("核验草案" if gates.get("guardrail_passed") or gates.get("can_upgrade") else "研究草稿"))


RISK_WEIGHT = {
    "low": 0,
    "medium": 1,
    "unknown": 2,
    "high": 3,
    "not_applicable": 4,
}

GRADIENT_WEIGHT = {
    "保": 0,
    "稳": 1,
    "冲": 2,
    "数据不足，不能判定冲稳保": 3,
    "不适用": 4,
}


def risk_weight(value: dict[str, Any] | None) -> int:
    if not isinstance(value, dict):
        return RISK_WEIGHT["unknown"]
    return RISK_WEIGHT.get(str(value.get("level") or "unknown"), RISK_WEIGHT["unknown"])


def ranking_score(item: dict[str, Any], assessment: dict[str, Any]) -> tuple[int, int, int, str]:
    gradient = str(assessment.get("gradient_status") or "数据不足，不能判定冲稳保")
    risk_total = sum(
        risk_weight(assessment.get(key))
        for key in (
            "qualification_risk",
            "filing_risk",
            "major_adjustment_risk",
            "withdrawal_risk",
            "outcome_acceptability_risk",
        )
    )
    proof_gap_count = len(item.get("proof_gaps") or []) + len((assessment.get("filing_risk") or {}).get("proof_gaps") or [])
    return (
        GRADIENT_WEIGHT.get(gradient, GRADIENT_WEIGHT["数据不足，不能判定冲稳保"]),
        risk_total,
        proof_gap_count,
        str(item.get("candidate_item_id") or ""),
    )


def build_ranking_rows(candidate_pool: dict[str, Any], risk: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    risk_by_id = {item.get("candidate_item_id"): item for item in risk.get("assessments", [])}
    retained = [
        item for item in candidate_pool.get("items", [])
        if item.get("keep_status") == "保留"
    ]
    rows = [(item, risk_by_id.get(item.get("candidate_item_id"), {})) for item in retained]
    return sorted(rows, key=lambda row: ranking_score(row[0], row[1]))


def build_report(profile: dict[str, Any], candidate_pool: dict[str, Any], risk: dict[str, Any], gates: dict[str, Any]) -> str:
    output_status = gate_status(gates)
    lines: list[str] = []
    lines.append("# gaokao-cn 志愿研究报告")
    lines.append("")
    lines.append(f"输出状态：{output_status}")
    lines.append("")
    lines.append("> 本报告只汇总已核验结构化结果；默认定位为研究草稿或核验草案，不是可直接提交的志愿表。")
    lines.append("")

    lines.append("## 状态与门槛")
    lines.append("")
    lines.append("| 门槛 | 状态 | 说明 |")
    lines.append("| --- | --- | --- |")
    for gate in gates.get("gates", []):
        lines.append(f"| {cell(gate.get('label') or gate.get('id'))} | {cell(gate.get('status'))} | {cell(gate.get('rationale') or gate.get('proof_gaps'))} |")
    lines.append("")

    subject_profile = profile.get("subject_profile") or {}
    budget = profile.get("budget") or {}
    lines.append("## 考生画像")
    lines.append("")
    lines.append("| 字段 | 内容 |")
    lines.append("| --- | --- |")
    lines.append(f"| 省份/年份 | {cell(profile.get('province'))} / {cell(profile.get('year'))} |")
    lines.append(f"| 科类/选科 | {cell(subject_profile.get('type'))} / {cell(subject_profile.get('selected_subjects'))} |")
    lines.append(f"| 分数/位次 | {cell(profile.get('score'))} / {cell(profile.get('rank'))} |")
    lines.append(f"| 目标批次 | {cell(profile.get('target_batch'))} |")
    lines.append(f"| 预算 | {cell(budget.get('max_annual_tuition'))}；高收费项目：{cell(budget.get('accept_high_fee_programs'))} |")
    lines.append(f"| 调剂底线 | {cell(profile.get('adjustment_acceptance'))} |")
    lines.append(f"| 不能接受项 | {cell(profile.get('unacceptable_outcomes'))} |")
    lines.append("")

    lines.append("## 候选池核验表")
    lines.append("")
    lines.append("| 候选项 | 计划/更正 | 选科 | 费用/校区/项目 | 保留状态 | 证据 |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for item in candidate_pool.get("items", []):
        evidence = item.get("evidence") or {}
        candidate = f"{cell(item.get('institution_name'))} {cell(item.get('major_group_code'))} {cell(item.get('major_name'))}"
        plan = f"{cell(item.get('plan_count'))} / {cell(item.get('correction_status'))}"
        fee = f"{cell(item.get('tuition'))} / {cell(item.get('campus'))} / {cell(item.get('project_type'))}"
        evidence_text = f"{cell(evidence.get('evidence_id'))}；{cell(evidence.get('field_evidence_level'))}"
        lines.append(f"| {candidate} | {plan} | {cell(item.get('selected_subject_requirements'))} | {fee} | {cell(item.get('keep_status'))}：{cell(item.get('reasons') or item.get('proof_gaps'))} | {evidence_text} |")
    lines.append("")

    risk_by_id = {item.get("candidate_item_id"): item for item in risk.get("assessments", [])}
    lines.append("## 五维风险表")
    lines.append("")
    lines.append("| 候选项 | 报考资格 | 投档 | 专业/调剂 | 退档 | 结果可接受度 | 冲稳保 | 量化检查 |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in candidate_pool.get("items", []):
        assessment = risk_by_id.get(item.get("candidate_item_id"), {})
        checks = assessment.get("quantification_checks") or {}
        check_text = f"样本 {cell(checks.get('historical_sample_count'))}；停止原因：{cell(checks.get('stop_reasons'))}"
        lines.append(
            "| "
            + " | ".join(
                [
                    cell(item.get("candidate_item_id")),
                    risk_cell(assessment.get("qualification_risk")),
                    risk_cell(assessment.get("filing_risk")),
                    risk_cell(assessment.get("major_adjustment_risk")),
                    risk_cell(assessment.get("withdrawal_risk")),
                    risk_cell(assessment.get("outcome_acceptability_risk")),
                    cell(assessment.get("gradient_status")),
                    check_text,
                ]
            )
            + " |"
        )
    lines.append("")

    lines.append("## 排序建议")
    lines.append("")
    lines.append("排序状态：研究排序")
    lines.append("")
    lines.append("下表只能作为研究排序建议，不是可直接提交的志愿表。排序只引用已保留候选项和五维风险结果。")
    lines.append("")
    ranking_rows = build_ranking_rows(candidate_pool, risk)
    if not ranking_rows:
        lines.append("当前没有通过候选池核验的保留项，不能生成排序建议。")
    else:
        lines.append("| 建议序号 | 候选项 | 冲稳保 | 排序依据 | 不得忽略的缺口 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for index, (item, assessment) in enumerate(ranking_rows, start=1):
            candidate = f"{cell(item.get('institution_name'))} {cell(item.get('major_group_code'))} {cell(item.get('major_name'))}"
            risks = [
                f"资格{cell((assessment.get('qualification_risk') or {}).get('level'))}",
                f"投档{cell((assessment.get('filing_risk') or {}).get('level'))}",
                f"调剂{cell((assessment.get('major_adjustment_risk') or {}).get('level'))}",
                f"退档{cell((assessment.get('withdrawal_risk') or {}).get('level'))}",
                f"结果{cell((assessment.get('outcome_acceptability_risk') or {}).get('level'))}",
            ]
            gaps = []
            for key in ("qualification_risk", "filing_risk", "major_adjustment_risk", "withdrawal_risk", "outcome_acceptability_risk"):
                gaps.extend((assessment.get(key) or {}).get("proof_gaps") or [])
            gaps.extend(item.get("proof_gaps") or [])
            lines.append(
                f"| {index} | {candidate} | {cell(assessment.get('gradient_status'))} | {'；'.join(risks)} | {cell(sorted(set(gaps)))} |"
            )
    lines.append("")

    lines.append("## 防越权检查清单")
    lines.append("")
    lines.append("这份清单用于避免把草案包装成最终志愿表；通过检查也不代表录取承诺或正式提交结果。")
    lines.append("")
    lines.append("- 2026 省级政策、填报时间、志愿单位、确认方式。")
    lines.append("- 2026 招生计划及全部更正、增补、取消、替换关系。")
    lines.append("- 考生位次、科类/选科、批次和专项资格。")
    lines.append("- 院校代码、专业组代码、专业代码、计划人数、学费、校区、备注。")
    lines.append("- 高校 2026 招生章程中的体检、单科、外语、投档比例、专业录取和调剂规则。")
    lines.append("- 正式填报系统中的志愿顺序和确认状态。")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--risk-assessment", type=Path, required=True)
    parser.add_argument("--gates", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_report(
        load_json(args.profile),
        load_json(args.candidate_pool),
        load_json(args.risk_assessment),
        load_json(args.gates),
    )
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
