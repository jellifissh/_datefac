# 348N-R7AJ dependency audit for real PDF text-layer provider

## Task ID

```text
348N-R7AJ dependency audit for real PDF text-layer provider
```

## Task size / reasoning level used

```text
task_size = small
recommended_reasoning_level = max
execution_mode = dependency-audit-only
reason = R7AJ audits whether the first real PDF text-layer provider can safely use existing project dependencies, or whether dependency addition / adapter skeleton work must be split into a later QA-gated task.
```

## Preflight

```text
git status -sb:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git pull origin pivot/348-agent-foundation:
  Updating acd68dc..785de6e
  Fast-forward
  created docs/codex_tasks/348N_R7AJ_dependency_audit_for_real_pdf_text_layer_provider.md
  updated docs/agent/项目进程.md
  updated docs/project_handoffs/CURRENT_MODEL_HANDOFF.md
  updated 项目进展大白话说明.md

git status -sb after pull:
  ## pivot/348-agent-foundation...origin/pivot/348-agent-foundation

git log --oneline -12:
  785de6e docs: update handoff after R7AI
  253cfcc docs: refresh plain-language progress after R7AI
  e2f21fd docs: sync progress after R7AI
  74fba5a docs: add R7AJ dependency audit task
  acd68dc docs: add R7AI real PDF text layer provider design
  17963c2 docs: update handoff after R7AH QA
  3fefad9 docs: refresh plain-language progress after R7AH QA
  f5b52d3 docs: sync progress after R7AH QA
  3012b3d docs: add R7AI real PDF text layer provider design task
  d0529a7 docs: add R7AH QA review
  0bc70a9 docs: update handoff after R7AH
  40312bd docs: refresh plain-language progress after R7AH
```

Worktree was clean after pull.

Read-only tooling note:

```text
rg.exe failed locally with Access is denied during broad search.
Equivalent read-only inventory was completed with git ls-files and git grep over tracked files.
This does not change the dependency-audit conclusion.
```

## Files reviewed

Required task/context files:

- `AGENTS.md`
- `.skills/README.md`
- `.skills/git_workflow.md`
- `.skills/datefac_agent_foundation.md`
- `.skills/agent_excel_intake_audit_workflow.md`
- `项目进展大白话说明.md`
- `docs/agent/项目进程.md`
- `docs/project_handoffs/CURRENT_MODEL_HANDOFF.md`
- `docs/codex_tasks/348N_R7AJ_dependency_audit_for_real_pdf_text_layer_provider.md`
- `docs/agent/348N_R7AI_REAL_PDF_TEXT_LAYER_PROVIDER_DESIGN.md`
- `docs/codex_tasks/348N_R7AI_real_pdf_text_layer_provider_design.md`
- `docs/agent/348N_R7AH_QA_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_PROTOTYPE_REVIEW.md`
- `docs/agent/348N_R7AG_LIGHTWEIGHT_PDF_EVIDENCE_BRIDGE_DESIGN.md`

Read-only implementation / boundary files:

- `tests/agent/lightweight_pdf_evidence_bridge_348n.py`
- `tests/agent/test_lightweight_pdf_evidence_bridge_348n.py`
- `datefac_agent/schemas/audit_models.py`
- `datefac_agent/audit/evidence_checker.py`
- `datefac_agent/review/review_queue_builder.py`
- `datefac_agent/delivery/evidence_index_writer.py`

Dependency/config files inspected:

- `requirements.txt`
- `pyproject.toml` = `NOT_PRESENT`
- `requirements-dev.txt` = `NOT_PRESENT`
- `setup.cfg` = `NOT_PRESENT`
- `setup.py` = `NOT_PRESENT`
- `Pipfile` = `NOT_PRESENT`
- `poetry.lock` = `NOT_PRESENT`
- `uv.lock` = `NOT_PRESENT`

## Dependency/config inventory

Tracked dependency/config inventory:

