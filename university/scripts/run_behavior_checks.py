#!/usr/bin/env python3
"""Validate gaokao-cn behavior cases and simple output assertions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


REQUIRED_CASE_FIELDS = {"id", "title", "input", "required_behavior", "checks"}
CHECK_LIST_FIELDS = {"must_contain", "must_contain_any", "must_not_contain", "must_match", "must_not_match"}


def load_cases(root: Path) -> list[dict[str, Any]]:
    path = root / "references" / "gaokao-cn-behavior-cases.yaml"
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError(f"{path}: expected top-level cases list")
    return data["cases"]


def validate_cases(cases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            errors.append(f"case {index}: expected mapping")
            continue
        missing = REQUIRED_CASE_FIELDS - case.keys()
        if missing:
            errors.append(f"case {index}: missing fields: {', '.join(sorted(missing))}")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            errors.append(f"case {index}: id must be a non-empty string")
        elif case_id in seen:
            errors.append(f"case {case_id}: duplicate id")
        else:
            seen.add(case_id)
        if not isinstance(case.get("required_behavior"), list) or not case.get("required_behavior"):
            errors.append(f"case {case_id or index}: required_behavior must be a non-empty list")
        checks = case.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"case {case_id or index}: checks must be a mapping")
            continue
        unknown = set(checks) - CHECK_LIST_FIELDS
        if unknown:
            errors.append(f"case {case_id or index}: unknown check fields: {', '.join(sorted(unknown))}")
        if not checks:
            errors.append(f"case {case_id or index}: checks must not be empty")
        for field, value in checks.items():
            if field not in CHECK_LIST_FIELDS:
                continue
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                errors.append(f"case {case_id or index}: {field} must be a non-empty list of strings")
    return errors


def check_output(case: dict[str, Any], output: str) -> list[str]:
    errors: list[str] = []
    checks = case.get("checks", {})
    case_id = case.get("id", "<unknown>")

    for phrase in checks.get("must_contain", []):
        if phrase not in output:
            errors.append(f"{case_id}: output missing required phrase: {phrase}")

    any_phrases = checks.get("must_contain_any", [])
    if any_phrases and not any(phrase in output for phrase in any_phrases):
        errors.append(f"{case_id}: output must contain at least one of: {', '.join(any_phrases)}")

    for phrase in checks.get("must_not_contain", []):
        if phrase in output:
            errors.append(f"{case_id}: output contains forbidden phrase: {phrase}")

    for pattern in checks.get("must_match", []):
        if not re.search(pattern, output):
            errors.append(f"{case_id}: output does not match required regex: {pattern}")

    for pattern in checks.get("must_not_match", []):
        if re.search(pattern, output):
            errors.append(f"{case_id}: output matches forbidden regex: {pattern}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--validate", action="store_true", help="validate case file structure")
    parser.add_argument("--list", action="store_true", help="list behavior case IDs")
    parser.add_argument("--case-id", help="case ID to check against an output file")
    parser.add_argument("--output", type=Path, help="sample output text file for --case-id")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        cases = load_cases(root)
    except Exception as exc:  # noqa: BLE001
        print(f"run_behavior_checks: failed to load cases: {exc}", file=sys.stderr)
        return 1

    errors = validate_cases(cases)
    if args.list:
        for case in cases:
            print(case["id"])

    if args.case_id:
        if not args.output:
            errors.append("--output is required with --case-id")
        else:
            selected = next((case for case in cases if case.get("id") == args.case_id), None)
            if selected is None:
                errors.append(f"unknown case id: {args.case_id}")
            else:
                output = args.output.read_text(encoding="utf-8")
                errors.extend(check_output(selected, output))

    if errors:
        print("run_behavior_checks: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    if args.case_id:
        print(f"run_behavior_checks: ok ({args.case_id})")
    elif args.list:
        print(f"run_behavior_checks: ok ({len(cases)} cases listed)")
    else:
        print(f"run_behavior_checks: ok ({len(cases)} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
