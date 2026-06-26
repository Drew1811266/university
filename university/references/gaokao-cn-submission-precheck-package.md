# gaokao-cn 防越权核验包

## 目的

防越权核验包是候选项级证据集合，用来防止把 `研究草稿` 包装成可直接提交的志愿表。它把考生画像、位次证据、省级政策、全量专业级招生计划、计划更正、选科资格和高校招生章程限制绑定到同一组候选项。

运行 `scripts/validate_submission_precheck_package.py package.json` 可做防越权检查。脚本通过只表示证据包结构覆盖关键门槛，可作为 `核验草案` 的辅助证明；它不是必须达成的产品目标，仍不保证录取，也不生成可直接提交的志愿表。

## 何时使用

在以下场景使用：

- 需要检查报告是否已经越权暗示“可提交”“稳录”或“完整闭环”。
- 希望把 `研究草稿` 提升为更谨慎的 `核验草案`。
- 用户已经提供考生位次、选科、批次和底线。
- 已从考生所在省 2026 官方招生专业目录抽取专业组或专业级全量计划。
- 已完成计划更正、增补、取消和替换关系检查。
- 已逐个候选项核验高校 2026 招生章程限制。

任一条件缺失时，不要构造通过包；输出继续保持 `研究草稿`。

## 必需证据

每个核验包必须包含：

- `candidate_profile`：省份、年份、选科或科类、分数、位次、目标批次和偏好。
- `candidate_rank_evidence`：位次来源、口径和脱敏状态；不得包含考生号、密码、验证码或完整身份证号。
- `provincial_policy_evidence`：2026 省级志愿规则官方来源。
- `plan_corrections_evidence`：计划更正检查状态和官方来源。
- `candidate_items[]`：每个保留候选项的提交前证据。

每个 `candidate_items[]` 必须包含：

- `plan_item`：来自省级 2026 官方招生计划或更正的全量专业级条目，`coverage_level=full_major_level`，`field_evidence_level=official_current`，`candidate_pool_eligible=true`。
- `subject_qualification`：选科、科类、批次和资格匹配证据，必须 `status=pass`。
- `charter_restrictions`：高校 2026 招生章程限制，必须覆盖体检、单科、外语语种、投档比例、专业录取办法和调剂规则。

## 不能自动补齐的内容

技能不能自行生成或猜测：

- 考生位次。只有分数时，必须让用户提供位次或用官方一分一段定位后让用户确认。
- 登录后可见的官方计划、位次或辅助系统结果。只能由用户上传脱敏材料，或由用户提供可公开核验的官方文件。
- 高校章程中未写明的体检、单科、语种、专业录取和调剂规则。
- 招生计划中缺失的学费、校区、备注、专业组或专业代码。

## 输出解释

校验脚本输出：

```json
{
  "output_status": "核验草案",
  "guardrail_passed": true,
  "precheck_guard_status": "通过防越权检查",
  "can_upgrade": true,
  "summary": {
    "candidate_item_count": 1,
    "passed_gates": ["全量专业级招生计划"]
  },
  "gaps": []
}
```

`can_upgrade=false` 时，`gaps` 会列出缺失字段，例如：

- `candidate_rank_evidence.sensitive_info_redacted: must be true`
- `candidate_items[0].plan_item.coverage_level: must be full_major_level`
- `candidate_items[0].charter_restrictions: must be an object`

修复缺口前不得输出 `核验草案`，只能保持 `研究草稿`。即使通过防越权检查，也不得称为可提交志愿表。
