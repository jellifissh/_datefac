# Skill: Table Extraction

## Current Parser Strategy
- MinerU is the current primary benchmark parser candidate for real PDF financial reports
- `pdfplumber` remains a legacy/stable baseline for some structured PDFs
- `marker` remains an optional legacy backend, not the main path
- `docling` remains probe-only unless benchmark evidence improves

## Current Benchmark Position
- `342C` MinerU first run failed because of SSL / HuggingFace / environment issues
- `342C2` after env fix produced real parse artifacts and is currently `3/5` success
- `ready_for_342d = conditional`
- Do not claim full MinerU benchmark pass
- Must inspect failed retry rows before parser ensemble compare

## Extraction Evidence Order
- Always inspect extraction artifacts first
- Then inspect post-processing behavior
- Then inspect financial standardization behavior
- Do not jump to cleaning-rule changes before parser evidence is reviewed

## MinerU Output Consumption Priority
- Prefer `.md`
- Prefer `*_content_list.json`
- Review table-related JSON and structured sidecar evidence
- Do not treat raw images as the primary downstream consumption surface

## Legacy Baselines
- `pdfplumber` remains useful as a historical baseline for structured tables
- `marker` history should be preserved as legacy context, not deleted
- `docling` remains a probe path until stronger benchmark evidence exists

## Known Failure Modes
- SSL certificate verify failed
- HuggingFace / hf-mirror inaccessible
- user site-packages pollution from `C:\Users\哥哥\AppData\Roaming\Python\Python312\site-packages`
- `huggingface_hub >= 1.0` incompatible with the current `transformers / tokenizers` stack
- base env cannot find `mineru`
- `mineru_new` env may lack `pandas` for DateFac runner usage
- Windows subprocess path issues for `.exe` / `.cmd`
- runner may look silent while MinerU is still processing

## Action Rules
- Do not hand-write more PDF cleaning rules before MinerU benchmark evidence is inspected
- Do not treat partial MinerU success as parser-compare readiness by default
- Do not move to `342D` until failed retry rows are inspected and `qa_fail_count = 0`
- Keep legacy parser context, but anchor new decisions on current MinerU benchmark evidence