| File | Status | Finding |
| --- | --- | --- |
| `requirements.txt` | `PRESENT` | Contains only `pandas`, `openpyxl`, `requests`, `pyyaml`. |
| `requirements-dev.txt` | `NOT_PRESENT` | No dev/test dependency declaration found. |
| `pyproject.toml` | `NOT_PRESENT` | No PEP 621 / build-system dependency metadata found. |
| `setup.cfg` | `NOT_PRESENT` | No setuptools config dependency metadata found. |
| `setup.py` | `NOT_PRESENT` | No setuptools script dependency metadata found. |
| `Pipfile` | `NOT_PRESENT` | No Pipenv workflow found. |
| `poetry.lock` | `NOT_PRESENT` | No Poetry lock found. |
| `uv.lock` | `NOT_PRESENT` | No uv lock found. |

Observed dependency workflow:

```text
Current active project dependency declaration appears to be a minimal root requirements.txt file.
No lock file is present.
No package metadata file is present.
No optional dependency group mechanism is currently declared.
```

`requirements.txt` content:

```text
pandas
openpyxl
requests
pyyaml
```

## Existing PDF library findings

Declared project dependencies:

| Library | Declared in dependency/config files? | Audit result |
| --- | --- | --- |
| `PyMuPDF` / `fitz` | No | Not an existing project dependency. |
| `pdfplumber` | No | Not an existing project dependency. |
| `pypdf` | No | Not an existing project dependency. |
| `PyPDF2` | No | Not an existing project dependency. |
| `pdfminer.six` | No | Not an existing project dependency. |
| `reportlab` | No | Not an existing project dependency. |

Read-only tracked search findings:

```text
Legacy/root configuration and old extraction paths reference pdfplumber.
Legacy tools include optional pdfplumber / fitz / pypdf import patterns.
R7AG/R7AI docs discuss pypdf / PyMuPDF / pdfplumber as future candidates.
R7AH-QA confirmed no heavy parser imports in the test-only prototype.
```

These references do not count as active `datefac_agent` dependencies. The current DateFac Agent mainline must not treat legacy parser modules or local environment packages as dependency authorization.

Local environment probe, for audit context only:

| Package | Environment probe | Project-declared? | Usable for R7AK direct implementation? |
| --- | --- | --- | --- |
| `PyMuPDF` / `fitz` | import spec present, version `1.27.2.3` | No | No. Environment-only availability is not a dependency contract. |
| `pdfplumber` | import spec present, version `0.11.9` | No | No. Environment-only availability is not a dependency contract. |
| `pdfminer.six` | import spec present, version `20251230` | No | No. Environment-only availability is not a dependency contract. |
| `reportlab` | import spec present, version `4.5.0` | No | No. Useful only after explicit test dependency design. |
| `pypdf` | not importable | No | No. |
| `PyPDF2` | not importable | No | No. |

Conclusion:

```text
No acceptable PDF text-layer extraction dependency is currently declared for the active project.
R7AK should not implement a real PDF text-layer provider that relies on environment-only packages.
```

## Candidate comparison

| Candidate | Page text extraction fit | Page-selection fit | Windows/install risk | Scanned-PDF behavior | Performance / cost fit | Lightweight-first fit | Audit position |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `pypdf` | Suitable for simple text-layer extraction and smoke-level page text. Layout fidelity is limited. | Good enough for target-page `extract_text` style access if dependency is added. | Lower install risk because it is pure Python. Not currently declared or importable. | Text layer empty/None on scanned/image-only pages; must fail closed. | Likely adequate for capped page extraction; not a table parser. | Strong candidate for first optional dependency design because it keeps scope light. | Do not implement yet; consider as first dependency-design candidate. |
| `PyMuPDF` / `fitz` | Strong page-level text extraction and possible coordinates. | Very good for target-page extraction and future locator precision. | Native-wheel/package/license risk; installed in local env but not declared. | Can return empty text for image-only pages; must not trigger OCR automatically. | Fast and capable, but capability may tempt production parser expansion. | Good technical fit but needs dependency/license/Windows audit before adoption. | Do not implement from environment-only availability. |
| `pdfplumber` | Richer text/table geometry and familiar legacy use. | Good page targeting; table/layout features are more than R7AJ needs. | Heavier dependency stack, likely via `pdfminer.six`; not declared. | Empty/weak text on scanned pages; no OCR by itself. | Slower/heavier than needed for bounded evidence snippets. | Risk of drifting back to legacy pdfplumber extraction route. | Not recommended as first default provider. |
| `pdfminer.six` | Text-layer extraction engine, but lower-level API. | Possible, but adapter complexity is higher. | Pure Python but can be slower/complex; environment-only, not declared. | Fails to useful text on scanned/image-only pages. | Potentially slower for many pages; more implementation surface. | Less ergonomic for a small first provider. | Not recommended as first adapter unless dependency design rejects higher-level options. |
| No new dependency / adapter boundary only | No real PDF text extraction. | Can define status contracts and missing-dependency behavior only. | Lowest risk. | Can model fallback-required statuses but cannot inspect PDFs. | Cost-zero and safe. | Good for skeleton/status tests, but R7AI already designed most boundary concepts. | Safe if the next task is not allowed to add dependency; less valuable than dependency-design next. |

