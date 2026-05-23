# Stage 5X EPS Unit Conflict Apply

项目路径：`D:\_datefac`

## 当前状态

Stage 5W 已完成并推送。

- commit: `dd533f9e2e3eb6e5e3385de0701574a71a13ea10`
- push 状态：成功，`origin/main`
- summary 文件：`173_stage5w_eps_unit_conflict_summary.json`
- `check_delivery_state.py --json`：`overall_status=PASS`

`173_stage5w_eps_unit_conflict_summary.json` 关键结果：

```text
eps_conflict_count=5
eps_value_same_count=5
eps_value_mismatch_count=0
eps_unit_conflict_count=5
recommended_keep_existing_count=0
recommended_replace_with_candidate_count=5
recommended_unit_normalization_rule_count=1
ready_for_stage5x_eps_apply=true
production_06_unchanged=true
formal_rules_unchanged=true
stage5w_eps_conflict_review_pass=true
check_delivery_state.py --json: overall_status=PASS
```

EPS 5 个年份值一致：`2024A / 2025A / 2026E / 2027E / 2028E`。

注意：年份标签必须以 Stage 5W 报告和源数据为准，不允许自行把 `2025A` 改成 `2025E`。

Stage 5W 推荐：

- EPS / 每股收益统一单位推荐为：`元/股`
- 当前冲突为：`ratio` vs `元`
- 建议将 `ratio` 口径归一到 `元/股`
- Stage 5W 只给建议，未修改生产文件，未修改 formal rules

## 本轮目标

执行 Stage 5X，只处理 EPS / 每股收益 5 个 06 单位冲突。

将已审查通过、`value_same=true` 的 EPS 5 行安全写入生产 06。

最终单位统一使用：`元/股`。

## 严格范围

1. 只允许处理 EPS / 每股收益 5 行。
2. 只允许处理 Stage 5W 报告中 `ready_for_stage5x_eps_apply=true` 的记录。
3. 只允许写入生产 06 中这 5 行对应记录。
4. 不允许处理其他指标。
5. 不允许重跑大范围 Stage 5V2。
6. 不允许改 01 / 02 / 02A / 05。
7. 不允许改 official 02B。
8. 默认不修改 formal rules。
9. 如果 formal rules 必须更新，本轮只生成建议报告，不直接修改 formal rules。
10. 不允许自动扩大修复范围。

## 必须读取的输入依据

- `173_stage5w_eps_unit_conflict_summary.json`
- Stage 5W 详细 review 输出文件，如存在
- 当前生产 06 文件
- Stage 5V2 conflict / skipped / rejected / audit 文件中 EPS 相关记录

## 执行前校验

必须确认：

1. 当前 git HEAD 为 `dd533f9e2e3eb6e5e3385de0701574a71a13ea10`，或当前分支已经包含该 commit。
2. `check_delivery_state.py --json` 当前为 `PASS`。
3. production 06 当前行数为 `114`。
4. EPS 待处理冲突数为 `5`。
5. 这 5 行均 `value_same=true`。
6. `eps_value_mismatch_count=0`。
7. `ready_for_stage5x_eps_apply=true`。
8. 无新增 blocker。
9. 工作区可能仍有历史未提交文件 `tools/update_stage5v_production_06_safe_rows.py`，该文件不是本轮产物，不得纳入本轮提交，除非它正是本轮必需脚本并经过明确复核。

## 执行逻辑

对 Stage 5W 标记为 `recommended_replace_with_candidate` 的 5 行 EPS 记录执行安全写入。

写入规则：

1. `metric_name` 必须为 `EPS` 或 `每股收益`。
2. `year` 必须完全匹配 Stage 5W 报告中的 year label。
3. `value` 必须使用 Stage 5W 证据链确认的 candidate value。
4. 写入前如果生产 06 已有相同 key：
   - 如果 value 相同但 unit 为 `ratio` / `元` / 其他非标准单位，则仅允许将单位归一为 `元/股`。
   - 如果 value 不同，立即停止并生成 blocker，不得覆盖。
5. 写入前如果生产 06 不存在对应 key：
   - 可以新增该 EPS 记录。
   - unit 使用 `元/股`。
6. 不允许写入 `ratio`。
7. 不允许写入空单位。
8. 不允许改变非 EPS 行。

## 预期结果

1. EPS 5 行成功写入或单位归一。
2. production 06 行数变化要根据实际情况判断：
   - 如果是更新已有 5 行单位，行数应保持 `114`。
   - 如果是新增之前跳过的 5 行，行数应从 `114` 增加到 `119`。
   - 必须在报告中明确说明实际是哪一种。
3. `duplicate_key_count=0`。
4. `value_mismatch_count=0`。
5. EPS 范围内 `unit_conflict_count=0`。
6. `year_conflict_count=0`。
7. production 01/02/02A/05 unchanged。
8. official 02B unchanged。
9. formal rules unchanged，除非本轮只生成 rules recommendation 文件。
10. `check_delivery_state.py --json` 最终 `overall_status=PASS`。
11. `rollback_possible=true`。

