#!/usr/bin/env python3
"""Check profile-library wording and source-status hygiene."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


STATUS_RE = re.compile(r"\| profile_source_status \| ([ABC])：([^|]+)\|")
OUTDATED_TIME_PHRASE = "2025 年及以后官方来源"


def validate_profile_file(path: Path, warnings: list[str], errors: list[str], counts: dict[str, int]) -> None:
    text = path.read_text(encoding="utf-8")
    if "profile_source_status 等级" not in text and path.name != "university-profiles-international.md":
        errors.append(f"{path}: missing profile_source_status level explanation")

    if OUTDATED_TIME_PHRASE in text:
        warnings.append(f"{path}: contains old generic time-sensitive phrase '{OUTDATED_TIME_PHRASE}'")

    statuses = list(STATUS_RE.finditer(text))
    if not statuses and path.name != "university-profiles-international.md":
        errors.append(f"{path}: no profile_source_status rows found")

    for match in statuses:
        level = match.group(1)
        description = match.group(2).strip()
        counts[level] = counts.get(level, 0) + 1
        if level == "B":
            if "精确简介页待补充" not in description:
                errors.append(f"{path}:{line_number(text, match.start())}: B status must include 精确简介页待补充")
            if "直接核验" in description or "已核验" in description:
                errors.append(f"{path}:{line_number(text, match.start())}: B status must not imply precise verification")
        if level == "C" and not any(phrase in description for phrase in ("需复核", "回官网", "简介页不稳定")):
            errors.append(f"{path}:{line_number(text, match.start())}: C status must warn that source needs recheck")


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    references = root / "references"
    files = sorted(references.glob("university-profiles-*.md"))
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {"A": 0, "B": 0, "C": 0}

    if not files:
        errors.append(f"{references}: no university profile files found")
    for path in files:
        validate_profile_file(path, warnings, errors, counts)

    if warnings:
        print("validate_profile_library: warnings", file=sys.stderr)
        for warning in warnings:
            print(f"- {warning}", file=sys.stderr)

    if errors or (args.strict and warnings):
        print("validate_profile_library: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        if args.strict and warnings:
            print("- strict mode treats warnings as failures", file=sys.stderr)
        return 1

    print(
        "validate_profile_library: ok "
        f"(files={len(files)}, A={counts.get('A', 0)}, B={counts.get('B', 0)}, C={counts.get('C', 0)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
