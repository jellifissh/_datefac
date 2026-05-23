# Stage 5S - Real apply production 02/05 from final apply plan

项目：`D:\_datefac`

## 当前状态

Stage 5R 已完成最终 apply plan，且未修改生产文件。

Stage 5R 关键结果：

- commit: `47708bcbf73a7f5cfc9bd6539ab9bf3cf20e5759`
- `check_delivery_state.py --json => overall_status=PASS`
- `production_02_reference_file=D:\_datefac\output\H3_AP202605121822223662_1_资产包\02_研报全量结构化数据.xlsx`
- `production_05_reference_file=D:\_datefac\output\H3_AP202605121822223662_1_资产包\05_核心财务指标标准化.xlsx`
- `promote_to_02_metric_count=59`
- `promote_to_02_row_count=295`
- `promote_to_05_metric_count=9`
- `promote_to_05_row_count=45`
- `excluded_need_mapping_metric_count=4`
- `excluded_need_scope_review_metric_count=4`
- `blocked_metric_count=0`
- `rollback_plan_generated=true`
- `apply_manifest_generated=true`
- `ready_for_stage5s_real_apply=true`
- `production_files_unchanged=true`
- `formal_rules_unchanged=true`
- `stage5r_apply_plan_pass=true`

被排除的 review 项：

- `NEED_MAPPING_RULE`: `每股净资产(最新摊薄)`、`每股经营现金流(最新摊薄)`、`流动比率`、`速动比率`
- `NEED_SCOPE_REVIEW`: `净利润`、`营业利润`、`EBITDA`

## 下一任务

Stage 5S - Execute real apply to production 02/05 using Stage 5R manifest.

这一步会真实修改生产资产包中的：

- `output/H3_AP202605121822223662_1_资产包/02_研报全量结构化数据.xlsx`
- `output/H3_AP202605121822223662_1_资产包/05_核心财务指标标准化.xlsx`

## 核心目标

1. 严格按 Stage 5R apply manifest 执行 real apply。
2. 只写入 Stage 5R 允许的记录：
   - 02: 59 个指标 / 295 行
   - 05: 9 个指标 / 45 行
3. 排除所有 `NEED_MAPPING_RULE` 和 `NEED_SCOPE_REVIEW` 项。
4. apply 前必须备份生产 02/05。
5. apply 后必须做 hash guard、row count、duplicate/conflict 校验。
6. 生成 rollback 信息。
7. 修改范围仅限 production 02/05 和本轮脚本/文档，不修改正式规则，不修改 01/02A/06/02B override。

## 严格约束

1. 不调用外部 AI。
2. 不联网。
3. 不运行 `factory_core.py`。
4. 不触发 OCR / vision / marker / surya / PaddleOCR。
5. 不修改 `01 / 02A / 06`。
6. 不修改 `data/overrides/02B_ai_repair_override.xlsx`。
7. 不修改正式 mapping / scope / normalization / alias 规则文件。
8. 不提交临时 `output/stage5s_real_apply/*` 报告文件，除非项目已有约定要求提交。
9. 只允许真实修改以下两个生产文件：
   - `output/H3_AP202605121822223662_1_资产包/02_研报全量结构化数据.xlsx`
   - `output/H3_AP202605121822223662_1_资产包/05_核心财务指标标准化.xlsx`
10. 必须保留 backup 文件到 `output/stage5s_real_apply/backup/`，但默认不提交 backup。

## 输入

- `output/stage5r_final_apply_plan/160_stage5r_apply_manifest.xlsx`
- `output/stage5r_final_apply_plan/160_stage5r_apply_risk_review.xlsx`
- `output/stage5r_final_apply_plan/160_stage5r_backup_rollback_plan.md`
- `output/stage5r_final_apply_plan/161_stage5r_final_apply_plan_summary.json`
- `output/stage5o_promotion_review/154_stage5o_candidate_02.xlsx`
- `output/stage5o_promotion_review/154_stage5o_candidate_05.xlsx`
- production 02:
  - `output/H3_AP202605121822223662_1_资产包/02_研报全量结构化数据.xlsx`
- production 05:
  - `output/H3_AP202605121822223662_1_资产包/05_核心财务指标标准化.xlsx`

## apply 规则

### 1. Apply 前置检查

必须确认：

- `ready_for_stage5s_real_apply=true`
- `blocked_metric_count=0`
- Stage 5R manifest 存在
- production 02/05 存在
- production 02/05 hash before 与 Stage 5R summary 中记录一致，或如果 Stage 5R 未记录完整 hash，则本轮重新计算并写入 summary
- 当前 git working tree 没有未解释的生产文件改动

### 2. 02 写入规则

只允许写入 Stage 5R manifest 中标记为 02 apply 的记录：

- `PROMOTE_TO_02_ONLY`
- 以及 `PROMOTE_TO_05_SAFE` 对应的 02 层记录

必须排除：

- `NEED_MAPPING_RULE`
- `NEED_SCOPE_REVIEW`
- `DEFER_DERIVED_METRIC`
- `FILTER_NON_CORE`
- `BLOCKED`

写入后检查：

