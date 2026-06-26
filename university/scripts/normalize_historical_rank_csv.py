#!/usr/bin/env python3
"""Normalize historical rank CSV into historical-rank-item JSON records."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "province",
    "year",
    "batch",
    "subject_category",
    "institution_code",
    "institution_name",
    "minimum_rank",
    "source_file",
    "comparability_status",
}

OPTIONAL_FIELDS = {
    "major_group_code",
    "major_code",
    "major_name",
    "campus",
    "project_type",
    "comparison_unit_key",
    "continuity_status",
    "change_flags",
    "minimum_score",
    "plan_count",
    "source_url",
    "field_evidence_level",
    "comparability_notes",
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
EVIDENCE_LEVELS = {"official_current", "official_historical", "official_entry_only", "user_supplied", "third_party_lead", "missing"}
COMPARABILITY_STATUSES = {"comparable", "partially_comparable", "not_comparable", "unknown"}
CONTINUITY_STATUSES = {"stable", "changed", "new", "merged", "split", "unknown"}
CHANGE_FLAGS = {"major_group_changed", "major_changed", "campus_changed", "project_type_changed", "plan_count_changed", "first_year", "unknown_change"}


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def parse_int(value: str | None, field: str, row_number: int, errors: list[str], allow_blank: bool = False) -> int | None:
    value = blank_to_none(value)
    if value is None:
        if allow_blank:
            return None
        errors.append(f"row {row_number}: {field} is required")
        return None
    try:
        return int(value)
    except ValueError:
        errors.append(f"row {row_number}: {field} must be an integer")
        return None


def normalize_row(row: dict[str, str], row_number: int, errors: list[str]) -> dict[str, Any]:
    for field in REQUIRED_FIELDS:
        if not blank_to_none(row.get(field)):
            errors.append(f"row {row_number}: missing required field {field}")

    item: dict[str, Any] = {}
    item["year"] = parse_int(row.get("year"), "year", row_number, errors)
    item["minimum_rank"] = parse_int(row.get("minimum_rank"), "minimum_rank", row_number, errors)
    item["minimum_score"] = parse_int(row.get("minimum_score"), "minimum_score", row_number, errors, allow_blank=True)
    item["plan_count"] = parse_int(row.get("plan_count"), "plan_count", row_number, errors, allow_blank=True)

    for field in sorted(REQUIRED_FIELDS - {"year", "minimum_rank"}):
        item[field] = (row.get(field) or "").strip()
    for field in sorted(OPTIONAL_FIELDS - {"minimum_score", "plan_count", "comparability_notes", "change_flags"}):
        item[field] = blank_to_none(row.get(field))

    evidence = item.get("field_evidence_level") or "official_historical"
    if evidence not in EVIDENCE_LEVELS:
        errors.append(f"row {row_number}: invalid field_evidence_level {evidence}")
    item["field_evidence_level"] = evidence

    status = item.get("comparability_status")
    if status not in COMPARABILITY_STATUSES:
        errors.append(f"row {row_number}: invalid comparability_status {status}")

    continuity = item.get("continuity_status") or "unknown"
    if continuity not in CONTINUITY_STATUSES:
        errors.append(f"row {row_number}: invalid continuity_status {continuity}")
    item["continuity_status"] = continuity

    flags_text = blank_to_none(row.get("change_flags"))
    flags = [part.strip() for part in flags_text.split(";") if part.strip()] if flags_text else []
    unknown_flags = sorted(set(flags) - CHANGE_FLAGS)
    if unknown_flags:
        errors.append(f"row {row_number}: invalid change_flags {', '.join(unknown_flags)}")
    item["change_flags"] = flags

    if item.get("comparability_status") == "comparable" and continuity != "stable":
        errors.append(f"row {row_number}: comparable historical rows must set continuity_status=stable")

    notes = blank_to_none(row.get("comparability_notes"))
    item["comparability_notes"] = [part.strip() for part in notes.split(";") if part.strip()] if notes else []

    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    with args.csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_FIELDS - headers
        unknown = headers - ALL_FIELDS
        errors: list[str] = []
        if missing:
            errors.append(f"missing required columns: {', '.join(sorted(missing))}")
        if unknown:
            errors.append(f"unknown columns: {', '.join(sorted(unknown))}")
        items = [normalize_row(row, row_number, errors) for row_number, row in enumerate(reader, start=2)]

    if errors:
        print("normalize_historical_rank_csv: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    output = json.dumps(items, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
