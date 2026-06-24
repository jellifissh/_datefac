# 348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation

## Task Goal

Implement the R7R design as an R7S implementation task.

Add a conservative deterministic clean-admission guard so that weak-evidence strict-table rows that look like pseudo-header, comparison-dimension, or table-scaffolding rows do not enter `clean_data`.

Rows currently typed as `STRICT_FINANCIAL_TABLE_ROW` with `WEAK_EVIDENCE` may still be useful for review, but should not become `INTERNAL_CLEAN_CANDIDATE` when their content is only table structure rather than a stable financial fact.

The expected routing for matched rows is `REVIEW_REQUIRED`.

Keep row typing unchanged. Do not create a new row type.

## Background

Read these first:

```text
AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
```

R7Q confirmed that the previous market-reference clean-data leak is fixed. `收盘价` and `总市值` now remain in review. R7Q also confirmed no logical/physical row-count mismatch, no forbidden clean row type, and no Taihao qualitative_facts-like schema.

R7R recommended a narrower clean-candidate policy, not a new row type.

Key R7Q numbers:

```text
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true
```

Observed risky labels include:

```text
市场数据
厂商
对比维度
订单日期
项目
指标
```

Examples of suspicious non-fact period values include:

```text
数值 / 基础数据 / 数值
型号 / 最大功率 / 排量 / 缸型
中速燃气内燃机 / 重型或航改型燃气轮机
季度 / 项目地点 / 容量 / 发动机型号 / 数量 / 用途
2025A / 2026E / 2027E / 2028E as echoed period labels for rows such as 项目 or 指标
```

## Allowed Scope

Allowed implementation file:

```text
datefac_agent/review/clean_candidate_policy.py
```

Allowed test scope:

```text
tests/
```

Only change tests directly related to R7S strict-table pseudo-header / comparison-row clean-boundary behavior.

## Forbidden Actions

Do not modify docs, skills, input, output, temp, data, legacy datefac, dependencies, config files, or readiness gates.

Do not modify `datefac_agent/audit/row_type_classifier.py` unless you stop first and explain why the policy file alone cannot solve the task.

Do not modify `datefac_agent/review/output_schema_guardrails.py`.

Do not run MinerU, OCR, LLM, VLM, a new extraction pipeline, or a new workbook pilot.

Do not broaden qualitative_facts admission. Do not change MARKET_REFERENCE_ROW policy. Do not mark the project client-ready or production-ready.

Do not stage, commit, or push in this task. Do not use broad Git staging or destructive cleanup commands.

## Implementation Requirements

Implement a small deterministic helper or branch inside `clean_candidate_policy.py`.

The guard should apply only when all conditions are true:

```text
row_type == STRICT_FINANCIAL_TABLE_ROW
evidence_level == WEAK_EVIDENCE
the row would otherwise become INTERNAL_CLEAN_CANDIDATE
metric text and/or period_values indicate pseudo-header, comparison-dimension, or scaffolding content
```

When matched, return `REVIEW_REQUIRED`.

Use deterministic signals only. Do not rely on LLM judgment.

Prefer a conservative rule combining metric text and period value shape, so normal numeric financial rows remain eligible for clean admission under the existing policy.

Normal rows such as `营业总收入`, `归母净利润`, `EPS`, `P/E`, `ROE`, `毛利率`, `收入同比`, and `净利润同比` should preserve existing behavior when period values are numeric financial values.

## Test Requirements

Add compact tests covering:

1. `市场数据` with non-numeric period values returns `REVIEW_REQUIRED`.
2. `厂商` with non-numeric period values returns `REVIEW_REQUIRED`.
3. `对比维度` with non-numeric period values returns `REVIEW_REQUIRED`.
4. `项目` or `指标` with echoed period labels such as `2025A / 2026E / 2027E / 2028E` returns `REVIEW_REQUIRED`.
5. A normal financial row with numeric period values preserves existing clean admission behavior.
6. Existing MARKET_REFERENCE_ROW behavior remains unchanged.
7. Existing qualitative_facts behavior remains unchanged.

Prefer extending existing clean-candidate policy tests.

## Validation Commands

Run and report:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
pytest tests -q
git diff --check
git status -sb
git diff --stat
git diff --name-only
```

If full tests fail due to an unrelated historical issue, explain why and run the smallest relevant test file as a fallback. Do not skip tests.

## Expected Output

Report:

1. Preflight: `git status -sb`, `git log --oneline -5`.
2. Files modified.
3. Implementation summary.
4. Tests added or modified.
5. Validation outputs.
6. Whether MARKET_REFERENCE_ROW policy changed.
7. Whether qualitative_facts admission changed.
8. Whether output_schema_guardrails changed.
9. Whether output/input/temp/data/legacy were modified.
10. Whether readiness gates remain closed.
11. Whether forbidden files were modified.
12. Remaining risks.
13. Whether human review is recommended.
14. Whether commit/push is recommended after review.
15. Whether follow-up R7S-QA or Taihao rerun is recommended.

Final summary:

```text
Data Result / 数据结果

Decision（任务结论）=
build_result（构建结果）=
test_result（测试结果）=
files_modified（修改文件数）=
error_count（错误数）=
boundary_check（边界检查）=
policy_result（策略结果）=
recommended_next_task（推荐下一任务）=
```

Stop after the report. No staging, commit, or push.
