# Stage 5V2 - Update production 06 with safe rows excluding EPS conflicts

项目：`D:\_datefac`

## 当前状态

Stage 5V 在 apply 前校验阶段触发硬阻塞，已正确停止，未修改生产 `06_最终核心财务指标.xlsx`。

阻塞原因：

- `SAFE_TO_ADD_TO_06` 输入共 40 行
- `BLOCKED_NEED_MANUAL_REVIEW` 共 5 行
- 两者存在 5 行重叠，全部为 `每股收益` / EPS 冲突键
- 冲突类型：单位口径冲突，`元` vs `ratio`
- 根据 Stage 5V 文档约束：safe manifest 包含 blocked EPS conflict 行时必须停止，不得 apply

当前结论：

- 生产 06 仍为 79 行，未改动
- `check_delivery_state.py --json => overall_status=PASS`
- safe_minus_blocked = 35
- 下一步应先修正 safe manifest，将 5 个 EPS 冲突行从 safe apply 中剔除，只写入剩余 35 行安全记录

## 下一任务

Stage 5V2 - Regenerate safe 06 apply manifest excluding EPS conflicts, then real update production 06 with only 35 safe rows.

## 核心目标

1. 从 Stage 5U / Stage 5V 输入中重新生成 corrected safe manifest。
2. 明确剔除 5 个 EPS / 每股收益单位冲突行。
3. 仅将剩余 35 行 `SAFE_TO_ADD_TO_06` 写入生产 `06_最终核心财务指标.xlsx`。
4. apply 前备份生产 06。
5. apply 后执行 hash guard、row count、duplicate/conflict 校验。
6. 不修改生产 01/02/02A/05，不修改正式规则，不修改 02B override。

## 必须排除的 5 个冲突键

- `H3_AP202605121822223662_1||D:\_datefac\input\H3_AP202605121822223662_1.pdf||每股收益||2024A`
- `H3_AP202605121822223662_1||D:\_datefac\input\H3_AP202605121822223662_1.pdf||每股收益||2025A`
- `H3_AP202605121822223662_1||D:\_datefac\input\H3_AP202605121822223662_1.pdf||每股收益||2026E`
- `H3_AP202605121822223662_1||D:\_datefac\input\H3_AP202605121822223662_1.pdf||每股收益||2027E`
- `H3_AP202605121822223662_1||D:\_datefac\input\H3_AP202605121822223662_1.pdf||每股收益||2028E`

## 严格约束

1. 不调用外部 AI。
2. 不联网。
3. 不运行 `factory_core.py`。
4. 不触发 OCR / vision / marker / surya / PaddleOCR。
5. 不修改生产 `01 / 02 / 02A / 05`。
6. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
7. 不修改正式 mapping / scope / normalization / alias 规则文件。
8. 只允许真实修改 `06_最终核心财务指标.xlsx`。
9. 不提交 `output/stage5v2_update_06_safe_rows_excluding_eps/*` 报告和 backup，除非仓库规范明确要求。
10. 如果 corrected safe manifest 仍包含 EPS / 每股收益冲突行，必须停止，不得 apply。

## 输入

- `output/stage5u_06_conflict_review/166_stage5u_06_safe_update_manifest.xlsx`
- `output/stage5u_06_conflict_review/166_stage5u_06_conflict_review.xlsx`
- `output/stage5u_06_conflict_review/167_stage5u_06_conflict_review_summary.json`
- Stage 5V precheck 产生的本地阻塞信息，如存在
- production 06: `06_最终核心财务指标.xlsx`

## apply 规则

### 1. corrected safe manifest

生成 corrected safe manifest 时：

- 从 Stage 5U safe manifest 中移除所有 `每股收益` / EPS 冲突行
- 移除所有 `BLOCKED_NEED_MANUAL_REVIEW`
- 移除所有单位冲突、值冲突、年份冲突、来源优先级不清楚的记录
- corrected safe manifest 应为 35 行

### 2. 写入 06

只允许写入 corrected safe manifest 中的 35 行。

写入后检查：

- 生产 06 原始 79 行保留
- 新增 35 行
- 06 row count 从 79 增加到 114
- duplicate key count = 0
- value conflict count = 0
- unit conflict count = 0
- year conflict count = 0
- EPS conflict rows written count = 0
- blocked conflict written count = 0
- production 01/02/02A/05 unchanged
- official 02B unchanged
- formal rules unchanged
- rollback possible = true
- `check_delivery_state.py --json => overall_status=PASS`

## 输出文件

生成到：

- `output/stage5v2_update_06_safe_rows_excluding_eps/170_stage5v2_corrected_safe_manifest.xlsx`
- `output/stage5v2_update_06_safe_rows_excluding_eps/170_stage5v2_update_06_log.xlsx`
- `output/stage5v2_update_06_safe_rows_excluding_eps/170_stage5v2_update_06_diff.xlsx`
- `output/stage5v2_update_06_safe_rows_excluding_eps/170_stage5v2_update_06_report.md`
- `output/stage5v2_update_06_safe_rows_excluding_eps/171_stage5v2_update_06_summary.json`
- backup under `output/stage5v2_update_06_safe_rows_excluding_eps/backup/`

## summary.json 至少包含

- `production_06_file`
- `production_06_hash_before`
- `production_06_backup_file`
- `production_06_backup_hash`
- `production_06_hash_after`
- `input_safe_to_add_06_row_count`
- `input_blocked_conflict_count`
- `safe_blocked_overlap_count`
- `eps_conflict_excluded_count`
- `corrected_safe_manifest_row_count`
- `applied_to_06_row_count`
- `skipped_existing_06_row_count`
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
- `stage5v2_update_06_safe_rows_pass`

## pass 判定

- `input_safe_to_add_06_row_count=40`
- `input_blocked_conflict_count=5`
- `safe_blocked_overlap_count=5`
- `eps_conflict_excluded_count=5`
- `corrected_safe_manifest_row_count=35`
- `applied_to_06_row_count=35`，除非存在 `skipped_existing_06_row_count` 且解释清楚
- `blocked_conflict_written_count=0`
- `eps_unit_conflict_written_count=0`
- `production_06_row_count_before=79`
- `production_06_row_count_after=114`，除非有 skipped existing 且解释清楚
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
- `stage5v2_update_06_safe_rows_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`。
4. 只提交：
   - `tools/update_stage5v2_production_06_safe_rows_excluding_eps.py`
   - 修改后的 `06_最终核心财务指标.xlsx`
   - 可选 docs
5. 不提交 `output/stage5v2_update_06_safe_rows_excluding_eps/*` 报告/backup，除非仓库规范明确要求。
6. commit message: `stage5v2: update production 06 excluding EPS conflicts`
7. `git push origin main`

## 如果发生 blocker

如果 corrected safe manifest 不等于 35 行、仍包含 EPS conflict、写入后出现 duplicate/conflict、或非目标生产文件被修改，必须立即停止并使用 backup 回滚，不得提交修改后的 06。