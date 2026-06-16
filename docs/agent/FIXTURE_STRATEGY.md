# DateFac Agent Fixture Strategy

## Why Fixtures Matter After The Pivot

After the Agent pivot, the main question is no longer only whether data can be extracted.

The stronger question is whether extracted financial data can be audited, challenged, rejected when necessary, and routed into human review safely.

That means regression fixtures become core evidence for the new system. They preserve known failure modes and keep the new audit modules honest.

## Legacy Work As Future Test Material

The legacy `346B` chain already contains valuable error patterns and review signals:

- `346B`: quality-limited recovery pilot
- `346B2`: QA findings on false-positive risk
- `346B3`: semantic and unit rule refinement
- `346B4`: controlled expansion
- `346B5`: larger expansion
- `346B5Q`: larger QA audit

These should be mined for fixture ideas, not continued as the immediate foundation mainline.

## Fixture Types

Future fixtures should be grouped by failure pattern, not only by historical task ID.

Recommended categories:

- `unit_mismatch`
- `period_shift`
- `valuation_metric_confusion`
- `per_share_vs_total_amount`
- `weak_evidence`
- `false_positive_recovery`
- `semantic_class_unknown`
- `lineage_gap`

Each fixture should stay as small as possible while still reproducing a meaningful audit condition.

## Naming Convention

Use stable, descriptive names that separate fixture category from case intent.

Recommended pattern:

```text
<category>__<short_case_name>__v1.json
<category>__<short_case_name>__expected.json
```

If the fixture needs multiple files, keep a compact directory per case:

```text
<category>__<short_case_name>/
  input.json
  expected.json
  notes.md
```

Avoid naming fixtures only by task number, because future tests should remain understandable even after historical task memory fades.

## Source And Traceability

Every fixture should record where it came from:

- legacy stage or audit source such as `346B4Q`;
- high-level issue type;
- whether it represents a real observed failure or a synthetic reduction;
- what the expected audit outcome is.

This traceability can live in `notes.md` or inside compact metadata fields.

## Privacy And Safety Boundary

Fixtures should preserve failure semantics without copying large or sensitive historical payloads.

Do not put the following into fixtures unless there is explicit need and the content has been minimized:

- large real PDF outputs;
- bulk benchmark folders;
- client preview packages;
- temporary local dumps;
- uncontrolled copies of `input/`, `output/`, `temp/`, or `data/`.

Fixtures should be reduced, scoped, and safe for repeated local test use.

## How Future Tests Should Use Fixtures

Future tests should treat fixtures as audit assertions, not demo artifacts.

Typical usage should look like:

- load a compact structured input;
- run one checker or one narrow audit flow;
- assert `PASS`, `REVIEW`, or `FAIL`;
- assert issue codes, severity, and evidence expectations.

Prefer narrow tests over broad replay tests. The goal is to verify specific audit behavior with clear failure reasons.

## What Not To Do

Do not use fixture introduction as an excuse to migrate old runners wholesale.

Do not convert historical benchmark directories directly into test fixtures.

Do not claim that fixture coverage alone makes the system `client_ready` or `production_ready`.
