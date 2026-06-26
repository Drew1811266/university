#!/usr/bin/env python3
"""Summarize source freshness and monitoring status for province packs."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


MONITORED_KEYS = [
    "result_release",
    "score_review",
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root).resolve()
    province_dir = root / "references"

    today = date.today().isoformat()
    stale_count = 0
    for path in sorted(province_dir.glob("gaokao-cn-province-*-2026.yaml")):
        data = load(path)
        print(f"# {data.get('province', path.stem)} {data.get('year', '')}")
        print(f"cycle_status: {data.get('cycle_status')} last_checked_at: {data.get('last_checked_at')}")
        if data.get("last_checked_at") != today:
            stale_count += 1
            print(f"freshness: needs check today ({today})")
        else:
            print("freshness: checked today")
        for key in MONITORED_KEYS:
            item = data.get(key, {})
            if not isinstance(item, dict):
                continue
            print(f"- {key}: {item.get('status')} | {item.get('source_title') or 'no source title'}")
        print()

    if stale_count:
        print(f"detect_source_changes: {stale_count} province pack(s) need a new daily check")
    else:
        print("detect_source_changes: all province packs checked today")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
