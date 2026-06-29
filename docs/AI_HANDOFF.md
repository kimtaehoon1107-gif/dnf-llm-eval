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

## 2026-06-29 Freshness and Gate Follow-up

- Goal: address Issue #1 by separating score metrics from critical gates and recording evaluation date metadata.
- Branch: `codex/freshness-critical-gates`.
- Pre-step: PR #2 was verified with local bundled Python and GitHub Actions, then squash-merged into `main`.
- Scope:
  - Rewrite `eval/evaluation_rubric.md` so hallucination/overreach is a binary critical gate instead of a 0-3 score item.
  - Add `최신성` as a scored rubric item.
  - Add `checked_at`, `answer_reference_date`, and `source_reference_date` output fields to local and RAG evaluation CSV writers.
  - Keep existing generated CSVs and historical report scores unchanged; treat them as legacy results.
- Current implementation note:
  - `checked_at` defaults to the run date.
  - `answer_reference_date` defaults to `checked_at` unless explicitly supplied.
  - `source_reference_date` uses `data/metadata.csv` `posted_date` per `doc_id` unless explicitly supplied.

## 2026-06-29 Stable Document ID Follow-up

- Goal: prevent future corpus refreshes from reassigning `DOC-01`, `DOC-02`, etc. to different official posts.
- Branch: `codex/stable-document-ids`.
- Scope:
  - Change `scripts/collect_dnf_updates_selenium.py` so new collection runs use official update post IDs like `DNF-2927756` when the source URL contains a post number.
  - Keep a `DOC-xx` fallback for any source that does not expose a numeric update post ID.
  - Update RAG, structured-data builder, and smoke check document discovery to accept both existing `DOC-*` files and future `DNF-*` files.
- Deliberate non-goal:
  - Do not rewrite existing `data/processed_md`, `data/metadata.csv`, benchmark questions, or historical evaluation CSVs in this PR.
  - Corpus refresh should happen after this compatibility layer is merged.
- Verification note:
  - Smoke check compiles the collector, but direct collector import was not run in the bundled Python because `requests` is not installed there.
