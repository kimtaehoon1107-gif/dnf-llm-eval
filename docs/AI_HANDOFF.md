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

## 2026-06-29 Follow-up Polish

- Goal: tighten the open PR after reviewing current strengths and weak points.
- Branch: `codex/review-reproducibility`.
- PR: https://github.com/kimtaehoon1107-gif/dnf-llm-eval/pull/2
- Plan review requested from Claude Reviewer before implementation in Discord.
- Changes:
  - Updated `scripts/smoke_check.py` to use in-memory `compile(...)` instead of `py_compile`, avoiding `__pycache__` side effects.
  - Added benchmark question ID uniqueness, benchmark doc reference, structured record ID uniqueness, and structured record doc reference checks.
  - Removed `codex/**` push trigger from `.github/workflows/ci.yml` so PR branches do not run duplicate push and pull_request workflows.
- Verification:
  - PowerShell integrity equivalent passed: 22 benchmark questions, 10 structured records, 5 processed docs.
  - Local Python remains unavailable, so final `python scripts\smoke_check.py` verification is expected to come from GitHub Actions after push.
