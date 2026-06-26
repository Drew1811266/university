# Sample Prompts

Use these prompts to check that the skill applies the resource library conservatively and keeps time-sensitive claims separate from stable background.

## Prompt 1: Stable School Background

Prompt:

```text
请用 university skill 简要介绍浙江大学，说明 profile_source_status，并提醒哪些内容不能只靠资源库判断。
```

Expected behavior:

- Read `university-profile-search-index.md`, then `university-profile-library.md`, then only the 001-050 China segment.
- Use the A-level profile entry only for non-time-sensitive background such as history, location, positioning, and stable strengths.
- State that admissions, programs, fees, deadlines, policies, scholarships, and other time-sensitive fields require current official sources.

## Prompt 2: Admissions Or Policy Question

Prompt:

```text
北京邮电大学 2026 年本科招生政策和热门专业录取风险怎么样？
```

Expected behavior:

- Do not answer admissions policy or admission risk from the profile library alone.
- Ask for the applicant province, subject category or selected subjects, score, rank, target batch, and risk tolerance if missing.
- Verify 2026 official provincial and university admissions sources, or mark unreleased items as `待核验`.

## Prompt 3: School Comparison

Prompt:

```text
对比华中科技大学、西安交通大学和哈尔滨工业大学的学校背景和优势方向。
```

Expected behavior:

- Locate all schools through the search index and load only the relevant 001-050 segment.
- Use A-level entries for concise non-time-sensitive background comparison.
- Avoid treating the Soft科 segment as a quality conclusion or admissions ranking.

## Prompt 4: Unlisted Or Ambiguous School

Prompt:

```text
帮我查一下“南大”的学校概况。
```

Expected behavior:

- Use aliases in the search index to detect ambiguity between 南京大学 and possible informal uses.
- Ask a brief clarification when context is insufficient.
- If the target is not covered by the library, state that it is not listed and switch to official-source verification.

## Prompt 5: Source Conflict Or Missing Date

Prompt:

```text
某大学官网简介和招生简章里的校区信息不一致，应该采用哪个？
```

Expected behavior:

- Treat the official school profile as stable background only.
- For admissions, training location, campus assignment, fees, deadlines, and policy fields, prefer the most specific current official admissions page or provincial authority source.
- Record uncertainty and use `待核验` when current-year official evidence is missing or conflicting.
