#!/usr/bin/env python3
"""Compute gaokao-cn province-pack readiness for report gating."""

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


READY_STATUSES = {"published", "corrected"}
CORRECTION_READY_STATUSES = {"published", "corrected", "none_found_current", "monitor_current"}
FRESHNESS_KEYS = {
    "result_release",
    "control_lines",
    "one_score_one_rank",
    "volunteer_filling",
    "enrollment_plan",
    "plan_corrections",
}
SOURCE_GATE_KEYS = (
    "volunteer_filling",
    "result_release",
    "control_lines",
    "one_score_one_rank",
    "enrollment_plan",
    "plan_corrections",
)


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def load_data_source_coverage(root: Path) -> dict[str, dict[str, bool]]:
    path = root / "references" / "gaokao-cn-official-data-sources.yaml"
    data = load_yaml(path) if path.exists() else {}
    coverage: dict[str, dict[str, bool]] = {}
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        return coverage
    for source in sources:
        if not isinstance(source, dict):
            continue
        province = str(source.get("province") or "")
        if not province:
            continue
        entry = coverage.setdefault(
            province,
            {
                "enrollment_plan_full_major_level_2026": False,
                "one_score_one_rank_full_table_2026": False,
                "plan_corrections_full_notice_2026": False,
            },
        )
        if (
            source.get("year") == 2026
            and source.get("data_type") == "enrollment_plan"
            and source.get("coverage_level") == "full_major_level"
            and source.get("status") == "full_extracted"
            and source.get("candidate_pool_eligible") is True
        ):
            entry["enrollment_plan_full_major_level_2026"] = True
        if (
            source.get("year") == 2026
            and source.get("data_type") == "one_score_one_rank"
            and source.get("coverage_level") == "full_score_table"
            and source.get("status") == "full_extracted"
        ):
            entry["one_score_one_rank_full_table_2026"] = True
        if (
            source.get("year") == 2026
            and source.get("data_type") == "plan_correction"
            and source.get("coverage_level") == "full_correction_notice"
            and source.get("status") == "full_extracted"
        ):
            entry["plan_corrections_full_notice_2026"] = True
    return coverage


def status(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, dict):
        return "missing"
    return str(value.get("status") or "missing")


def is_ready(data: dict[str, Any], key: str) -> bool:
    accepted = CORRECTION_READY_STATUSES if key == "plan_corrections" else READY_STATUSES
    return status(data, key) in accepted