## Recommended dependency strategy

R7AJ decision:

```text
Do not proceed to real PDF provider implementation with current dependencies.
Split dependency selection/addition into a separate R7AK optional PDF dependency addition design task.
```

Recommended strategy:

1. Keep real PDF provider behind the R7AI adapter boundary.
2. Do not rely on local environment packages that are not declared in project dependency files.
3. Do not import PDF libraries at module import time in `datefac_agent`.
4. Choose at most one first real text-layer dependency in a future dependency task.
5. Prefer a lightweight text-layer dependency first; do not choose a table parser because legacy pdfplumber paths exist.
6. Require a dependency-specific QA before implementation.

Candidate priority for R7AK design:

```text
Primary candidate to evaluate first: pypdf, because it is lightweight and pure-Python.
Secondary candidate: PyMuPDF, if page-level speed / locator quality outweighs native-wheel and license/package risk.
Defer pdfplumber as a default provider because it is heavier and risks reviving old table-extraction paths.
```

This is not a final library adoption decision. It is a recommendation that the next task should design and review one optional dependency path before implementation.

## Optional import strategy

Required optional-import policy for any later provider:

```text
- No top-level import of fitz / pdfplumber / pypdf / pdfminer in shared schemas, review, audit, delivery, runner, or CLI modules.
- Import only inside a narrow provider adapter method or a provider factory.
- Missing import returns a provider status, not an exception that crashes the audit path.
- Environment-only package availability must not silently activate production behavior.
- Tests must monkeypatch missing dependency behavior.
```

Recommended adapter pattern:

```text
PdfTextLayerProviderFactory.create(provider_name, config)
  -> checks configured provider allowlist
  -> checks import availability lazily
  -> returns MissingDependencyProvider when absent
  -> never falls back to MinerU/OCR/LLM/VLM automatically
```

Forbidden pattern:

```text
try:
    import pdfplumber
except ImportError:
    import fitz
```

Implicit fallback between libraries would make audit results non-reproducible and could change behavior by developer machine.

## Missing dependency status design

Missing dependency must be represented as data status, not as trusted evidence.

Recommended provider statuses:

```text
MISSING_DEPENDENCY
PROVIDER_NOT_CONFIGURED
PROVIDER_NOT_ALLOWED
SOURCE_FILE_MISSING
SOURCE_HASH_MISMATCH
PDF_UNREADABLE
PDF_ENCRYPTED
INVALID_PAGE_NUMBER
PAGE_TEXT_EMPTY
NO_TEXT_LAYER
SCANNED_OR_IMAGE_ONLY
SEARCH_CAP_EXCEEDED
EXTRACTION_ERROR
```

Recommended row-level consequence:

```text
source_text_selection.status = MISSING or unavailable-equivalent status
source_text_selection.used_for_agreement = false
agreement_status = UNVERIFIED unless ordinary evidence logic says MISSING
clean_candidate_type remains REVIEW_REQUIRED unless independently eligible by existing rules
readiness gates stay closed
```

A missing dependency must not:

```text
- synthesize SourceTextEvidence
- use Excel raw excerpt as trusted source_text
- trigger MinerU / OCR / LLM / VLM
- promote evidence_level
- create clean_data admission
```

## Implementation readiness decision

Current implementation readiness:

```text
NOT_READY_FOR_REAL_PDF_PROVIDER_IMPLEMENTATION
```

