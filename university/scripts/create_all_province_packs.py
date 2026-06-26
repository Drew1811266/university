#!/usr/bin/env python3
"""Create draft province packs from gaokao-cn-province-pack-seeds.csv."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path


REQUIRED_COLUMNS = {"province", "slug", "authority_title", "authority_url"}
SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def render_template(template: str, row: dict[str, str], checked_at: str) -> str:
    values = {
        "province": row["province"],
        "last_checked_at": checked_at,
        "authority_title": row["authority_title"],
        "authority_url": row["authority_url"],
    }
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--checked-at", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="show actions without writing")
    parser.add_argument("--overwrite", action="store_true", help="overwrite existing draft packs")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    seeds_path = root / "references" / "gaokao-cn-province-pack-seeds.csv"
    template_path = root / "references" / "gaokao-cn-province-pack-template.yaml"
    template = template_path.read_text(encoding="utf-8")

    created = 0
    skipped = 0
    errors: list[str] = []
    with seeds_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - columns
        if missing:
            print(f"{seeds_path}: missing columns {', '.join(sorted(missing))}", file=sys.stderr)
            return 1
        for row in reader:
            slug = row.get("slug", "").strip()
            if not SLUG_RE.match(slug):
                errors.append(f"invalid slug: {slug}")
                continue
            if not row.get("authority_url", "").startswith(("http://", "https://")):
                errors.append(f"{slug}: authority_url must be http(s)")
                continue
            output_path = root / "references" / f"gaokao-cn-province-{slug}-2026.yaml"
            if output_path.exists() and not args.overwrite:
                skipped += 1
                print(f"skip existing {output_path}")
                continue
            rendered = render_template(template, row, args.checked_at)
            if args.dry_run:
                print(f"would create {output_path}")
            else:
                output_path.write_text(rendered, encoding="utf-8")
                print(f"created {output_path}")
            created += 1

    if errors:
        print("create_all_province_packs: failed", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    action = "would create" if args.dry_run else "created"
    print(f"create_all_province_packs: {action} {created}, skipped {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
