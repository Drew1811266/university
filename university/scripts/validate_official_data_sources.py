#!/usr/bin/env python3
"""Validate official gaokao data-source coverage metadata."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


REQUIRED_FIELDS = {
    "id",
    "province",
    "year",
    "data_type",
    "status",
    "coverage_level",
    "candidate_pool_eligible",
    "source_title",
    "source_url",
    "source_type",
    "retrieved_at",
}

STATUSES = {
    "sampled",
    "full_extracted",
    "source_verified_not_extracted",
    "monitor_current",
    "missing",
    "stale",
}

COVERAGE_LEVELS = {
    "sample_rows",
    "school_level_summary",
    "full_major_level",
    "full_score_table",
    "full_correction_notice",
    "source_only",
}

DATA_TYPES = {
    "one_score_one_rank",
    "enrollment_plan",
    "enrollment_plan_summary",
    "plan_correction",
    "historical_rank",
    "volunteer_filling",
    "control_lines",
    "score_release",
}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def validate_source(source: dict[str, Any], index: int, errors: list[str], root: Path) -> None:
    prefix = f"sources[{index}] {source.get('id', '<missing id>')}"
    missing = sorted(field for field in REQUIRED_FIELDS if field not in source)
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(missing)}")
        return

    if source.get("year") != 2026 and source.get("data_type") not in {"historical_rank"}:
        errors.append(f"{prefix}: non-historical sources must use year 2026")
    if source.get("status") not in STATUSES:
        errors.append(f"{prefix}: invalid status {source.get('status')}")
    if source.get("coverage_level") not in COVERAGE_LEVELS:
        errors.append(f"{prefix}: invalid coverage_level {source.get('coverage_level')}")
    if source.get("data_type") not in DATA_TYPES:
        errors.append(f"{prefix}: invalid data_type {source.get('data_type')}")
    if not str(source.get("source_url") or "").startswith(("http://", "https://")):
        errors.append(f"{prefix}: source_url must be http(s)")
    if not isinstance(source.get("candidate_pool_eligible"), bool):
        errors.append(f"{prefix}: candidate_pool_eligible must be boolean")

    eligible = bool(source.get("candidate_pool_eligible"))
    data_type = source.get("data_type")
    coverage = source.get("coverage_level")
    status = source.get("status")

    if eligible and data_type != "enrollment_plan":
        errors.append(f"{prefix}: only enrollment_plan sources can be candidate_pool_eligible")
    if eligible and coverage != "full_major_level":
        errors.append(f"{prefix}: candidate_pool_eligible requires coverage_level=full_major_level")
    if eligible and status != "full_extracted":
        errors.append(f"{prefix}: candidate_pool_eligible requires status=full_extracted")

    if data_type == "enrollment_plan_summary" and coverage != "school_level_summary":
        errors.append(f"{prefix}: enrollment_plan_summary must use school_level_summary coverage")
    if data_type == "one_score_one_rank" and coverage not in {"sample_rows", "full_score_table"}:
        errors.append(f"{prefix}: one_score_one_rank must use sample_rows or full_score_table coverage")
    if data_type == "plan_correction" and coverage not in {"sample_rows", "full_correction_notice", "source_only"}:
        errors.append(f"{prefix}: plan_correction coverage is inconsistent")
    if data_type == "historical_rank" and status == "full_extracted" and coverage == "sample_rows":
        errors.append(f"{prefix}: full_extracted cannot use sample_rows coverage")

    extraction_file = source.get("extraction_file")
    if status in {"sampled", "full_extracted"} and not extraction_file:
        errors.append(f"{prefix}: extracted sources must include extraction_file")
    if extraction_file:
        extraction_path = root / str(extraction_file)
        if not extraction_path.exists():
            errors.append(f"{prefix}: extraction_file not found: {extraction_file}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_yaml", type=Path)
    args = parser.parse_args()

    path = args.source_yaml.resolve()
    root = path.parents[1]
    data = load_yaml(path)
    errors: list[str] = []
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{path}: sources must be a non-empty list")
    else:
        seen_ids: set[str] = set()
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                errors.append(f"sources[{index}]: must be a mapping")
                continue
            source_id = str(source.get("id") or "")
            if source_id in seen_ids:
                errors.append(f"sources[{index}]: duplicate id {source_id}")
            seen_ids.add(source_id)
            validate_source(source, index, errors, root)

    if errors:
        print("validate_official_data_sources: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"validate_official_data_sources: ok ({len(sources)} sources)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
