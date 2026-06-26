#!/usr/bin/env python3
"""Resolve corrected enrollment-plan items into an active-plan view."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ACTIVE_STATUSES = {"active", "added", "corrected"}
INACTIVE_STATUSES = {"cancelled", "replaced"}


def item_id(item: dict[str, Any]) -> str:
    parts = [
        item.get("province"),
        item.get("batch"),
        item.get("subject_category"),
        item.get("institution_code"),
        item.get("major_group_code") or "nogroup",
        item.get("major_code") or item.get("major_name"),
    ]
    return "|".join(str(part) for part in parts if part is not None)


def load_items(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("expected a JSON array")
    if not all(isinstance(item, dict) for item in data):
        raise ValueError("all JSON array items must be objects")
    return data


def resolve(items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]], list[str]]:
    active: list[dict[str, Any]] = []
    report: dict[str, list[str]] = {
        "active": [],
        "added": [],
        "corrected": [],
        "cancelled": [],
        "replaced": [],
        "unknown": [],
    }
    errors: list[str] = []
    seen: dict[str, str] = {}

    for item in items:
        status = item.get("correction_status", "unknown")
        ident = item_id(item)
        report.setdefault(status, []).append(ident)
        if ident in seen and status in ACTIVE_STATUSES:
            errors.append(f"duplicate active candidate item: {ident}")
        if status in ACTIVE_STATUSES:
            active.append(item)
            seen[ident] = status
        elif status == "replaced" and not item.get("replaced_by"):
            errors.append(f"replaced item lacks replaced_by: {ident}")
        elif status == "unknown":
            errors.append(f"unknown correction status cannot enter final candidate pool: {ident}")
        elif status not in INACTIVE_STATUSES:
            errors.append(f"invalid correction_status {status}: {ident}")

    replaced_targets = {str(item.get("replaced_by")) for item in items if item.get("correction_status") == "replaced" and item.get("replaced_by")}
    active_ids = {item_id(item) for item in active}
    for target in sorted(replaced_targets):
        if target not in active_ids:
            errors.append(f"replaced_by target not present as active item: {target}")

    return active, report, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("json_path", type=Path)
    parser.add_argument("--output", type=Path, help="write active JSON to file")
    parser.add_argument("--report", action="store_true", help="print status report to stderr")
    parser.add_argument("--pretty", action="store_true", help="pretty-print JSON")
    args = parser.parse_args()

    try:
        items = load_items(args.json_path)
        active, report, errors = resolve(items)
    except Exception as exc:  # noqa: BLE001
        print(f"resolve_plan_corrections: failed: {exc}", file=sys.stderr)
        return 1

    if args.report:
        for status in sorted(report):
            print(f"{status}: {len(report[status])}", file=sys.stderr)

    if errors:
        print("resolve_plan_corrections: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    output = json.dumps(active, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
