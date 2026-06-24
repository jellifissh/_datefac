348N-R7R strict_table pseudo-header / comparison-row clean-boundary design

Task ID

348N-R7R strict_table pseudo-header / comparison-row clean-boundary design

Task Type

review / diagnosis / policy design only

This task is a design task.

It is not an implementation task.

Do not modify code unless a later task explicitly changes the scope from design to implementation.

Do not run a new pipeline.

Do not run MinerU, OCR, LLM, or VLM.

Do not commit output artifacts.

---

Background

The current branch is:

pivot/348-agent-foundation

The current workspace is:

D:\_datefac_agent

The current DateFac Agent pipeline has been moving through:

intake -> audit -> review -> delivery

The active package is:

datefac_agent/

The project is still conservative by design:

client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true

The current stage is not production delivery.

The current stage is still strict audit / review / clean-boundary design.

---

Required Read Order

Read these files before doing the task:

AGENTS.md
.skills/README.md
.skills/git_workflow.md
.skills/datefac_agent_foundation.md
.skills/agent_excel_intake_audit_workflow.md
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md
docs/agent/348N_R7P_FIX2_QA_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_REVIEW.md
docs/agent/348N_R7P_FIX2_MARKET_REFERENCE_CLEAN_DATA_ADMISSION_POLICY_ALIGNMENT_RESULT.md
docs/agent/348N_R7P_FIX_MARKET_REFERENCE_CLEAN_DATA_BOUNDARY_LEAK_INVESTIGATION.md

Allowed output artifact references are read-only.

Do not modify "output/".

---

Latest Completed Result: R7Q

R7Q reviewed another workbook family after R7P-FIX2.

R7Q report:

docs/agent/348N_R7Q_ANOTHER_WORKBOOK_FAMILY_PILOT_REVIEW.md

Input workbook:

input/泰豪科技_深度研报_核心数据提取_豆包AI生成 (1).xlsx

Source PDF:

input/H3_AP202605231822706325_1.pdf

Reviewed pilot output:

output/agent_excel_intake_audit_348n_r7p_fix2_qa_market_reference_boundary/

Key output files reviewed read-only:

agent_excel_intake_audit_348a_manifest.json
clean_data.csv
review_queue.csv
evidence_index.json

---

R7Q Manifest Summary

R7Q confirmed the following post-FIX2 Taihao pilot values:

decision = AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX
clean_data_row_count = 92
clean_data_csv_row_count = 92
review_queue_row_count = 66
review_queue_csv_row_count = 66
unknown_row_count = 0
market_reference_row_count = 2
normalized_testset_record_row_count = 0
llm_api_call_count = 0
mineru_run_count = 0
ocr_run_count = 0
client_ready = false
production_ready = false
formal_client_export_allowed = false
demo_export_only = true

Important interpretation:

AI_EXCEL_INTAKE_AUDIT_348A_NEEDS_FIX reflects review pressure.
It is not a logical/physical row-count guardrail failure.
It is not an UNKNOWN_ROW collapse.
It is not production readiness.

---

R7Q Confirmed Improvements

R7Q confirmed:

post-FIX2 Taihao pilot has no logical / physical count confusion
clean_data_row_count == clean_data_csv_row_count == 92
review_queue_row_count == review_queue_csv_row_count == 66
unknown_row_count = 0
clean_data has no forbidden row_type
MARKET_REFERENCE_ROW no longer enters clean_data

The prior R7P failure was:

MARKET_REFERENCE_ROW entered clean_data

The concrete row involved in the earlier failure was:

报告核心信息与投资要点 / 收盘价 / MARKET_REFERENCE_ROW

After R7P-FIX2 and R7P-FIX2-QA, the market reference leak is fixed.

R7Q confirms that:

收盘价
总市值

now remain in "review_queue".

---

Current Remaining Risk

R7Q found that the current remaining issue is narrower than the previous market-reference leak.

The new risk is:

STRICT_FINANCIAL_TABLE_ROW may still over-admit pseudo-header / comparison-dimension rows into clean_data.

Examples observed in R7Q clean_data:

核心盈利预测与估值,11,市场数据,...
行业赛道数据,13,厂商,...
行业赛道数据,19,对比维度,...

These rows currently appear as:

row_type = STRICT_FINANCIAL_TABLE_ROW
clean_candidate_type = INTERNAL_CLEAN_CANDIDATE
evidence_level = WEAK_EVIDENCE

The question is whether they are truly clean financial facts, or whether they are table scaffolding / pseudo-header / comparison-dimension rows that should stay out of clean_data.

---

Non-Goal: qualitative_facts

R7Q did not find a second "qualitative_facts"-like facts schema in the Taihao workbook family.

R7Q observed:

facts_like_schema_found = no
qualitative_facts_like_rows = no dedicated qualitative_facts-like sheet observed

Therefore, this task must not broaden "qualitative_facts" clean admission.

Do not reopen broad "qualitative_facts" clean-admission policy from this workbook family.

This R7R task is about strict-table pseudo-header / comparison-row boundaries only.

---

Task Goal

Design the next clean-boundary policy direction for rows currently classified as:

STRICT_FINANCIAL_TABLE_ROW
INTERNAL_CLEAN_CANDIDATE
WEAK_EVIDENCE

when those rows look like:

pseudo-header rows
section label rows
comparison-dimension rows
table scaffolding rows

The goal is to decide whether these rows should continue entering "clean_data", or whether they should be redirected to "review_queue".

---

Required Design Questions

Answer all of the following:

1. Classification Question

