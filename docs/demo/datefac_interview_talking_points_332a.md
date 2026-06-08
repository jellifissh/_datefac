# Interview Talking Points 332A/339A Synced

## Why Parser Quality Alone Is Not Enough

A parser can recover text, tables, and candidate rows, but trust still depends on whether metric, year, unit, provenance, and surrounding context all line up. A plausible row can still be unsafe if the unit is wrong, the year is misaligned, or the row came from the wrong table role.

## Why MinerU Matters Now

MinerU is now the primary parser for the current real-PDF preview flow. That matters because the project is no longer talking only about cached sidecar previews. It now shows a concrete real-PDF intake path on three real reports, then layers governance and review logic on top of that parser output.

## Why Deterministic Rules Still Come First

The current system does not let model output outrank hard safety logic. Deterministic rules still guard against unit issues, duplicate rows, percentage-as-amount mistakes, and obvious noise. That is why the AI layer is framed as assistive dry-run logic rather than final truth.

## Why AI Review Is Dry-Run Only

The project intentionally separates model judgment from official adoption. 338A through 338D evaluate whether model outputs are useful, whether they are grounded, and whether any of them would be safe to accept under policy. They do not write back to official assets or production workbooks.

## How The Model Roles Differ

- MinerU is the primary parser for layout and table extraction.
- `AI_REVIEW_MODEL` is the current main text-adjudication candidate.
- DeepSeek flash is the conservative baseline and fallback.
- Vision models are reserved for future layout, screenshot, or image-table uncertainty.
- Human review remains the final safety layer.

## What 338B-338D Show

338B shows that `gpt-5.5` is materially stronger than the DeepSeek flash baseline on the sampled text-adjudication task. 338C shows that stronger grounding rules reduce invalid outputs further. 338D shows that even then, the project still does not automatically recommend default adoption, because dry-run policy and safety boundaries are more important than raw model enthusiasm.

## What Changed In The Project Story

The project story is no longer only “we created a reviewed preview after manual unit review.” It is now:

1. real PDFs can be ingested with MinerU-first parsing
2. candidate quality can be tightened with rules
3. reviewed rows can be made stricter before AI touches them
4. AI text adjudication can be evaluated safely in dry-run form
5. grounded review and adoption simulation can constrain model optimism

## Safest Honest Closing Line

DateFac is currently strongest as a trust-governed preview engineering system for financial research PDFs, not as a production-ready automatic delivery platform.
