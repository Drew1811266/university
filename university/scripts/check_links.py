#!/usr/bin/env python3
"""Check URLs embedded in gaokao-cn YAML/JSON/Markdown files."""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+")


def iter_candidate_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    return [
        path
        for path in root.rglob("*")
        if path.suffix.lower() in {".yaml", ".yml", ".json", ".md"}
    ]


def iter_urls(roots: list[Path]) -> dict[str, set[Path]]:
    urls: dict[str, set[Path]] = {}
    for root in roots:
        for path in iter_candidate_files(root):
            text = path.read_text(encoding="utf-8")
            for url in URL_RE.findall(text):
                urls.setdefault(url.rstrip(".,;"), set()).add(path)
    return urls


def check_url(url: str, timeout: float) -> tuple[bool, str]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "gaokao-cn-link-check/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status < 400, str(response.status)
    except urllib.error.HTTPError as exc:
        if exc.code == 405:
            request = urllib.request.Request(url, method="GET", headers={"User-Agent": "gaokao-cn-link-check/0.1"})
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return response.status < 400, str(response.status)
            except Exception as get_exc:  # noqa: BLE001
                return False, str(get_exc)
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="*", type=Path, default=[Path(__file__).resolve().parents[1]])
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--allow-failures", action="store_true")
    args = parser.parse_args()

    roots = [path.resolve() for path in args.roots]
    urls = iter_urls(roots)
    failures: list[str] = []
    for url, paths in sorted(urls.items()):
        ok, detail = check_url(url, args.timeout)
        status = "OK" if ok else "FAIL"
        rel_paths = ", ".join(str(path) for path in sorted(paths))
        print(f"{status} {detail} {url} ({rel_paths})")
        if not ok:
            failures.append(url)

    if failures and not args.allow_failures:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