## 新增输出

生成 Stage 5X apply summary：

`174_stage5x_eps_unit_apply_summary.json`

如果编号已占用，则使用下一个连续编号。

JSON 至少包含：

```json
{
  "stage": "stage5x_eps_unit_apply",
  "mode": "real_apply_limited_scope",
  "based_on_stage5w_commit": "dd533f9e2e3eb6e5e3385de0701574a71a13ea10",
  "stage5w_summary_file": "173_stage5w_eps_unit_conflict_summary.json",
  "target_metric_scope": ["EPS", "每股收益"],
  "target_conflict_count": 5,
  "applied_count": 0,
  "updated_existing_count": 0,
  "inserted_new_count": 0,
  "skipped_count": 0,
  "blocker_count": 0,
  "recommended_unit": "元/股",
  "formal_rules_modified": false,
  "official_02b_modified": false,
  "production_01_unchanged": true,
  "production_02_unchanged": true,
  "production_02a_unchanged": true,
  "production_05_unchanged": true,
  "production_06_modified": true,
  "production_06_row_count_before": 114,
  "production_06_row_count_after": null,
  "eps_rows": [
    {
      "metric_name": "",
      "year": "",
      "value": "",
      "unit_before": "",
      "unit_after": "元/股",
      "action": "",
      "value_same": true,
      "source_evidence": [],
      "status": ""
    }
  ],
  "post_apply_checks": {
    "duplicate_key_count": 0,
    "value_mismatch_count": 0,
    "unit_conflict_count": 0,
    "year_conflict_count": 0,
    "eps_unit_conflict_remaining_count": 0,
    "check_delivery_state_overall_status": "PASS",
    "rollback_possible": true
  }
}
```

同时生成 Markdown 报告：

`174_stage5x_eps_unit_apply_report.md`

内容包括：

1. 本轮范围
2. Stage 5W 依据
3. EPS 5 行 apply 明细
4. 行数变化说明
5. 单位从什么变成什么
6. 为什么统一为 `元/股`
7. 是否修改 formal rules
8. 验证结果
9. 下一步建议

## 安全验证

执行完成后必须运行：

1. `git diff --stat`
2. `git diff`
3. `check_delivery_state.py --json`
4. 检查 production 01/02/02A/05 unchanged
5. 检查 official 02B unchanged
6. 检查 formal rules unchanged
7. 检查 production 06 仅 EPS 5 行发生变化
8. 检查 duplicate/value/unit/year conflict
9. 检查 `rollback_possible=true`

## 提交要求

如果验证通过，可以提交。

commit message 建议：

```text
stage5x: apply reviewed eps unit normalization
```

本轮提交只允许包含：

- Stage 5X apply 脚本
- 更新后的生产 06 文件
- `174_stage5x_eps_unit_apply_summary.json`
- `174_stage5x_eps_unit_apply_report.md`
- 必要的审计输出文件

禁止提交：

- production 01
- production 02
- production 02A
- production 05
- official 02B
- formal rules
- 历史遗留未提交文件 `tools/update_stage5v_production_06_safe_rows.py`，除非确认它是本轮脚本且确实被使用

## 最终回复必须包含

1. commit hash
2. push 状态
3. production 06 行数 before / after
4. EPS `applied_count`
5. `updated_existing_count` / `inserted_new_count`
6. EPS 最终单位
7. `formal_rules_modified` 是否为 `false`
8. `check_delivery_state.py --json` 结果
9. duplicate/value/unit/year conflict 检查结果
10. git diff 范围确认
11. 是否 `ready_for_next_stage`

## 简易提示词

```text
项目：D:\_datefac
执行 Stage 5X：只 apply Stage 5W 审查通过的 EPS / 每股收益 5 行单位冲突。
依据 173_stage5w_eps_unit_conflict_summary.json：5 行 value_same=true，value_mismatch=0，ready_for_stage5x_eps_apply=true。
只处理 EPS/每股收益，不处理其他指标。
最终单位统一为 元/股。
允许修改生产 06；禁止修改 01/02/02A/05、official 02B、formal rules。
如果 06 已有相同 key 且 value 相同，只归一单位为 元/股；如果 value 不同，立刻停止并生成 blocker；如果 key 不存在，可以新增。
年份标签必须以 Stage 5W 报告为准，尤其不要把 2025A 擅自改成 2025E。
完成后生成 174_stage5x_eps_unit_apply_summary.json 和 174_stage5x_eps_unit_apply_report.md。
运行 git diff、check_delivery_state.py --json，并确认 duplicate/value/unit/year conflict 为 0，overall_status=PASS，rollback_possible=true。
提交时不要纳入历史未提交文件 tools/update_stage5v_production_06_safe_rows.py。
最终回复 commit hash、push 状态、06 行数 before/after、applied_count、updated/inserted count、EPS 最终单位、formal_rules_modified=false、检查结果、是否 ready_for_next_stage。
```