- 新增行数应等于 `promote_to_02_row_count=295`，除非 manifest 明确部分记录已存在且去重跳过
- 不允许 duplicate key
- 不允许 value conflict
- 不允许 unit conflict
- 不允许 year conflict
- 必须保留 source/provenance 字段

### 3. 05 写入规则

只允许写入 Stage 5R manifest 中 `PROMOTE_TO_05_SAFE` 对应记录：

- 9 个指标
- 45 行

必须排除：

- `NEED_MAPPING_RULE`
- `NEED_SCOPE_REVIEW`
- `DEFER_DERIVED_METRIC`
- `FILTER_NON_CORE`
- `BLOCKED`

写入后检查：

- 新增行数应等于 `promote_to_05_row_count=45`，除非 manifest 明确部分记录已存在且去重跳过
- 不允许 duplicate key
- 不允许 value conflict
- 不允许 unit conflict
- 不允许 year conflict
- 标准指标字段必须完整

### 4. 备份与回滚

apply 前必须备份：

- `output/stage5s_real_apply/backup/02_研报全量结构化数据.before_stage5s.xlsx`
- `output/stage5s_real_apply/backup/05_核心财务指标标准化.before_stage5s.xlsx`

summary 中必须写入：

- backup 文件路径
- backup hash
- production hash before
- production hash after
- rollback possible

## 输出文件

生成到：

- `output/stage5s_real_apply/162_stage5s_apply_log.xlsx`
- `output/stage5s_real_apply/162_stage5s_apply_diff.xlsx`
- `output/stage5s_real_apply/162_stage5s_apply_report.md`
- `output/stage5s_real_apply/163_stage5s_real_apply_summary.json`
- backup files under `output/stage5s_real_apply/backup/`

## summary.json 至少包含

- `production_02_file`
- `production_05_file`
- `production_02_hash_before`
- `production_05_hash_before`
- `production_02_backup_file`
- `production_05_backup_file`
- `production_02_backup_hash`
- `production_05_backup_hash`
- `production_02_hash_after`
- `production_05_hash_after`
- `manifest_promote_to_02_metric_count`
- `manifest_promote_to_02_row_count`
- `manifest_promote_to_05_metric_count`
- `manifest_promote_to_05_row_count`
- `applied_to_02_metric_count`
- `applied_to_02_row_count`
- `applied_to_05_metric_count`
- `applied_to_05_row_count`
- `skipped_existing_02_row_count`
- `skipped_existing_05_row_count`
- `excluded_need_mapping_metric_count`
- `excluded_need_scope_review_metric_count`
- `blocked_metric_count`
- `duplicate_key_count_02`
- `duplicate_key_count_05`
- `value_conflict_count_02`
- `value_conflict_count_05`
- `unit_conflict_count_02`
- `unit_conflict_count_05`
- `year_conflict_count_02`
- `year_conflict_count_05`
- `production_02_changed`
- `production_05_changed`
- `production_01_unchanged`
- `production_02A_unchanged`
- `production_06_unchanged`
- `official_02B_unchanged`
- `formal_rules_unchanged`
- `rollback_possible`
- `check_delivery_state_after`
- `stage5s_real_apply_pass`

## pass 判定

- `applied_to_02_metric_count=59`
- `applied_to_02_row_count=295`，除非有 `skipped_existing_02_row_count` 且解释清楚
- `applied_to_05_metric_count=9`
- `applied_to_05_row_count=45`，除非有 `skipped_existing_05_row_count` 且解释清楚
- `excluded_need_mapping_metric_count=4`
- `excluded_need_scope_review_metric_count=4`
- `blocked_metric_count=0`
- `duplicate_key_count_02=0`
- `duplicate_key_count_05=0`
- `value_conflict_count_02=0`
- `value_conflict_count_05=0`
- `unit_conflict_count_02=0`
- `unit_conflict_count_05=0`
- `year_conflict_count_02=0`
- `year_conflict_count_05=0`
- `production_02_changed=true`
- `production_05_changed=true`
- `production_01_unchanged=true`
- `production_02A_unchanged=true`
- `production_06_unchanged=true`
- `official_02B_unchanged=true`
- `formal_rules_unchanged=true`
- `rollback_possible=true`
- `check_delivery_state_after=PASS`
- `stage5s_real_apply_pass=true`

## 完成后

1. 运行 `python tools/check_delivery_state.py --json`。
2. 确认 `overall_status=PASS`。
3. 检查 `git status`。
4. 只提交：
   - `tools/apply_stage5s_real_apply_production_02_05.py`
   - 可选：`docs/stage5s_real_apply_production_02_05.md`
   - 修改后的生产 02/05 文件，如果它们是 repo tracked production files
5. 不提交 `output/stage5s_real_apply/*` 报告/backup，除非仓库现有规范要求。
6. commit message:
   - `stage5s: apply clean wide candidates to production 02 and 05`
7. `git push origin main`

## 如果发生 blocker

如果 apply 前 hash 不匹配、manifest 不完整、production 文件缺失、写入后出现重复/冲突、或非目标生产文件被修改，必须立即停止并使用 backup 回滚，不得提交修改后的生产文件。