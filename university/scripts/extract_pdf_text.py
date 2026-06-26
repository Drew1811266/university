#!/usr/bin/env python3
"""Extract review text from an official PDF before manual table normalization."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import zlib
from pathlib import Path
from typing import Any


def run_pdftotext(pdf_path: Path) -> str | None:
    executable = shutil.which("pdftotext")
    if not executable:
        return None
    completed = subprocess.run(
        [executable, "-layout", str(pdf_path), "-"],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "pdftotext failed")
    return completed.stdout


def unescape_pdf_literal(value: str) -> str:
    output: list[str] = []
    index = 0
    escapes = {
        "n": "\n",
        "r": "\r",
        "t": "\t",
        "b": "\b",
        "f": "\f",
        "(": "(",
        ")": ")",
        "\\": "\\",
    }
    while index < len(value):
        char = value[index]
        if char != "\\":
            output.append(char)
            index += 1
            continue
        index += 1
        if index >= len(value):
            break
        escaped = value[index]
        if escaped in escapes:
            output.append(escapes[escaped])
            index += 1
        elif escaped in "\r\n":
            if escaped == "\r" and index + 1 < len(value) and value[index + 1] == "\n":
                index += 2
            else:
                index += 1
        elif escaped.isdigit():
            digits = escaped
            index += 1
            for _ in range(2):
                if index < len(value) and value[index].isdigit():
                    digits += value[index]
                    index += 1
            output.append(chr(int(digits, 8)))
        else:
            output.append(escaped)
            index += 1
    return "".join(output)


def iter_streams(data: bytes) -> list[bytes]:
    streams: list[bytes] = []
    for match in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", data, re.DOTALL):
        stream = match.group(1)
        prefix = data[max(0, match.start() - 300): match.start()]
        if b"/FlateDecode" in prefix:
            try:
                stream = zlib.decompress(stream)
            except zlib.error:
                pass
        streams.append(stream)
    return streams


def fallback_extract(pdf_path: Path) -> str:
    data = pdf_path.read_bytes()
    chunks: list[str] = []
    for stream in iter_streams(data):
        text = stream.decode("latin-1", errors="ignore")
        if " Tj" not in text and " TJ" not in text and "'" not in text and '"' not in text:
            continue
        literals = re.findall(r"\(((?:\\.|[^\\()])*)\)", text)
        for literal in literals:
            value = unescape_pdf_literal(literal).strip()
            if value:
                chunks.append(value)
    if not chunks:
        raise RuntimeError("no extractable text found; install pdftotext or convert the PDF manually")
    return "\n".join(chunks) + "\n"


def extract_text(pdf_path: Path, tool: str) -> str:
    if tool not in {"auto", "pdftotext", "fallback"}:
        raise RuntimeError(f"unsupported tool: {tool}")
    if tool in {"auto", "pdftotext"}:
        text = run_pdftotext(pdf_path)
        if text is not None:
            return text
        if tool == "pdftotext":
            raise RuntimeError("pdftotext not found")
    return fallback_extract(pdf_path)


def write_text(text: str, output: Path | None) -> None:
    handle: Any
    handle = output.open("w", encoding="utf-8") if output else sys.stdout
    try:
        handle.write(text)
        if text and not text.endswith("\n"):
            handle.write("\n")
    finally:
        if output:
            handle.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--tool", choices=["auto", "pdftotext", "fallback"], default="auto")
    args = parser.parse_args()

    try:
        text = extract_text(args.pdf_path, args.tool)
        write_text(text, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"extract_pdf_text: failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