Reasoning:

1. No PDF text-layer dependency is declared in `requirements.txt` or another dependency/config file.
2. No lock file exists to make environment-only package availability reproducible.
3. Current active DateFac Agent contract has only synthetic/test-only bridge coverage for page text.
4. R7AI explicitly required a dependency audit before implementation.
5. Using locally installed `fitz`, `pdfplumber`, or `pdfminer` would bypass dependency review and create hidden machine-specific behavior.

If a suitable dependency had already been declared, a narrow `test-only` or `demo-only` provider slice could be considered. Since no suitable dependency is declared, R7AK should not implement real PDF parsing yet.

Generated in-test PDF policy:

```text
Defer generated in-test PDF until after dependency design/addition is approved.
Do not introduce reportlab or any PDF-generation helper implicitly in R7AJ.
Synthetic page text remains the current safe test source.
```

Cache manifest policy:

```text
Defer cache implementation until after provider dependency and adapter status contracts are approved.
R7AK optional dependency design may specify cache metadata, but should not write cache artifacts.
```

## Recommended next slice

Recommended next task:

```text
348N-R7AK optional PDF dependency addition design
```

Why not `348N-R7AK real PDF text-layer provider test-only implementation`:

```text
No real PDF text-layer library is declared as a project dependency.
A test-only implementation would either fail immediately or rely on undeclared local packages.
```

Why not `348N-R7AK adapter-boundary-only provider skeleton` as the primary next slice:

```text
R7AI already defined the provider boundary and missing/status concepts.
A skeleton without dependency selection would add limited evidence value while still not proving text-layer extraction.
If dependency addition is postponed again, a skeleton can be the fallback; it should not replace dependency design as the recommended next step.
```

Smallest safe R7AK scope:

```text
- Design optional dependency addition only.
- Choose one candidate path or decide no-go.
- Define dependency declaration location and QA gates.
- Define missing-dependency tests.
- Keep implementation, real PDF execution, cache writes, and production hooks out of scope.
```

## Risk review

Key risks and controls:

| Risk | Control |
| --- | --- |
| Environment-only packages make behavior machine-specific. | Treat undeclared packages as unavailable for project readiness. |
| Legacy pdfplumber paths pull work back into batch extraction. | Do not use legacy parser modules; keep provider adapter narrow and source_text-only. |
| Adding a heavy parser makes MinerU/OCR/PDF parsing feel default. | Keep MinerU/OCR fallback explicit and disabled by default; no automatic fallback chain. |
| Scanned/image-only PDFs silently pass as empty or weak evidence. | Return `SCANNED_OR_IMAGE_ONLY` / `NO_TEXT_LAYER` / `PAGE_TEXT_EMPTY`; no trusted evidence. |
| Encrypted/unreadable PDFs crash runner. | Return data status such as `PDF_ENCRYPTED` / `PDF_UNREADABLE`. |
| Full page text leaks into evidence_index or review_queue. | Only metadata/hash/count/status in serialized outputs; bounded snippet only inside `SourceTextEvidence` when trusted. |
| VERIFIED gets misread as STRONG_EVIDENCE. | Keep agreement separate from evidence_level; no evidence promotion. |
| Page search becomes expensive over many PDFs. | Enforce target-page first, capped candidate search, max pages/chars, cache-key design. |
| Cache becomes stale. | Key by `source_file_sha256`, provider/version, extraction config hash, page-index policy. |

## Boundary review

R7AJ stayed within dependency-audit-only scope:

```text
code modified = no
tests modified = no
fixtures modified = no
dependency/config files modified = no
datefac_agent/ modified = no
tests/ modified = no
input/output/temp/data/legacy modified = no
new dependency added = no
PDF parser implemented = no
real PDF run = no
workbook rerun = no
run_pilot = no
MinerU / OCR / LLM / VLM = 0
readiness gates opened = no
```

Policy boundaries confirmed:

```text
MinerU remains fallback, not default.
OCR remains fallback, not default.
Scanned/image-only PDF must return fallback-required / review status.
Raw Excel/JSON excerpt remains a hint, not trusted source_text.
Full source_text must not serialize to evidence_index / review_queue.
VERIFIED must not imply STRONG_EVIDENCE.
VERIFIED must not imply clean_data admission.
VERIFIED must not imply client_ready / production_ready / formal_client_export_allowed.
```

