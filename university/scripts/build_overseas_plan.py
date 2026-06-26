#!/usr/bin/env python3
"""Build a gaokao-to-overseas application verification plan."""

from __future__ import annotations

import argparse
from pathlib import Path


COUNTRY_SOURCE_HINTS = {
    "英国": ["大学课程页/International entry requirements", "UCAS", "GOV.UK Student visa", "英国学位授予资格官方查询", "中国留学网/留服中心"],
    "美国": ["大学本科国际招生页", "DAPIP", "Study in the States", "Department of State", "中国留学网/留服中心"],
    "加拿大": ["大学本科国际招生页", "IRCC study permit", "DLI list", "PAL/TAL/CAQ 相关官方说明", "中国留学网/留服中心"],
    "澳大利亚": ["大学课程页", "CRICOS", "TEQSA", "Home Affairs Student visa 500", "中国留学网/留服中心"],
    "日本": ["大学入試/留学生募集要項", "JASSO/EJU", "日本驻华使领馆签证信息", "中国留学网/留服中心"],
    "韩国": ["大学 International Admissions", "Study in Korea", "韩国签证官方入口", "中国留学网/留服中心"],
    "新加坡": ["大学本科招生页", "ICA Student's Pass", "教育部/学校官方资质信息", "中国留学网/留服中心"],
    "香港": ["大学本科招生页", "香港入境事务处学生签证/进入许可", "教育局/院校官方信息", "中国留学网/留服中心"],
    "澳门": ["大学本科招生页", "澳门高等教育局/院校官方信息", "入境/逗留官方说明", "中国留学网/留服中心"],
}


def source_hints(country: str) -> list[str]:
    return COUNTRY_SOURCE_HINTS.get(country, ["目标大学项目页", "目标国家/地区教育质量保障系统", "目标国家/地区签证官网", "中国留学网/留服中心", "中国领事服务网"])


def build_plan(country: str, pathway: str, intake: str, program: str | None) -> str:
    target = f"{country} {program}" if program else country
    hints = source_hints(country)
    lines: list[str] = []
    lines.append("# 高考生海外本科申请核验计划")
    lines.append("")
    lines.append(f"- 目标国家/地区：{country}")
    lines.append(f"- 申请路径：{pathway}")
    lines.append(f"- 入学季：{intake}")
    lines.append(f"- 目标项目：{program or '待补充'}")
    lines.append("- 输出状态：研究草稿")
    lines.append("")
    lines.append("> 该计划不代表录取、签证、入境、学历认证、住宿或职业资格已经成立；每项都必须回到当前官方来源核验。")
    lines.append("")
    lines.append("## 录取可行性")
    lines.append("")
    lines.append(f"- 核验 {target} 是否接受中国高考成绩或该路径。")
    lines.append("- 记录成绩口径、语言要求、材料清单、截止日期、offer 条件、押金和退款政策。")
    lines.append("- 证据缺口：目标大学具体项目页、目标入学季要求、是否仍开放申请。")
    lines.append("")
    lines.append("## 签证可行性")
    lines.append("")
    lines.append("- 将 offer 条件与学生签证条件分开核验。")
    lines.append("- 核验签证前置文件、资金证明、真实学习目的、体检/保险/入境要求和预约周期。")
    lines.append("- 证据缺口：目标国家/地区当前学生签证官网。")
    lines.append("")
    lines.append("## 资金可行性")
    lines.append("")
    lines.append("- 估算完整学习周期，不只看押金或第一年学费。")
    lines.append("- 覆盖学费、住宿、生活费、保险、签证、机票、假期住宿、汇率和学费上涨。")
    lines.append("- 不默认用打工覆盖核心费用。")
    lines.append("")
    lines.append("## 认证风险")
    lines.append("")
    lines.append("- 通过中国留学网/留服中心信息核验学校、项目、学习方式和加强认证审查风险。")
    lines.append("- 认证院校查询只能作择校参考，不是未来认证保证。")
    lines.append("")
    lines.append("## 职业资格风险")
    lines.append("")
    lines.append("- 医学、牙科、药学、法律、教师、建筑、心理、护理、会计、工程等专业必须单独核验执业资格。")
    lines.append("- 国外毕业不等于当地执业，也不等于回国直接取得职业资格。")
    lines.append("")
    lines.append("## 安全/住宿风险")
    lines.append("")
    lines.append("- 核验学校住宿、正规租房路径、押金条款、城市安全提醒、领事提醒和常见诈骗。")
    lines.append("- 重要文件保留电子与纸质备份。")
    lines.append("")
    lines.append("## 国内备选风险")
    lines.append("")
    lines.append("- 对齐国内高考志愿、国外押金、语言成绩、签证预约、住宿和入学日期。")
    lines.append("- 不因海外 offer 未核验完成而放弃国内志愿兜底。")
    lines.append("")
    lines.append("## 官方来源起点")
    lines.append("")
    for hint in hints:
        lines.append(f"- {hint}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", required=True)
    parser.add_argument("--pathway", required=True)
    parser.add_argument("--intake", required=True)
    parser.add_argument("--program")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = build_plan(args.country, args.pathway, args.intake, args.program)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
