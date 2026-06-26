#!/usr/bin/env python3
"""Normalize a CSV enrollment plan into enrollment-plan-item JSON records."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = {
    "province",
    "year",
    "batch",
    "subject_category",
    "institution_code",
    "institution_name",
    "major_name",
    "plan_count",
    "source_file",
}

OPTIONAL_FIELDS = {
    "major_group_code",
    "major_code",
    "selected_subject_requirements",
    "tuition",
    "campus",
    "project_type",
    "remarks",
    "source_title",
    "source_type",
    "source_locator",
    "source_published_at",
    "source_url",
    "retrieved_at",
    "field_evidence_level",
    "coverage_level",
    "candidate_pool_eligible",
    "is_corrected",
    "correction_status",
    "replaces",
    "replaced_by",
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
CORRECTION_STATUSES = {"active", "replaced", "cancelled", "added", "corrected", "unknown"}
SOURCE_TYPES = {"provincial_enrollment_plan", "provincial_plan_correction", "official_auxiliary_system", "official_publication", "user_upload"}
FIELD_EVIDENCE_LEVELS = {"official_current", "official_entry_only", "user_supplied", "third_party_lead", "missing"}
COVERAGE_LEVELS = {"full_major_level", "sample_rows", "school_level_summary", "source_only"}


def blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def parse_bool(value: str | None) -> bool:
    value = (value or "").strip().lower()
    return value in {"1", "true", "yes", "y", "是"}


def make_record_id(item: dict[str, Any]) -> str:
    parts = [
        item.get("province"),
        item.get("year"),
        item.get("batch"),
        item.get("subject_category"),
        item.get("institution_code"),
        item.get("major_group_code") or "nogroup",
        item.get("major_code") or item.get("major_name"),
    ]
    return "|".join(str(part).replace("|", "/") for part in parts if part is not None)


def normalize_row(row: dict[str, str], index: int, errors: list[str]) -> dict[str, Any]:
    item: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        if not blank_to_none(row.get(field)):
            errors.append(f"row {index}: missing required field {field}")

    try:
        item["year"] = int(row.get("year", ""))
    except ValueError:
        errors.append(f"row {index}: year must be integer 2026")
        item["year"] = row.get("year")
    if item.get("year") != 2026:
        errors.append(f"row {index}: year must be 2026")

    try:
        item["plan_count"] = int(row.get("plan_count", ""))
    except ValueError:
        errors.append(f"row {index}: plan_count must be an integer")
        item["plan_count"] = row.get("plan_count")

    for field in sorted(REQUIRED_FIELDS - {"year", "plan_count"}):
        item[field] = (row.get(field) or "").strip()

    for field in sorted(OPTIONAL_FIELDS - {"selected_subject_requirements", "is_corrected", "correction_status", "candidate_pool_eligible"}):
        item[field] = blank_to_none(row.get(field))

    subjects = blank_to_none(row.get("selected_subject_requirements"))
    item["selected_subject_requirements"] = [part.strip() for part in subjects.split(";") if part.strip()] if subjects else []
    item["is_corrected"] = parse_bool(row.get("is_corrected"))
    item["candidate_pool_eligible"] = parse_bool(row.get("candidate_pool_eligible")) if row.get("candidate_pool_eligible") is not None else True

    status = blank_to_none(row.get("correction_status")) or "unknown"
    if status not in CORRECTION_STATUSES:
        errors.append(f"row {index}: invalid correction_status {status}")
    item["correction_status"] = status

    item["source_title"] = item.get("source_title") or item.get("source_file")
    item["source_type"] = item.get("source_type") or ("provincial_plan_correction" if item["is_corrected"] else "provincial_enrollment_plan")
    if item["source_type"] not in SOURCE_TYPES:
        errors.append(f"row {index}: invalid source_type {item['source_type']}")
    item["retrieved_at"] = item.get("retrieved_at") or date.today().isoformat()
    item["field_evidence_level"] = item.get("field_evidence_level") or ("official_current" if item.get("source_url") else "missing")
    if item["field_evidence_level"] not in FIELD_EVIDENCE_LEVELS:
        errors.append(f"row {index}: invalid field_evidence_level {item['field_evidence_level']}")
    item["coverage_level"] = item.get("coverage_level") or "full_major_level"
    if item["coverage_level"] not in COVERAGE_LEVELS:
        errors.append(f"row {index}: invalid coverage_level {item['coverage_level']}")
    if item["candidate_pool_eligible"] and item["coverage_level"] != "full_major_level":
        errors.append(f"row {index}: candidate_pool_eligible requires coverage_level=full_major_level")
    item["evidence_id"] = f"enrollment_plan:{make_record_id(item)}"

    if status == "replaced" and not item.get("replaced_by"):
        errors.append(f"row {index}: replaced item must include replaced_by")
    if status in {"added", "corrected"} and item["is_corrected"] is False:
        errors.append(f"row {index}: {status} item should set is_corrected true")

    return item


def evidence_rows(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        rows.append(
            {
                "field": f"enrollment_plan_item:{make_record_id(item)}",
                "source_title": item.get("source_title") or item.get("source_file") or "待核验",
                "source_url": item.get("source_url"),
                "source_type": item.get("source_type"),
                "applicable_year": item.get("year"),
                "applicable_audience": f"{item.get('province')} {item.get('batch')} {item.get('subject_category')}",
                "published_at": item.get("source_published_at"),
                "retrieved_at": item.get("retrieved_at"),
                "field_evidence_level": item.get("field_evidence_level"),
                "coverage_level": item.get("coverage_level"),
                "candidate_pool_eligible": item.get("candidate_pool_eligible"),
                "notes": item.get("source_locator") or item.get("remarks"),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path, help="write JSON to file instead of stdout")
    parser.add_argument("--evidence-output", type=Path, help="write field-evidence ledger JSON")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
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
        items = [normalize_row(row, index, errors) for index, row in enumerate(reader, start=2)]

    if errors:
        print("normalize_enrollment_plan_csv: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    output = json.dumps(items, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    if args.evidence_output:
        evidence = json.dumps(evidence_rows(items), ensure_ascii=False, indent=2 if args.pretty else None)
        args.evidence_output.write_text(evidence + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
