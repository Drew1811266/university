#!/usr/bin/env python3
"""Create and compare local source-file digests for official data monitoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


STATUSES = ("new", "unchanged", "changed", "missing")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path, root: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(resolved)


def iter_path_inputs(paths: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in paths:
        if path.is_dir():
            for child in sorted(p for p in path.rglob("*") if p.is_file()):
                if "__pycache__" not in child.parts:
                    entries.append({"path": child})
        else:
            entries.append({"path": path})
    return entries


def iter_official_source_files(root: Path, official_sources: Path) -> list[dict[str, Any]]:
    if yaml is None:
        raise RuntimeError("PyYAML is required when reading gaokao-cn-official-data-sources.yaml")
    data = yaml.safe_load(official_sources.read_text(encoding="utf-8"))
    sources = data.get("sources") if isinstance(data, dict) else None
    if not isinstance(sources, list):
        raise RuntimeError(f"{official_sources}: expected top-level sources list")

    entries: list[dict[str, Any]] = []
    for source in sources:
        if not isinstance(source, dict):
            continue
        extraction_file = source.get("extraction_file")
        if not extraction_file:
            continue
        entries.append(
            {
                "path": root / str(extraction_file),
                "source_id": source.get("id"),
                "source_title": source.get("source_title"),
                "source_url": source.get("source_url"),
                "data_type": source.get("data_type"),
                "coverage_level": source.get("coverage_level"),
            }
        )
    return entries


def load_manifest(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise RuntimeError(f"{path}: expected JSON object with items list")
    manifest: dict[str, dict[str, Any]] = {}
    for item in items:
        if isinstance(item, dict) and item.get("path"):
            manifest[str(item["path"])] = item
    return manifest


def snapshot_entry(entry: dict[str, Any], root: Path, previous: dict[str, dict[str, Any]]) -> dict[str, Any]:
    path = Path(entry["path"])
    name = display_path(path, root)
    result: dict[str, Any] = {
        "path": name,
        "exists": path.exists(),
        "size_bytes": None,
        "sha256": None,
    }
    for key in ("source_id", "source_title", "source_url", "data_type", "coverage_level"):
        if entry.get(key) is not None:
            result[key] = entry[key]

    old = previous.get(name)
    if not path.exists():
        result["status"] = "missing"
        return result

    stat = path.stat()
    result["size_bytes"] = stat.st_size
    result["sha256"] = sha256_file(path)

    if old is None:
        result["status"] = "new"
    elif old.get("sha256") == result["sha256"] and old.get("size_bytes") == result["size_bytes"]:
        result["status"] = "unchanged"
    else:
        result["status"] = "changed"
        result["previous_sha256"] = old.get("sha256")
        result["previous_size_bytes"] = old.get("size_bytes")
    return result


def build_report(entries: list[dict[str, Any]], root: Path, previous: dict[str, dict[str, Any]]) -> dict[str, Any]:
    items = [snapshot_entry(entry, root, previous) for entry in entries]
    summary = {status: 0 for status in STATUSES}
    for item in items:
        summary[str(item["status"])] += 1
    return {
        "generated_at": date.today().isoformat(),
        "summary": summary,
        "items": items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, help="files or directories to snapshot; defaults to extraction_file entries")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--official-sources", type=Path, default=None)
    parser.add_argument("--manifest", type=Path, help="previous snapshot JSON to compare against")
    parser.add_argument("--output", type=Path, help="write snapshot JSON here; defaults to stdout")
    parser.add_argument("--fail-on-change", action="store_true", help="exit non-zero when files changed or are missing")
    args = parser.parse_args()

    root = args.root.resolve()
    official_sources = args.official_sources or root / "references" / "gaokao-cn-official-data-sources.yaml"

    try:
        entries = iter_path_inputs(args.paths) if args.paths else iter_official_source_files(root, official_sources)
        previous = load_manifest(args.manifest)
        report = build_report(entries, root, previous)
        text = json.dumps(report, ensure_ascii=False, indent=2)
        if args.output:
            args.output.write_text(text + "\n", encoding="utf-8")
        else:
            print(text)
        if args.fail_on_change and (report["summary"]["changed"] or report["summary"]["missing"]):
            return 2
    except Exception as exc:  # noqa: BLE001
        print(f"snapshot_sources: failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
