#!/usr/bin/env python3
"""Create a draft 2026 gaokao province pack from the bundled template."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path


SLUG_RE = re.compile(r"^[a-z0-9-]+$")


def render_template(template: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    return template


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--province", required=True, help="Province name, e.g. 广东")
    parser.add_argument("--slug", required=True, help="Lowercase filename slug, e.g. guangdong")
    parser.add_argument("--authority-title", required=True, help="Official authority title")
    parser.add_argument("--authority-url", required=True, help="Official authority URL")
    parser.add_argument("--checked-at", default=date.today().isoformat(), help="YYYY-MM-DD")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true", help="print without writing")
    args = parser.parse_args()

    if not SLUG_RE.match(args.slug):
        print("--slug must contain only lowercase letters, digits, and hyphens", file=sys.stderr)
        return 2
    if not args.authority_url.startswith(("http://", "https://")):
        print("--authority-url must be an http(s) URL", file=sys.stderr)
        return 2

    root = Path(args.root).resolve()
    template_path = root / "references" / "gaokao-cn-province-pack-template.yaml"
    output_path = root / "references" / f"gaokao-cn-province-{args.slug}-2026.yaml"
    template = template_path.read_text(encoding="utf-8")
    rendered = render_template(
        template,
        {
            "province": args.province,
            "last_checked_at": args.checked_at,
            "authority_title": args.authority_title,
            "authority_url": args.authority_url,
        },
    )

    if args.dry_run:
        print(rendered)
        return 0
    if output_path.exists():
        print(f"{output_path}: already exists", file=sys.stderr)
        return 1
    output_path.write_text(rendered, encoding="utf-8")
    print(f"created {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
