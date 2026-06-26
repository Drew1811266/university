#!/usr/bin/env python3
"""Validate gaokao-cn structured data without external schema dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required: python3 -m pip install pyyaml") from exc


REQUIRED_PROVINCE_KEYS = {
    "province",
    "year",
    "exam_type",
    "cycle_status",
    "last_checked_at",
    "sources",
}

REQUIRED_GATES = {
    "result_release",
    "control_lines",
    "one_score_one_rank",
    "volunteer_filling",
    "enrollment_plan",
    "plan_corrections",
}

SCHEMA_FILES = {
    "candidate-profile.schema.json",
    "province-cycle.schema.json",
    "enrollment-plan-item.schema.json",
    "historical-rank-item.schema.json",
    "official-data-source.schema.json",
    "score-segment-item.schema.json",
    "risk-assessment.schema.json",
    "evidence.schema.json",
    "submission-precheck-package.schema.json",
}

MAINTENANCE_FILES = {
    "resource-map.md",
    "development-roadmap.md",
    "gaokao-cn-candidate-pool.md",
    "gaokao-cn-risk-method.md",
    "gaokao-cn-submission-gates.md",
    "gaokao-cn-submission-precheck-package.md",
    "gaokao-cn-submission-evidence-sample.json",
    "gaokao-cn-enrollment-plan-import.md",
    "gaokao-cn-plan-corrections.md",
    "gaokao-cn-province-pack-template.yaml",
    "gaokao-cn-province-pack-seeds.csv",
    "gaokao-cn-enrollment-plan-beijing-2026-summary-official-sample.csv",
    "gaokao-cn-enrollment-plan-sample.csv",
    "gaokao-cn-enrollment-plan-sichuan-2026-corrections-official-sample.csv",
    "gaokao-cn-official-data-sources.yaml",
    "gaokao-cn-candidate-profile-sample.json",
    "gaokao-cn-historical-rank-sample.csv",
    "gaokao-cn-historical-rank-guangdong-2025-official-sample.csv",
    "gaokao-cn-score-segment-beijing-2026-official-sample.csv",
}

SCRIPT_FILES = {
    "validate_data.py",
    "check_links.py",
    "detect_source_changes.py",
    "snapshot_sources.py",
    "extract_html_table.py",
    "extract_pdf_text.py",
    "extract_xlsx_sheet.py",
    "province_readiness.py",
    "build_markdown.py",
    "build_gaokao_report.py",
    "build_overseas_plan.py",
    "create_province_pack.py",
    "create_all_province_packs.py",
    "normalize_enrollment_plan_csv.py",
    "normalize_score_segment_csv.py",
    "resolve_plan_corrections.py",
    "build_candidate_pool.py",
    "normalize_historical_rank_csv.py",
    "build_risk_assessment.py",
    "check_submission_gates.py",
    "validate_submission_precheck_package.py",
    "run_self_test.py",
    "run_behavior_checks.py",
    "validate_profile_library.py",
    "validate_official_data_sources.py",
    "profile_maintenance_queue.py",
}

SEED_COLUMNS = {"province", "slug", "authority_title", "authority_url"}

CHECK_FIELDS = {
    "must_contain",
    "must_contain_any",
    "must_not_contain",
    "must_match",
    "must_not_match",
}


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def validate_schema_files(root: Path, errors: list[str]) -> None:
    schema_dir = root / "references"
    found = {p.name for p in schema_dir.glob("*.json")}
    missing = sorted(SCHEMA_FILES - found)
    if missing:
        errors.append(f"missing schema files: {', '.join(missing)}")

    for filename in sorted(SCHEMA_FILES):
        path = schema_dir / filename
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: invalid JSON: {exc}")
            continue
        for key in ("$schema", "title", "type"):
            if key not in data:
                errors.append(f"{path}: missing {key}")


def validate_maintenance_files(root: Path, errors: list[str]) -> None:
    references = root / "references"
    scripts = root / "scripts"
    for filename in sorted(MAINTENANCE_FILES):
        path = references / filename
        if not path.exists():
            errors.append(f"{path}: missing maintenance reference")
        elif path.stat().st_size == 0:
            errors.append(f"{path}: maintenance reference is empty")

    for filename in sorted(SCRIPT_FILES):
        path = scripts / filename
        if not path.exists():
            errors.append(f"{path}: missing expected script")


def load_province_seed_rows(root: Path, errors: list[str]) -> list[dict[str, str]]:
    path = root / "references" / "gaokao-cn-province-pack-seeds.csv"
    if not path.exists():
        errors.append(f"{path}: missing province pack seeds")
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = SEED_COLUMNS - columns
        if missing:
            errors.append(f"{path}: missing columns: {', '.join(sorted(missing))}")
            return []
        rows = list(reader)
    return rows


def validate_province_seeds(root: Path, errors: list[str]) -> list[dict[str, str]]:
    path = root / "references" / "gaokao-cn-province-pack-seeds.csv"
    rows = load_province_seed_rows(root, errors)
    if not rows:
        return []
    if len(rows) != 31:
        errors.append(f"{path}: expected 31 province rows, found {len(rows)}")
    seen_slugs: set[str] = set()
    seen_provinces: set[str] = set()
    for index, row in enumerate(rows, start=2):
        province = (row.get("province") or "").strip()
        slug = (row.get("slug") or "").strip()
        url = (row.get("authority_url") or "").strip()
        if not province:
            errors.append(f"{path}:{index}: missing province")
        if not slug:
            errors.append(f"{path}:{index}: missing slug")
        if slug in seen_slugs:
            errors.append(f"{path}:{index}: duplicate slug {slug}")
        seen_slugs.add(slug)
        if province in seen_provinces:
            errors.append(f"{path}:{index}: duplicate province {province}")
        seen_provinces.add(province)
        if not url.startswith(("http://", "https://")):
            errors.append(f"{path}:{index}: authority_url must be http(s)")
    return rows


def validate_province_pack_coverage(root: Path, seed_rows: list[dict[str, str]], packs: list[Path], errors: list[str]) -> None:
    if not seed_rows:
        return
    expected = {row["slug"].strip() for row in seed_rows}
    found = {
        path.name.removeprefix("gaokao-cn-province-").removesuffix("-2026.yaml")
        for path in packs
    }
    missing = sorted(expected - found)
    extra = sorted(found - expected)
    if missing:
        errors.append(f"missing province packs for seed slugs: {', '.join(missing)}")
    if extra:
        errors.append(f"province packs without seed rows: {', '.join(extra)}")


def validate_province_pack(path: Path, errors: list[str]) -> None:
    data = load_yaml(path)
    if not isinstance(data, dict):
        errors.append(f"{path}: expected mapping")
        return

    missing = REQUIRED_PROVINCE_KEYS - data.keys()
    if missing:
        errors.append(f"{path}: missing required keys: {', '.join(sorted(missing))}")

    if data.get("year") != 2026:
        errors.append(f"{path}: year must be 2026")

    for key in REQUIRED_GATES:
        value = data.get(key)
        if not isinstance(value, dict):
            errors.append(f"{path}: {key} must be a mapping")
            continue
        if "status" not in value:
            errors.append(f"{path}: {key}.status is required")
        if value.get("status") in {"published", "corrected"} and not value.get("source_url"):
            errors.append(f"{path}: {key} is {value.get('status')} but lacks source_url")

    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append(f"{path}: sources must be a non-empty list")
    else:
        seen_urls: set[str] = set()
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                errors.append(f"{path}: sources[{index}] must be a mapping")
                continue
            for field in ("title", "url", "source_type", "status"):
                if not source.get(field):
                    errors.append(f"{path}: sources[{index}] missing {field}")
            url = source.get("url")
            if url in seen_urls:
                errors.append(f"{path}: duplicate source url {url}")
            if url:
                seen_urls.add(url)

    if data.get("cycle_status") == "published":
        unmet = [
            key
            for key in REQUIRED_GATES
            if data.get(key, {}).get("status") not in {"published", "corrected"}
        ]
        if unmet:
            errors.append(f"{path}: cycle_status published but gates are not published: {', '.join(unmet)}")


def validate_tests(root: Path, errors: list[str]) -> None:
    path = root / "references" / "gaokao-cn-behavior-cases.yaml"
    if not path.exists():
        errors.append(f"{path}: missing behavior cases")
        return
    data = load_yaml(path)
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        errors.append(f"{path}: expected top-level cases list")
        return
    case_ids = [case.get("id") for case in data["cases"] if isinstance(case, dict)]
    if len(case_ids) != len(set(case_ids)):
        errors.append(f"{path}: duplicate case id")
    if len(case_ids) < 10:
        errors.append(f"{path}: expected at least 10 behavior cases")
    for case in data["cases"]:
        if not isinstance(case, dict):
            continue
        checks = case.get("checks")
        case_id = case.get("id", "<unknown>")
        if not isinstance(checks, dict) or not checks:
            errors.append(f"{path}: case {case_id} missing non-empty checks")
            continue
        unknown = sorted(set(checks) - CHECK_FIELDS)
        if unknown:
            errors.append(f"{path}: case {case_id} unknown check fields: {', '.join(unknown)}")
        for field, value in checks.items():
            if field not in CHECK_FIELDS:
                continue
            if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
                errors.append(f"{path}: case {case_id} {field} must be a non-empty list of strings")

    forward_path = root / "references" / "gaokao-cn-forward-scenarios.yaml"
    if not forward_path.exists():
        errors.append(f"{forward_path}: missing forward scenarios")
        return
    forward = load_yaml(forward_path)
    if not isinstance(forward, dict) or not isinstance(forward.get("scenarios"), list):
        errors.append(f"{forward_path}: expected top-level scenarios list")
        return
    if len(forward["scenarios"]) < 3:
        errors.append(f"{forward_path}: expected at least 3 forward scenarios")
    for scenario in forward["scenarios"]:
        if not isinstance(scenario, dict):
            errors.append(f"{forward_path}: scenario must be a mapping")
            continue
        for field in ("id", "title", "input_summary", "expected"):
            if field not in scenario:
                errors.append(f"{forward_path}: scenario missing {field}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = Path(args.root).resolve()

    errors: list[str] = []
    validate_maintenance_files(root, errors)
    seed_rows = validate_province_seeds(root, errors)
    validate_schema_files(root, errors)

    province_dir = root / "references"
    packs = sorted(province_dir.glob("gaokao-cn-province-*-2026.yaml"))
    if not packs:
        errors.append(f"{province_dir}: no province packs found")
    validate_province_pack_coverage(root, seed_rows, packs, errors)
    for path in packs:
        validate_province_pack(path, errors)

    validate_tests(root, errors)

    if errors:
        print("validate_data: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"validate_data: ok ({len(packs)} province packs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
