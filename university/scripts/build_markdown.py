#!/usr/bin/env python3
"""Generate a Markdown province-pack status table from structured YAML."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc

from province_readiness import evaluate_pack, load_data_source_coverage


GATE_KEYS = [
    "result_release",
    "control_lines",
    "one_score_one_rank",
    "volunteer_filling",
    "enrollment_plan",
    "plan_corrections",
]


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def render(root: Path) -> str:
    province_dir = root / "references"
    today = date.today().isoformat()
    coverage_by_province = load_data_source_coverage(root)
    lines = [
        "# 2026 省份包状态",
        "",
        "| 省份 | 省份包状态 | 最终状态 | 已核验门槛 | 今日复核 | 成绩 | 控制线 | 一分一段 | 志愿规则 | 招生计划 | 更正监控 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for path in sorted(province_dir.glob("gaokao-cn-province-*-2026.yaml")):
        data = load(path)
        readiness = evaluate_pack(path, today, coverage_by_province)
        statuses = [data.get(key, {}).get("status", "missing") for key in GATE_KEYS]
        lines.append(
            "| {province} | {province_pack_status} | {output_status} | {ready}/{total} | {freshness} | {statuses} |".format(
                province=data.get("province", path.stem),
                province_pack_status=readiness["province_pack_status"],
                output_status=readiness["output_status"],
                ready=readiness["source_gate_ready_count"],
                total=readiness["source_gate_total"],
                freshness=readiness["freshness_status"],
                statuses=" | ".join(statuses),
            )
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--write", type=Path, help="Optional output markdown path")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = render(root)
    if args.write:
        target = args.write if args.write.is_absolute() else root / args.write
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(output, encoding="utf-8")
        print(f"wrote {target}")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
