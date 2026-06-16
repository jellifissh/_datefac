# Agent Fixture Foundation

## Purpose

This directory is reserved for future `datefac_agent` regression fixtures.

The main goal is to preserve known bad cases and audit-sensitive edge cases from legacy DateFac work so the new Agent flow can prove that it rejects unsafe outputs instead of only passing happy-path samples.

## Planned Fixture Categories

Future fixture sets should cover cases such as:

- `unit_mismatch`
- `period_shift`
- `valuation_metric_confusion`
- `per_share_vs_total_amount`
- `weak_evidence`
- `false_positive_recovery`
- `semantic_class_unknown`

## Expected Source Material

The primary source of fixture ideas is the legacy `346B` series and related QA/audit stages, including:

- `346B`
- `346B2`
- `346B3`
- `346B4`
- `346B5`
- `346B5Q`

These stages exposed failure patterns that should later be distilled into small, reviewable fixture files.

## What Not To Do Yet

Do not copy large real outputs, benchmark folders, or client-preview assets into this directory during the foundation stage.

Do not treat raw historical outputs as drop-in fixtures without first shrinking them into minimal, test-focused cases.
