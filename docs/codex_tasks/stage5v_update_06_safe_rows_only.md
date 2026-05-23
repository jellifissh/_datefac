# Stage 5V - Update production 06 with safe rows only

项目：`D:\_datefac`

## 当前状态

Stage 5U 已完成 06 dry-run 冲突审查。

关键结果：

- commit: `899332b057bd571541415749a9c42acaf991c628`
- `check_delivery_state.py --json => overall_status=PASS`
- `input_dry_run_06_new_row_count=40`
- `input_dry_run_06_conflict_count=5`
- `conflict_key_count=5`
- `safe_to_add_06_row_count=40`
- `conflict_same_value_count=0`
- `conflict_value_mismatch_count=0`
- `conflict_unit_mismatch_count=5`
- `blocked_conflict_count=5`
- `ready_for_stage5v_update_06_safe_rows=true`
- `production_06_unchanged=true`
- `formal_rules_unchanged=true`
- `stage5u_06_conflict_review_pass=true`

5 个 blocked conflict keys 均为 `每股收益` 的 2024A/2025A/2026E/2027E/2028E，冲突类型为单位口径冲突：`元` vs `ratio` 来源。

## 下一任务

Stage 5V - Real update production 06 with only the 40 safe rows from Stage 5U.

## 核心目标

1. 只将 Stage 5U `SAFE_TO_ADD_TO_06` 的 40 行写入生产 `06_最终核心财务指标.xlsx`。
2. 5 个 `每股收益` 单位冲突行必须继续 blocked，不得写入 06。
3. apply 前备份生产 06。
4. apply 后做 hash guard、row count、duplicate/conflict 校验。
5. 不修改生产 01/02/02A/05、02B override、正式规则。

## 严格约束

1. 不调用外部 AI。
2. 不联网。
3. 不运行 `factory_core.py`。
4. 不触发 OCR / vision / marker / surya / PaddleOCR。
5. 不修改生产 `01 / 02 / 02A / 05`。
6. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
7. 不修改正式 mapping / scope / normalization / alias 规则文件。
8. 只允许真实修改 `06_最终核心财务指标.xlsx`。
9. 不提交 `output/stage5v_update_06_safe_rows/*` 报告和 backup，除非仓库规范明确要求。
10. 如果发现 safe manifest 包含 blocked EPS conflict 行，必须停止，不得 apply。

## 输入

- `output/stage5u_06_conflict_review/166_stage5u_06_safe_update_manifest.xlsx`
- `output/stage5u_06_conflict_review/166_stage5u_06_conflict_review.xlsx`
- `output/stage5u_06_conflict_review/167_stage5u_06_conflict_review_summary.json`
- production 06: `06_最终核心财务指标.xlsx`

## apply 规则

### 写入规则

只允许写入 `166_stage5u_06_safe_update_manifest.xlsx` 中明确标记为 `SAFE_TO_ADD_TO_06` 的记录。

必须排除：

- 所有 `BLOCKED_NEED_MANUAL_REVIEW`
- 所有 `每股收益` 2024A/2025A/2026E/2027E/2028E 冲突行
- 所有单位冲突、值冲突、年份冲突、来源优先级不清楚的记录

### 校验规则

apply 后必须确认：

- production 06 原始行保留
- 新增 40 行
- 06 row count 从 79 增加到 119，除非 manifest 中存在已存在记录并有清楚 skipped 说明
- duplicate key count = 0
- value conflict count = 0
- unit conflict count = 0
- year conflict count = 0
- blocked EPS conflict rows written count = 0
- production 01/02/02A/05 unchanged
- official 02B unchanged
- formal rules unchanged
- rollback possible = true
- `check_delivery_state.py --json => overall_status=PASS`

## 输出文件

生成到：

- `output/stage5v_update_06_safe_rows/168_stage5v_update_06_log.xlsx`
- `output/stage5v_update_06_safe_rows/168_stage5v_update_06_diff.xlsx`
- `output/stage5v_update_06_safe_rows/168_stage5v_update_06_report.md`
- `output/stage5v_update_06_safe_rows/169_stage5v_update_06_summary.json`
- backup under `output/stage5v_update_06_safe_rows/backup/`

## summary.json 至少包含

- `production_06_file`
- `production_06_hash_before`
- `production_06_backup_file`
- `production_06_backup_hash`
- `production_06_hash_after`
- `input_safe_to_add_06_row_count`
- `applied_to_06_row_count`
- `skipped_existing_06_row_count`
- `blocked_conflict_input_count`
- `blocked_conflict_written_count`
- `eps_unit_conflict_written_count`
- `production_06_row_count_before`
- `production_06_row_count_after`
- `expected_06_row_count_after`
- `duplicate_key_count_06`
- `value_conflict_count_06`
- `unit_conflict_count_06`
- `year_conflict_count_06`
- `production_06_changed`
- `production_01_unchanged`
- `production_02_unchanged`
- `production_02A_unchanged`
- `production_05_unchanged`
- `official_02B_unchanged`
- `formal_rules_unchanged`
- `rollback_possible`
- `check_delivery_state_after`
- `stage5v_update_06_safe_rows_pass`

## pass 判定

- `input_safe_to_add_06_row_count=40`
- `applied_to_06_row_count=40`，除非存在 `skipped_existing_06_row_count` 且解释清楚
- `blocked_conflict_written_count=0`
- `eps_unit_conflict_written_count=0`
- `production_06_row_count_before=79`
- `production_06_row_count_after=119`，除非有 skipped existing 且解释清楚
- `duplicate_key_count_06=0`
- `value_conflict_count_06=0`
- `unit_conflict_count_06=0`
- `year_conflict_count_06=0`
- `production_06_changed=true`
- `production_01_unchanged=true`
- `production_02_unchanged=true`
- `production_02A_unchanged=true`
- `production_05_unchanged=true`
- `official_02B_unchanged=true`
- `formal_rules_unchanged=true`
- `rollback_possible=true`
- `check_delivery_state_after=PASS`
- `stage5v_update_06_safe_rows_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`。
4. 只提交：
   - `tools/update_stage5v_production_06_safe_rows.py`
   - 修改后的 `06_最终核心财务指标.xlsx`
   - 可选 docs
5. 不提交 `output/stage5v_update_06_safe_rows/*` 报告/backup，除非仓库规范明确要求。
6. commit message: `stage5v: update production 06 with safe rows`
7. `git push origin main`

## 如果发生 blocker

如果 safe manifest 不等于 40 行、包含 EPS blocked conflict、写入后出现 duplicate/conflict、或非目标生产文件被修改，必须立即停止并使用 backup 回滚，不得提交修改后的 06。