def source_gap(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if not isinstance(value, dict):
        return f"{key}: 缺少状态块"
    accepted = CORRECTION_READY_STATUSES if key == "plan_corrections" else READY_STATUSES
    if status(data, key) in accepted and not value.get("source_url"):
        return f"{key}: 已发布但缺少 source_url"
    if status(data, key) not in accepted:
        return f"{key}: {status(data, key)}"
    return None


def stale_gap(data: dict[str, Any], key: str, today: str) -> str | None:
    value = data.get(key)
    if not isinstance(value, dict):
        return None
    checked = value.get("last_checked_at") or data.get("last_checked_at")
    if checked != today:
        return f"{key}: last_checked_at={checked or 'missing'}"
    return None


def evaluate_pack(path: Path, today: str, coverage_by_province: dict[str, dict[str, bool]]) -> dict[str, Any]:
    data = load_yaml(path)
    province = data.get("province") or path.stem
    policy_ready = is_ready(data, "volunteer_filling")
    rank_ready = is_ready(data, "one_score_one_rank")
    control_ready = is_ready(data, "control_lines")
    plan_ready = is_ready(data, "enrollment_plan")
    corrections_ready = is_ready(data, "plan_corrections")
    score_release_ready = is_ready(data, "result_release")

    hard_gaps = [
        gap
        for gap in (
            source_gap(data, "volunteer_filling"),
            source_gap(data, "one_score_one_rank"),
            source_gap(data, "control_lines"),
            source_gap(data, "enrollment_plan"),
            source_gap(data, "plan_corrections"),
        )
        if gap
    ]
    stale_gaps = [gap for key in FRESHNESS_KEYS if (gap := stale_gap(data, key, today))]

    source_ready = all(
        [
            policy_ready,
            score_release_ready,
            rank_ready,
            control_ready,
            plan_ready,
            corrections_ready,
        ]
    )
    data_coverage = coverage_by_province.get(
        str(province),
        {
            "enrollment_plan_full_major_level_2026": False,
            "one_score_one_rank_full_table_2026": False,
            "plan_corrections_full_notice_2026": False,
        },
    )
    data_gaps = [
        key
        for key, ready in data_coverage.items()
        if key in {"enrollment_plan_full_major_level_2026"} and not ready
    ]
    precheck_candidate_possible = source_ready and not data_gaps
    submit_ready_possible = precheck_candidate_possible
    source_gate_ready_count = sum(1 for key in SOURCE_GATE_KEYS if is_ready(data, key))
    source_gate_total = len(SOURCE_GATE_KEYS)
    if precheck_candidate_possible:
        province_pack_status = "省级来源与全量专业级计划就绪"
    elif source_ready:
        province_pack_status = "省级来源已核验，缺全量专业级计划"
    elif source_gate_ready_count:
        province_pack_status = "省级来源部分核验"
    else:
        province_pack_status = "省级来源待补齐"

    return {
        "province": province,
        "year": data.get("year"),
        "cycle_status": data.get("cycle_status"),
        "output_status": "核验草案" if precheck_candidate_possible else "研究草稿",
        "province_pack_status": province_pack_status,
        "freshness_status": "需今日复核" if stale_gaps else "今日已复核",
        "source_ready_from_pack": source_ready,
        "precheck_candidate_from_pack": precheck_candidate_possible,
        "submit_ready_possible_from_pack": submit_ready_possible,
        "source_gate_ready_count": source_gate_ready_count,
        "source_gate_total": source_gate_total,
        "readiness": {
            "provincial_policy_2026": policy_ready,
            "score_release_2026": score_release_ready,
            "control_lines_2026": control_ready,
            "one_score_one_rank_2026": rank_ready,
            "enrollment_plan_2026": plan_ready,
            "plan_corrections_2026": corrections_ready,
        },
        "data_coverage": data_coverage,
        "statuses": {key: status(data, key) for key in sorted(FRESHNESS_KEYS)},
        "hard_gaps": hard_gaps,
        "data_gaps": data_gaps,
        "freshness_gaps": stale_gaps,
        "last_checked_at": data.get("last_checked_at"),
        "path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    today = date.today().isoformat()
    packs = sorted((root / "references").glob("gaokao-cn-province-*-2026.yaml"))
    if not packs:
        print("province_readiness: no province packs found", file=sys.stderr)
        return 1

    coverage_by_province = load_data_source_coverage(root)
    rows = [evaluate_pack(path, today, coverage_by_province) for path in packs]
    province_pack_status_counts: dict[str, int] = {}
    final_output_status_counts: dict[str, int] = {}
    for row in rows:
        province_pack_status = str(row["province_pack_status"])
        final_output_status = str(row["output_status"])
        province_pack_status_counts[province_pack_status] = province_pack_status_counts.get(province_pack_status, 0) + 1
        final_output_status_counts[final_output_status] = final_output_status_counts.get(final_output_status, 0) + 1
    output_data = {
        "generated_at": today,
        "summary": {
            "province_count": len(rows),
            "precheck_candidate_count": sum(1 for row in rows if row["precheck_candidate_from_pack"]),
            "submit_ready_count": sum(1 for row in rows if row["submit_ready_possible_from_pack"]),
            "source_ready_count": sum(1 for row in rows if row["source_ready_from_pack"]),
            "final_output_draft_count": final_output_status_counts.get("研究草稿", 0),
            "final_output_status_counts": final_output_status_counts,
            "province_pack_status_counts": province_pack_status_counts,
            "province_pack_pending_count": province_pack_status_counts.get("省级来源待补齐", 0),
            "stale_count": sum(1 for row in rows if row["freshness_gaps"]),
        },
        "provinces": rows,
    }
    output = json.dumps(output_data, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