Should rows like the following remain classified as "STRICT_FINANCIAL_TABLE_ROW"?

市场数据
厂商
对比维度

If yes, explain why.

If no, propose a narrower classification or a new row type.

Possible options include:

STRICT_TABLE_PSEUDO_HEADER_ROW
STRICT_TABLE_COMPARISON_DIMENSION_ROW
STRUCTURED_TABLE_SCAFFOLDING_ROW
REVIEW_REQUIRED

Do not introduce a new row type casually. Explain whether a new row type is actually necessary.

---

2. Clean Admission Question

Should these rows remain in "clean_data"?

Answer conservatively.

The project principle is:

宁可进 review，不轻易进 clean。

If a row does not represent a stable financial fact, it should not become clean_data merely because it appears inside a structured sheet.

---

3. Policy Question

Is the better fix:

new row_type

or:

narrower clean_candidate_policy

or:

additional review-required rule for STRICT_FINANCIAL_TABLE_ROW + weak evidence + pseudo-header-like metric text

Compare the options.

Prefer the smallest safe policy change.

---

4. Evidence Question

What signals can distinguish a true clean financial fact row from a pseudo-header / comparison-dimension row?

Consider signals such as:

metric name shape
numeric value presence
period presence
unit presence
column role
row position
sheet name
neighbor rows
value density
whether the row is a category label
whether the row describes a comparison axis rather than a metric
whether the row has enough financial fact content to be exported

Do not rely on LLM judgment.

Design should be deterministic and auditable.

---

5. Scope Question

Should the policy be general across workbook families, or limited to the Taihao workbook family?

The default should be:

general if evidence is structural
narrow if evidence is workbook-specific

Do not overfit to one workbook unless necessary.

---

6. Guardrail Question

Should this become a hard output guardrail?

For example:

clean_data must not contain pseudo-header / comparison-dimension rows

Or should it first be a policy refinement reviewed through tests?

Be careful: output guardrails should only enforce stable rules that are unlikely to block legitimate data.

---

7. Implementation Readiness Question

Should R7R recommend an implementation task?

If yes, specify the likely next task.

Possible next task:

348N-R7S strict_table pseudo-header / comparison-row clean-boundary implementation

The implementation task should be separate from this design task.

---

Allowed Scope

This task may create one result report:

docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md

This task may read existing docs and output artifacts.

This task must not modify:

AGENTS.md
.skills/
docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
docs/agent/项目进程.md
项目进展大白话说明.md
source code
tests
input/
output/
temp/
data/
legacy datefac/
dependencies
config files

This task must not create or modify output artifacts.

This task must not run a new extraction pipeline.

---

Forbidden Actions

Do not modify code.

Do not modify tests.

Do not modify dependencies.

Do not modify config files.

Do not modify "input/".

Do not modify "output/".

Do not modify "temp/".

Do not modify "data/".

Do not modify legacy "datefac/".

Do not run MinerU.

Do not run OCR.

Do not run LLM.

Do not run VLM.

Do not run a new workbook pilot.

Do not broaden "qualitative_facts" clean admission.

Do not change "MARKET_REFERENCE_ROW" policy.

Do not change output guardrails.

Do not mark the project client-ready.

Do not mark the project production-ready.

Do not allow formal client export.

Do not use:

git add .
git add -A
git reset --hard

---

Expected Result Report

Create:

docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md

The report must include:

Task ID
Input context
Files reviewed
R7Q recap
Problem statement
Observed risky rows
Policy options
Recommended option
Rationale
Whether new row_type is needed
Whether clean_candidate_policy should change
Whether output guardrails should change
Whether tests are required in a later implementation task
Whether rerun is required in a later task
Readiness gates
Forbidden actions respected
Boundary check
Data Result / 数据结果
Recommended next task

The "Data Result / 数据结果" section must include:

Decision（任务结论）=
design_result（设计结果）=
implementation_required（是否需要实现）=
test_required_later（后续是否需要测试）=
output_rerun_required_later（后续是否需要重跑 output）=
readiness_gates（就绪门）=
code_changes_made（是否改代码）=
test_changes_made（是否改测试）=
output_files_modified（是否修改 output）=
recommended_next_task（推荐下一任务）=

---

Expected Decision Style

The decision should be conservative.

Preferred conclusion shape:

Pseudo-header / comparison-dimension rows should not enter clean_data unless they carry a direct financial fact with sufficient metric/value/period/unit structure.
Rows like 市场数据 / 厂商 / 对比维度 should probably become REVIEW_REQUIRED or be excluded from clean admission under a narrower STRICT_FINANCIAL_TABLE_ROW policy.

Do not force this exact answer if evidence contradicts it, but any less conservative recommendation must be justified.

---

Validation Commands

After creating the result report, run:

git status -sb
git diff -- docs/agent/348N_R7R_STRICT_TABLE_PSEUDO_HEADER_COMPARISON_ROW_CLEAN_BOUNDARY_DESIGN.md
git diff --stat
git diff --name-only
git diff --check

Do not run pytest unless the task scope is explicitly changed.

This is a docs-only design task.

---

Expected Output

Report:

1. Created file path
2. Files reviewed
3. Design recommendation
4. Whether only the allowed result report was created
5. Whether any code/test/output/config files were modified
6. "git status -sb" output
7. "git diff --stat" output
8. "git diff --name-only" output
9. "git diff --check" output
10. Whether the result is ready for human review
11. Whether a follow-up implementation task is recommended

Stop after this task.

Do not git add.

Do not commit.

Do not push.