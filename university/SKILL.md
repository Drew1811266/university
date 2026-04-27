---
name: university
description: "Platform-neutral university information research and synthesis. Use for university profiles, admissions verification, academic majors or programs, China gaokao volunteer filling, China gaokao overseas undergraduate applications, and official-source checks."
---

# university

## Overview

Use this skill to research, verify, organize, and summarize university information across China, South Korea, Japan, the United Kingdom, the United States, Canada, and Australia. Produce structured, source-traceable reports about schools, undergraduate admissions, postgraduate admissions, and academic programs.

## Portability

Treat this `SKILL.md` as the source of truth across AI platforms. Platform-specific metadata, invocation syntax, browser tools, file tools, memory systems, citation managers, and database integrations are optional adapters.

When a platform cannot browse the web, inspect files, or open linked pages, state the limitation and provide a verification plan. When a platform cannot automatically load bundled references, ask the user to provide the needed reference text or manually load the relevant file from `references/`.

## Default Scope

- Countries: China, South Korea, Japan, the United Kingdom, the United States, Canada, and Australia.
- Depth: university profile, undergraduate admissions, postgraduate admissions, academic departments, majors, and programs.
- Output language: Chinese by default, unless the user asks for another language.
- Source policy: official sources first; credible third-party sources may supplement context only when clearly labeled.
- Freshness policy: time-sensitive fields such as admissions, fees, deadlines, scholarships, visas, policies, and gaokao volunteer rules require 2025-or-later official sources by default. Stable background such as school history, institutional positioning, campus overview, and long-term academic strengths may use facts from a current official profile page even when the historical event occurred before 2025.

## Core Workflow

1. Clarify the research target.
   - Identify country, university, school/department, degree level, major/program, applicant background, intake year, and desired output format.
   - If the user asks about China mainland gaokao volunteer filling, identify province, year, subject category or selected subjects, score, rank, target batch, target universities or majors, and any special eligibility.
   - If the user asks about China gaokao candidates applying overseas, identify destination country, target intake, application path, gaokao score or expected score, high-school transcript, language tests, budget, visa constraints, credential recognition concerns, and domestic-gaokao backup plan.
   - For consultation-style China mainland gaokao volunteer filling or China gaokao overseas undergraduate application tasks, read `references/consultation-intake-profile.md` and complete the user profile before detailed recommendations.
   - Ask profile questions in stages: start with hard eligibility information and score/application positioning, then ask about volunteer mode or application route, major and university preferences, family constraints, risk tolerance, and special pathways.
   - Prefer 3-7 high-impact questions per turn. Skip anything the user already provided. If missing information does not block a preliminary answer, mark it as `待补充` and continue with clear limits.
   - If the user asks broadly, define a practical search scope before collecting details.
   - If the user asks for comparison, define the comparison dimensions first.

2. Build the source plan.
   - Prefer official university websites, admissions offices, graduate schools, faculties, departments, course catalogs, application portals, and government or exam-agency pages.
   - For school introductions, background summaries, university profiles, institutional positioning, history, or stable academic strengths, first read `references/university-profile-search-index.md`, then read `references/university-profile-library.md` for field rules, then load only the one 50-school segment file that contains the target school. Do not load the full profile library by default.
   - Treat profile library entries as non-time-sensitive background only. `A` entries may support concise background summaries; `B` entries are background leads with precise profile source still pending; `C` entries require an explicit source-recheck warning. Admissions, programs, tuition, scholarships, deadlines, language requirements, policies, and other time-sensitive fields still require 2025-or-later official-source verification.
   - For verification, comparison, strategy, gaokao volunteer filling, overseas application, visa, credential recognition, fees, deadlines, or other high-impact tasks, read `references/source-evidence-ledger.md` and keep field-level evidence.
   - For China mainland gaokao volunteer filling, the highest authority is the candidate's provincial education examination authority for that year's policy, enrollment plan, volunteer filling system, and admission rules. Use 阳光高考 and university admissions charters for auxiliary verification; third-party predictions cannot replace official rules.
   - For China mainland gaokao volunteer filling, read `references/china-provincial-exam-authority-index.md` after confirming the candidate's province, then verify the current-year policy, enrollment plan, volunteer system, one-score-one-rank table, filing rules, and admission notices from that provincial authority.
   - For China gaokao candidates applying overseas, verify university admission, student visa, funds, entry compliance, credential recognition, professional licensing, housing, and safety from separate official sources; an offer does not prove the other items.
   - For China gaokao candidates applying overseas, read `references/overseas-official-source-map.md` for destination-country official education, quality assurance, visa, credential recognition, and safety sources.
   - Apply a 2025-or-later freshness filter to time-sensitive fields by default. Use date filters when available, and include current intake year, 2025, or later years in search terms when useful.
   - For 2026 gaokao volunteer scenarios, prioritize 2026 official provincial documents. If a 2026 document has not been released, use the latest 2025-or-later official source and mark the item as `待核验`.
   - Use `references/country-source-guide.md` for country-specific source types and search hints.
   - Use third-party ranking, media, encyclopedia, or study-abroad sites only as supplemental context, and label them as non-official.

