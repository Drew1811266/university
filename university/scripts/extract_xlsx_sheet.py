#!/usr/bin/env python3
"""Extract an XLSX worksheet into CSV without third-party dependencies."""

from __future__ import annotations

import argparse
import csv
import posixpath
import re
import sys
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_OFFICE_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def cell_index(ref: str) -> int:
    match = re.match(r"([A-Z]+)", ref.upper())
    if not match:
        return 0
    value = 0
    for char in match.group(1):
        value = value * 26 + (ord(char) - ord("A") + 1)
    return value - 1


def read_xml(archive: zipfile.ZipFile, name: str) -> ET.Element:
    try:
        data = archive.read(name)
    except KeyError as exc:
        raise ValueError(f"missing XLSX part: {name}") from exc
    return ET.fromstring(data)


def text_content(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


def load_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        root = read_xml(archive, "xl/sharedStrings.xml")
    except ValueError:
        return []
    values: list[str] = []
    for item in root.findall(f"{NS_MAIN}si"):
        values.append(text_content(item))
    return values


def workbook_sheets(archive: zipfile.ZipFile) -> list[dict[str, str]]:
    workbook = read_xml(archive, "xl/workbook.xml")
    rels = read_xml(archive, "xl/_rels/workbook.xml.rels")
    rel_targets = {
        rel.attrib.get("Id"): rel.attrib.get("Target")
        for rel in rels.findall(f"{NS_REL}Relationship")
    }
    sheets: list[dict[str, str]] = []
    sheets_root = workbook.find(f"{NS_MAIN}sheets")
    if sheets_root is None:
        return sheets
    for sheet in sheets_root.findall(f"{NS_MAIN}sheet"):
        rel_id = sheet.attrib.get(f"{NS_OFFICE_REL}id")
        target = rel_targets.get(rel_id)
        if not target:
            continue
        path = posixpath.normpath(posixpath.join("xl", target))
        sheets.append(
            {
                "name": sheet.attrib.get("name", ""),
                "sheet_id": sheet.attrib.get("sheetId", ""),
                "path": path,
            }
        )
    return sheets


def select_sheet(sheets: list[dict[str, str]], selector: str | None) -> dict[str, str]:
    if not sheets:
        raise ValueError("workbook contains no worksheets")
    if selector is None:
        return sheets[0]
    if selector.isdigit():
        index = int(selector)
        if index < 0 or index >= len(sheets):
            raise ValueError(f"sheet index {index} out of range; found {len(sheets)} sheets")
        return sheets[index]
    for sheet in sheets:
        if sheet["name"] == selector:
            return sheet
    names = ", ".join(sheet["name"] for sheet in sheets)
    raise ValueError(f"sheet {selector!r} not found; available sheets: {names}")


def cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return text_content(cell.find(f"{NS_MAIN}is"))
    value = text_content(cell.find(f"{NS_MAIN}v"))
    if cell_type == "s":
        try:
            return shared_strings[int(value)]
        except (ValueError, IndexError):
            return ""
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    return value


def worksheet_rows(root: ET.Element, shared_strings: list[str]) -> list[list[str]]:
    rows: list[list[str]] = []
    sheet_data = root.find(f"{NS_MAIN}sheetData")
    if sheet_data is None:
        return rows
    for row in sheet_data.findall(f"{NS_MAIN}row"):
        values: list[str] = []
        for cell in row.findall(f"{NS_MAIN}c"):
            ref = cell.attrib.get("r", "")
            index = cell_index(ref) if ref else len(values)
            while len(values) <= index:
                values.append("")
            values[index] = cell_value(cell, shared_strings).strip()
        rows.append(values)
    max_width = max((len(row) for row in rows), default=0)
    return [row + [""] * (max_width - len(row)) for row in rows]


def write_csv(rows: list[list[str]], output: Path | None) -> None:
    handle: Any
    handle = output.open("w", encoding="utf-8", newline="") if output else sys.stdout
    try:
        writer = csv.writer(handle)
        writer.writerows(rows)
    finally:
        if output:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xlsx_path", type=Path)
    parser.add_argument("--sheet", help="sheet name or 0-based index; defaults to first sheet")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        with zipfile.ZipFile(args.xlsx_path) as archive:
            shared_strings = load_shared_strings(archive)
            sheet = select_sheet(workbook_sheets(archive), args.sheet)
            root = read_xml(archive, sheet["path"])
            rows = worksheet_rows(root, shared_strings)
        if not rows:
            raise ValueError("selected worksheet is empty")
        write_csv(rows, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"extract_xlsx_sheet: failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