## Validation outputs

Required validation commands run:

```text
python -m py_compile datefac_agent/review/clean_candidate_policy.py
  PASS

python -m py_compile datefac_agent/audit/evidence_checker.py datefac_agent/schemas/audit_models.py datefac_agent/review/review_queue_builder.py datefac_agent/delivery/evidence_index_writer.py
  PASS

python -m py_compile tests/agent/source_text_sidecar_loader_348n.py tests/agent/test_source_text_sidecar_loader_348n.py tests/agent/test_agent_excel_intake_audit_348a.py
  PASS

python -m py_compile tests/agent/lightweight_pdf_evidence_bridge_348n.py tests/agent/test_lightweight_pdf_evidence_bridge_348n.py
  PASS

pytest tests/agent -q
  180 passed in 0.81s
```

Post-report diff validation expected/confirmed before staging:

```text
git status -sb
  one new allowed report only

git diff --stat
  docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md only

git diff --name-only
  docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md

git diff --check
  PASS
```

## Decision

```text
Decision = 348N_R7AJ_DEPENDENCY_AUDIT_CONFIRMED_NO_DECLARED_PDF_TEXT_LAYER_DEPENDENCY
```

Interpretation:

```text
The project cannot safely proceed directly to real PDF text-layer provider implementation using current declared dependencies.
R7AK should first design optional PDF dependency addition, including dependency location, package choice, missing-dependency behavior, QA gates, and no-production-hook boundaries.
```

## Recommended next task

```text
348N-R7AK optional PDF dependency addition design
```

Recommended R7AK focus:

```text
- Choose one candidate optional dependency path, likely pypdf-first unless PyMuPDF benefits justify native dependency risk.
- Decide where to declare optional/test dependency in a project that currently only has requirements.txt.
- Define dependency QA gates, Windows install checks, license/package risk review, and missing-dependency behavior.
- Keep real PDF parsing implementation out of R7AK unless a later task explicitly allows it.
- Keep MinerU/OCR/LLM/VLM and readiness gates closed.
```

## Data Result / 数据结果

```text
Decision（任务结论）= PASS，348N_R7AJ_DEPENDENCY_AUDIT_CONFIRMED_NO_DECLARED_PDF_TEXT_LAYER_DEPENDENCY
build_result（构建结果）= PASS，py_compile validation passed
test_result（测试结果）= PASS，pytest tests/agent -q => 180 passed in 0.81s
files_modified（修改文件数）= 1，only docs/agent/348N_R7AJ_DEPENDENCY_AUDIT_FOR_REAL_PDF_TEXT_LAYER_PROVIDER.md
error_count（错误数）= 0 validation errors; rg local access issue was recovered with git grep and did not affect audit completeness
boundary_check（边界检查）= PASS，audit report only; no code/test/dependency/input/output/temp/data/legacy changes\ndependency_inventory_result（依赖盘点结果）= PASS，only requirements.txt exists; no pyproject/setup/lock/dev dependency file present
pdf_library_available_result（PDF库可用性结果）= NO_DECLARED_PROJECT_PDF_TEXT_LAYER_LIBRARY; local env packages are not accepted as project dependencies
dependency_strategy_result（依赖策略结果）= SPLIT_TO_OPTIONAL_DEPENDENCY_ADDITION_DESIGN_BEFORE_IMPLEMENTATION
implementation_readiness_result（实现准备度结果）= NOT_READY_FOR_REAL_PDF_PROVIDER_IMPLEMENTATION_WITH_CURRENT_DECLARED_DEPENDENCIES
risk_control_result（风险控制结果）= PASS，MinerU/OCR fallback only; scanned PDF fail-closed; metadata-only serialization; VERIFIED non-promotional
readiness_gates（就绪门）= CLOSED，client_ready=false; production_ready=false; formal_client_export_allowed=false; demo_export_only=true
recommended_next_task（推荐下一任务）= 348N-R7AK optional PDF dependency addition design
```
