# gaokao-cn 防越权门禁

## 目的

防越权门禁用于判断报告是否可以从 `研究草稿` 提升为更谨慎的 `核验草案`。它不生成志愿表、不承诺录取，只检查关键证据是否齐全，防止模型把草案表述成可直接提交的志愿表。

## 五项硬门槛

只有以下五项全部通过，才能输出 `核验草案`：

1. `provincial_policy_2026`：考生省份 2026 省级政策已核验，包括志愿模式、批次、志愿数量、确认方式、填报时间、投档和征集志愿规则。
2. `enrollment_plan_2026`：2026 招生专业目录及官方更正、增补、取消和替换关系已核验。
3. `candidate_rank`：考生位次已存在，且与 2026 目标省份和科类口径一致。
4. `subject_qualification`：科类、选科、资格和批次条件已核验。
5. `charter_restrictions_2026`：候选项对应高校 2026 招生章程限制已核验，包括体检、单科、外语、投档比例、专业录取和调剂规则。

任一门槛失败，输出状态只能是 `研究草稿`。

## 证据字段约定

`scripts/check_submission_gates.py` 使用 evidence ledger JSON 数组。字段名可以是精确字段，也可以带院校代码后缀：

- `provincial_policy_2026`
- `enrollment_plan_2026`
- `plan_corrections_2026`
- `candidate_rank`
- `subject_qualification`
- `charter_restrictions_2026:{institution_code}`

高考最终填报相关官方规则必须使用：

- `field_evidence_level: official_current`
- `applicable_year: 2026`

`candidate_rank` 可来自用户确认的 2026 官方成绩/位次信息，但若只是截图或转述，报告中仍应提醒用户在正式系统中逐项复核。

## 脚本输入

必需：

- 省份 pack YAML。
- 考生画像 JSON。
- 候选池 JSON。
- 五维风险 JSON。
- 证据台账 JSON。

脚本检查：

- 省份、年份、位次是否一致。
- province pack 中关键状态是否已发布或更正。
- 候选池保留项是否仍有 `proof_gaps`。
- 每个保留候选项是否有对应高校章程证据。
- 风险输出是否覆盖所有保留候选项。

## 输出

输出 JSON：

```json
{
  "output_status": "研究草稿",
  "guardrail_passed": false,
  "precheck_guard_status": "未通过防越权检查",
  "can_upgrade": false,
  "gates": [
    {
      "id": "enrollment_plan_2026",
      "status": "fail",
      "reason": "缺少 2026 招生计划或更正核验"
    }
  ],
  "last_checked_at": "YYYY-MM-DD"
}
```

`guardrail_passed=true` 时，仍必须提醒用户在省级正式填报系统中核对代码、专业组、专业、计划人数、备注、费用、校区和确认状态。`can_upgrade` 是兼容旧脚本的布尔字段，语义等同于“防越权检查通过”，不是“已经生成可提交志愿表”。

## 候选项级防越权核验包

需要更严格检查时，可构造候选项级证据包并运行：

```bash
python3 scripts/validate_submission_precheck_package.py package.json
```

候选项级证据包见 `references/gaokao-cn-submission-precheck-package.md` 和 `references/submission-precheck-package.schema.json`。它比普通 evidence ledger 更严格，要求每个保留候选项同时绑定：

- 全量专业级 2026 省级招生计划条目。
- 计划更正、增补、取消或替换检查。
- 考生 2026 位次证据，且敏感信息已脱敏。
- 选科、科类、批次和资格匹配证据。
- 高校 2026 招生章程中体检、单科、外语、投档比例、专业录取和调剂规则。

没有通过候选项级证据包校验时，不得把报告标为 `核验草案`。通过校验也不得把报告称为可直接提交的志愿表。
