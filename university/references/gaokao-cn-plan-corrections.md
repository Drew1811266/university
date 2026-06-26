# gaokao-cn 招生计划更正规则

## 目的

计划更正、增补和取消会改变可填集合。旧条目一旦被官方更正，不得继续进入最终志愿排序。

## correction_status

- `active`：当前有效的原始计划条目。
- `added`：更正或增补公告新增的有效条目。
- `corrected`：官方更正后仍有效，但字段发生变化。
- `cancelled`：官方取消，必须从候选池剔除。
- `replaced`：被新条目替换，必须从候选池剔除，并填写 `replaced_by`。
- `unknown`：更正状态未核验，只能输出 `待核验` 或 `研究草稿`。

## 替换关系

使用 `replaces` 和 `replaced_by` 建立关系：

- 新条目填写 `replaces` 指向旧 `candidate_item_id`。
- 旧条目填写 `replaced_by` 指向新 `candidate_item_id`。
- 若公告只说明取消而无替换，旧条目设为 `cancelled`，`replaced_by` 为空。

## 变更类型

在 `remarks` 或证据台账中标出具体变更：

- `added`：新增院校、专业组、专业或计划。
- `cancelled`：取消院校、专业组、专业或计划。
- `code_changed`：院校代码、专业组代码或专业代码变化。
- `count_changed`：计划人数变化。
- `tuition_changed`：学费变化。
- `campus_changed`：校区变化。
- `subject_changed`：选科要求变化。
- `remark_changed`：备注或资格条件变化。

## 有效计划视图

生成最终候选池时：

1. 排除 `cancelled` 和 `replaced`。
2. 保留 `active`、`added`、`corrected`。
3. `unknown` 只能进入 `待核验`，不得进入提交前排序。
4. 若同一 `candidate_item_id` 出现多个版本，保留最后官方更正版本，并在证据中列出旧版本。

## 输出要求

更正相关输出必须展示：

- 旧条目。
- 新条目。
- 更正公告来源。
- 更正发布时间。
- 替换或取消关系。
- 对候选池和排序的影响。
