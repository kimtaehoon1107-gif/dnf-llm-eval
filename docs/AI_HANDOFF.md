# AI Handoff

## 2026-06-28 Codex Review

- Goal: review `kimtaehoon1107-gif/dnf-llm-eval` for practical fix opportunities and prepare a PR if useful.
- Branch: `codex/review-reproducibility`.
- Base: `origin/main`.
- Scope: repository reproducibility and lightweight validation; do not alter generated evaluation CSVs or report conclusions without a clear bug.
- Plan review requested from Claude Reviewer before implementation in Discord.
- Changes: added `scripts/smoke_check.py` and documented `python scripts\smoke_check.py` in `README.md`.
- Verification: PowerShell schema equivalent passed for required files, benchmark/adversarial CSV headers, and `data/structured/shop_items.json` UTF-8 parsing with 10 records.
- Local blocker: the Windows environment exposes Microsoft Store Python aliases but no usable `python` or `py` interpreter, so the new Python smoke check and syntax compilation could not be executed here until Python 3.10+ is installed or on PATH.
