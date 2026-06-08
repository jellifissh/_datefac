# Demo Release Checklist 332A/339A Synced

## 1. Safe To Show On GitHub

- MinerU-first real PDF intake preview
- Rule-based precision calibration and context repair
- Strict reviewed QA before any AI dry-run story
- AI review dry-run, grounded review, and adoption simulation with no-write-back wording
- Clear statements that the project is not client-ready and not production-ready

## 2. Safe To Say In Interview

- Parser quality is necessary but not sufficient
- MinerU is the current primary parser for real PDF preview intake
- Deterministic rules stay above model suggestions
- AI review is currently dry-run only
- Human review remains necessary for held, invalid, or conflicting rows
- `gpt-5.5` looks promising as a text adjudicator candidate, but 338D does not recommend immediate default adoption

## 3. Must Not Claim

- client-ready delivery
- production-ready deployment
- 100% accurate extraction
- no human review needed
- AI decisions are final
- fully automatic commercial SaaS
- direct investment-decision use

## 4. Known Limitations

- Current path remains sidecar / demo / preview / no-write-back
- Real PDF intake works, but production hardening is incomplete
- AI dry-run results still require human and policy review
- Broader benchmark coverage is still needed
- Deployment, security, permissions, and data isolation are unfinished

## 5. Suggested Next Engineering Milestones

- Expand real-PDF benchmark breadth
- Tighten deterministic guards where AI still produces invalid or weakly grounded responses
- Improve human review ergonomics beyond workbook-style workflows
- Revisit default model selection only after more adoption-simulation evidence
- Add deployment and data-governance design before any production ambition