3. Extract facts.
   - Capture school name, location, website, institution type, academic strengths, profile-library source quality, admissions pathways, program names, degree levels, application requirements, language requirements, materials, fees, scholarships, deadlines, and official links.
   - Preserve original names in the local language when useful, with Chinese translations when appropriate.
   - Record source URL, source type, source title, publication or update date when available, applicable year or intake, applicable audience, retrieval date, and evidence level.

4. Organize and synthesize.
   - Use `references/report-schema.md` for the default structured report format.
   - For narrow questions such as a short school introduction, a quick program check, or preliminary risk judgment, use the lightweight Q&A mode in `references/report-schema.md` before producing a full report.
   - If a target school is in the profile library, use its entry only for non-time-sensitive background and state source quality, verification source, and last manual verification date. If it is not listed, say the profile library has no entry and use official sources instead.
   - For a single university, produce a full profile and admissions report.
   - For multiple universities, provide a comparison table first, then concise school-by-school notes.
   - For major or program research, focus on departments, degree levels, curriculum or research direction, language of instruction, eligibility, application route, and official program page.

5. Verify and flag uncertainty.
   - Cross-check high-impact fields such as deadlines, fees, language scores, eligibility, application materials, and scholarship rules against official sources.
   - Mark missing, unclear, conflicting, or inaccessible information as `待核验`.
   - Do not invent facts to fill gaps.

## Information Integrity Rules

- Never fabricate application requirements, deadlines, tuition, scholarships, rankings, majors, program names, language requirements, policy details, source titles, URLs, or update dates.
- Never provide guaranteed gaokao volunteer outcomes such as `稳录`, `保录取`, `保专业`, or `一定录取`. Provide risk levels, official verification paths, and items requiring confirmation instead.
- Never imply that an overseas university offer guarantees a student visa, entry permission, credential recognition in China, housing availability, employment rights, or future professional licensure.
- Do not treat third-party summaries as authoritative when official pages are available.
- When sources conflict, prefer the most specific official page for the relevant year, degree level, department, or program, and note the conflict.
- When information changes by intake year, state the year or cycle explicitly.
- Do not use pre-2025 information for time-sensitive fields by default. Historical facts from a current official school profile may be used for stable background; label older standalone sources as historical when relevant.
- If an official live page has no visible publication or update date, use it only when it clearly applies to the current or target intake cycle; record the update date as unknown and mark time-sensitive fields as needing verification when appropriate.

## Reference Files

- Read `references/research-workflow.md` for the detailed research workflow, source quality rules, and uncertainty handling.
- Read `references/report-schema.md` when producing a university report, comparison table, or program information table.
- Read `references/source-evidence-ledger.md` when the task includes source verification, high-impact decisions, admissions, fees, deadlines, scholarships, visas, credential recognition, professional licensing, gaokao volunteer rules, enrollment plans, program requirements, or conflicting sources.
- Read `references/country-source-guide.md` when researching a specific country or choosing source types.
- Read `references/sample-prompts.md` when the user asks for sample prompts, expected behavior examples, usage demonstrations, or when validating whether this skill follows its source-quality and freshness rules.
- Read `references/university-profile-search-index.md` when the user asks for a school introduction, university background, institutional profile, school positioning, history, stable strengths, or a non-admissions overview. Use it to locate whether the school is covered and which profile segment file to load.
- After the search index, read `references/university-profile-library.md` for resource-library rules, field meanings, source-quality levels, and maintenance constraints.
- Load only the target segment file: `references/university-profiles-china-001-050.md`, `references/university-profiles-china-051-100.md`, `references/university-profiles-china-101-150.md`, `references/university-profiles-china-151-200.md`, `references/university-profiles-china-201-250.md`, `references/university-profiles-china-251-300.md`, `references/university-profiles-china-301-350.md`, `references/university-profiles-china-351-400.md`, or `references/university-profiles-international.md`.
- Read `references/consultation-intake-profile.md` when the user asks for consultation, planning, recommendation, strategy, checklist, or risk analysis in China mainland gaokao volunteer filling or China gaokao overseas undergraduate application scenarios.
- Read `references/china-gaokao-volunteer-guide.md` and `references/china-provincial-exam-authority-index.md` when the user asks about China mainland gaokao volunteer filling, provincial undergraduate admissions, 院校专业组, 专业（类）+院校, 招生计划, 投档录取规则, 调剂, 退档, 征集志愿, or related risk checks.
- Read `references/china-gaokao-overseas-study-guide.md` and `references/overseas-official-source-map.md` when the user asks about China gaokao candidates applying to overseas undergraduate programs, using gaokao scores abroad, direct entry, foundation, international year one, bridge or language programs, overseas offer conditions, student visas, funds, credential recognition, professional licensing, domestic-backup timing, agents, deposits, housing, or pre-departure safety.
