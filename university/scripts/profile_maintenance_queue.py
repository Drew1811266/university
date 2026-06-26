#!/usr/bin/env python3
"""Build a maintenance queue for the Markdown university profile library."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


HEADING_RE = re.compile(r"^###\s+(.+)$", re.MULTILINE)
STATUS_RE = re.compile(r"\| profile_source_status \| ([ABC])：([^|]+)\|")
FIELD_RE = re.compile(r"^\| ([^|]+) \| ([^|]*) \|$", re.MULTILINE)
PROFILE_EVIDENCE_FIELDS = {
    "history_evidence": "历史字段精确来源",
    "campus_evidence": "校区字段精确来源",
    "institution_type_evidence": "办学性质/定位字段精确来源",
    "strengths_evidence": "优势领域字段精确来源",
    "source_url": "主要官方来源 URL",
}


def field_gaps(fields: dict[str, str]) -> list[str]:
    gaps: list[str] = []
    for field, label in PROFILE_EVIDENCE_FIELDS.items():
        value = fields.get(field, "")
        if not value or "待补充" in value or "入口级" in value:
            gaps.append(label)
    return gaps


def next_action(level: str, gaps: list[str], reminders: str) -> str:
    if level == "C":
        return "先回官网简介、信息公开或学校概况栏目重建条目，再决定是否升级到 A/B。"
    if gaps:
        return "补齐精确简介/概况页和字段级证据；补齐前继续按 B 级背景线索使用。"
    if any(marker in reminders for marker in ("更名", "合并", "转设", "校区迁移", "办学性质", "栏目迁移")):
        return "复核稳定背景变化后更新提醒字段和最后核验日期。"
    return "抽样复核措辞和来源 URL，确认无强断言。"


def parse_entries(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    headings = list(HEADING_RE.finditer(text))
    entries: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        block = text[start:end]
        status_match = STATUS_RE.search(block)
        fields = {match.group(1).strip(): match.group(2).strip() for match in FIELD_RE.finditer(block)}
        level = status_match.group(1) if status_match else "unknown"
        description = status_match.group(2).strip() if status_match else "缺少 profile_source_status"
        reminders = fields.get("非时效性核验提醒", "")
        source = fields.get("核验来源", "")
        gaps = field_gaps(fields)
        priority = 0
        reasons: list[str] = []
        if level == "C":
            priority += 100
            reasons.append("C 级来源需复核")
        if level == "B":
            priority += 60
            reasons.append("B 级精确简介页待补充")
        if "待补充" in source or "待补充" in description:
            priority += 20
            reasons.append("精确来源待补充")
        if gaps:
            priority += min(20, len(gaps) * 4)
            reasons.append("字段级证据缺口")
        if any(marker in reminders for marker in ("更名", "合并", "转设", "校区迁移", "办学性质", "栏目迁移")):
            priority += 15
            reasons.append("稳定背景字段可能变化")
        if priority:
            entries.append(
                {
                    "school": heading.group(1).strip(),
                    "profile_source_status": level,
                    "priority": priority,
                    "reasons": reasons,
                    "field_gaps": gaps,
                    "next_action": next_action(level, gaps, reminders),
                    "source": source,
                    "file": str(path),
                    "line": text.count("\n", 0, heading.start()) + 1,
                }
            )
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    entries: list[dict[str, Any]] = []
    summary = {"A": 0, "B": 0, "C": 0, "unknown": 0}
    for path in sorted((root / "references").glob("university-profiles-*.md")):
        if path.name == "university-profiles-international.md":
            continue
        parsed = parse_entries(path)
        entries.extend(parsed)
        text = path.read_text(encoding="utf-8")
        for match in STATUS_RE.finditer(text):
            summary[match.group(1)] += 1
    entries.sort(key=lambda item: (-item["priority"], item["file"], item["line"]))
    output_data = {
        "summary": summary,
        "priority_queue": entries,
        "rule": "先复核 C 级、用户常查 B 级、来源待补充和发生更名/合并/转设/校区/办学性质变化的条目。",
    }
    output = json.dumps(output_data, ensure_ascii=False, indent=2 if args.pretty else None)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
