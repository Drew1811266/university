#!/usr/bin/env python3
"""Normalize gaokao one-score-one-rank CSV rows into JSON records."""

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
    "subject_category",
    "score_label",
    "score_min",
    "segment_count",
    "cumulative_count",
    "source_title",
    "source_url",
    "field_evidence_level",
}

OPTIONAL_FIELDS = {
    "score_max",
    "source_published_at",
    "retrieved_at",
    "notes",
}

ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
FIELD_EVIDENCE_LEVELS = {
    "official_current",
    "official_historical",
    "official_entry_only",
    "user_supplied",
    "third_party_lead",
    "missing",
}


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
    item["province"] = (row.get("province") or "").strip()
    item["year"] = parse_int(row.get("year"), "year", row_number, errors)
    item["subject_category"] = (row.get("subject_category") or "").strip()
    item["score_label"] = (row.get("score_label") or "").strip()
    item["score_min"] = parse_int(row.get("score_min"), "score_min", row_number, errors)
    item["score_max"] = parse_int(row.get("score_max"), "score_max", row_number, errors, allow_blank=True)
    item["segment_count"] = parse_int(row.get("segment_count"), "segment_count", row_number, errors)
    item["cumulative_count"] = parse_int(row.get("cumulative_count"), "cumulative_count", row_number, errors)
    item["source_title"] = (row.get("source_title") or "").strip()
    item["source_url"] = (row.get("source_url") or "").strip()
    item["source_published_at"] = blank_to_none(row.get("source_published_at"))
    item["retrieved_at"] = blank_to_none(row.get("retrieved_at")) or date.today().isoformat()

    evidence = (row.get("field_evidence_level") or "").strip()
    if evidence not in FIELD_EVIDENCE_LEVELS:
        errors.append(f"row {row_number}: invalid field_evidence_level {evidence}")
    item["field_evidence_level"] = evidence

    notes = blank_to_none(row.get("notes"))
    item["notes"] = [part.strip() for part in notes.split(";") if part.strip()] if notes else []

    if item["year"] != 2026 and item["field_evidence_level"] == "official_current":
        errors.append(f"row {row_number}: official_current score segments must use year 2026")
    if item["score_max"] is not None and item["score_min"] is not None and item["score_max"] < item["score_min"]:
        errors.append(f"row {row_number}: score_max must be greater than or equal to score_min")
    if item["source_url"] and not item["source_url"].startswith(("http://", "https://")):
        errors.append(f"row {row_number}: source_url must be http(s)")

    return item


def validate_monotonic(items: list[dict[str, Any]], errors: list[str]) -> None:
    previous: dict[tuple[str, int, str], int] = {}
    for index, item in enumerate(items, start=2):
        key = (item.get("province"), item.get("year"), item.get("subject_category"))
        current = item.get("cumulative_count")
        segment = item.get("segment_count")
        if not isinstance(current, int) or not isinstance(segment, int):
            continue
        last = previous.get(key)
        if last is not None and current < last:
            errors.append(f"row {index}: cumulative_count must be non-decreasing within province/year/category")
        previous[key] = current


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

    validate_monotonic(items, errors)

    if errors:
        print("normalize_score_segment_csv: failed", file=sys.stderr)
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
