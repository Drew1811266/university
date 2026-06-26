#!/usr/bin/env python3
"""Extract simple HTML tables into CSV for official-source import review."""

from __future__ import annotations

import argparse
import csv
import html
import re
import sys
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._current_table: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "table":
            self._in_table = True
            self._current_table = []
        elif tag == "tr" and self._in_table:
            self._in_row = True
            self._current_row = []
        elif tag in {"td", "th"} and self._in_row:
            self._in_cell = True
            self._current_cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"td", "th"} and self._in_cell:
            self._current_row.append(clean_text("".join(self._current_cell)))
            self._current_cell = []
            self._in_cell = False
        elif tag == "tr" and self._in_row:
            if any(cell for cell in self._current_row):
                self._current_table.append(self._current_row)
            self._current_row = []
            self._in_row = False
        elif tag == "table" and self._in_table:
            if self._current_table:
                self.tables.append(self._current_table)
            self._current_table = []
            self._in_table = False

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_cell.append(data)


def clean_text(value: str) -> str:
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def read_input(source: str) -> str:
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(source, headers={"User-Agent": "university-skill/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 - official source fetch helper
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, "replace")
    return Path(source).read_text(encoding="utf-8")


def normalize_table(table: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    max_width = max(len(row) for row in table)
    padded = [row + [""] * (max_width - len(row)) for row in table]
    header = padded[0]
    if not any(header):
        header = [f"column_{index}" for index in range(1, max_width + 1)]
    seen: dict[str, int] = {}
    unique_header: list[str] = []
    for index, column in enumerate(header, start=1):
        name = column or f"column_{index}"
        seen[name] = seen.get(name, 0) + 1
        unique_header.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    return unique_header, padded[1:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", help="HTML file path or official URL")
    parser.add_argument("--table-index", type=int, default=0, help="0-based table index to export")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        content = read_input(args.source)
        parser_obj = TableParser()
        parser_obj.feed(content)
    except Exception as exc:  # noqa: BLE001
        print(f"extract_html_table: failed to read or parse input: {exc}", file=sys.stderr)
        return 1

    tables = parser_obj.tables
    if not tables:
        print("extract_html_table: no tables found", file=sys.stderr)
        return 1
    if args.table_index < 0 or args.table_index >= len(tables):
        print(f"extract_html_table: table index {args.table_index} out of range; found {len(tables)} tables", file=sys.stderr)
        return 1

    header, rows = normalize_table(tables[args.table_index])
    output_handle = args.output.open("w", encoding="utf-8", newline="") if args.output else sys.stdout
    try:
        writer = csv.writer(output_handle)
        writer.writerow(header)
        writer.writerows(rows)
    finally:
        if args.output:
            output_handle.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
