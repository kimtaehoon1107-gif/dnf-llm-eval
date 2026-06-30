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

## 2026-06-29 Source Post ID Stability Follow-up

- Goal: fix a stable-ID edge case before corpus refresh.
- Branch: `codex/source-post-id-stability`.
- Problem:
  - Major update rows can use `data-url="/pr/actupdate/..."` while also carrying `data-no="2927617"`.
  - If the collector derives stable IDs from URL only, these important rows can fall back to `DOC-xx` instead of `DNF-2927617`.
- Change:
  - Preserve `data-no` as `source_post_id` in discovered and metadata CSV outputs.
  - Prefer `source_post_id` over URL parsing when building `doc_id`.
  - Keep URL parsing as fallback and `DOC-xx` as final fallback.
  - Reject duplicate non-empty `source_post_id` values.
  - Move third-party collector imports into runtime functions so smoke check can import and test stable-ID helpers without installing Selenium/requests.

## 2026-06-30 Ollama PC Continuation

- Branch: `codex/v2026-06-results`.
- Base commit: `4df4022 Add v2026_06 benchmark questions`.
- Goal: run the staged 2026-06 corpus evaluation that required an Ollama machine, then record results separately from the active 2026-05 benchmark.
- Environment:
  - Python 3.14.4.
  - Ollama model available: `qwen3:4b-instruct-2507-q4_K_M`.
  - `python scripts\smoke_check.py` passed.
- Implementation note:
  - Added `--num-ctx` to `scripts/run_rag_local_llm_eval.py`.
  - Without this option, some `top_k=8` RAG prompts exceeded Ollama's default 4096-token context and returned HTTP 400.
  - The successful run used `--num-ctx 8192`.
- Generated outputs:
  - `eval\rag_v2026_06_bm25_instruct_answers.csv`
  - `eval\rag_v2026_06_bm25_instruct_answers.manifest.json`
  - `eval\rag_v2026_06_bge_m3_instruct_answers.csv`
  - `eval\rag_v2026_06_bge_m3_instruct_answers.manifest.json`
  - `eval\rag_v2026_06_hybrid_instruct_answers.csv`
  - `eval\rag_v2026_06_hybrid_instruct_answers.manifest.json`
  - `eval\rag_v2026_06_hybrid_rerank_instruct_answers.csv`
  - `eval\rag_v2026_06_hybrid_rerank_instruct_answers.manifest.json`
  - `eval\v2026_06_answer_compare_summary.csv`
  - `eval\v2026_06_answer_compare_detail.csv`
  - `eval\v2026_06_retrieval_compare_summary.csv`
  - `eval\v2026_06_retrieval_compare_detail.csv`
  - Raw dry-run CSV/manifest were generated locally but remain ignored by `eval/*dry_run*`.
  - BGE-M3 embedding cache was generated locally under ignored `data/cache/`.
- Results:
  - BM25 generation: factual 13/20, format 20/20, meta reasoning 0, refusal 3, average latency 6.061s.
  - BGE-M3 generation: factual 13/20, format 20/20, meta reasoning 0, refusal 3, average latency 4.219s.
  - Hybrid generation: factual 15/20, format 20/20, meta reasoning 0, refusal 2, average latency 4.613s.
  - Hybrid + BGE reranker generation: factual 15/20, format 20/20, meta reasoning 0, refusal 0, average latency 20.868s.
  - BM25 retrieval: evidence hit 19/20, top-1 evidence hit 18/20, avg token recall 0.974.
  - BGE-M3 retrieval: evidence hit 20/20, top-1 evidence hit 18/20, avg token recall 0.997.
  - Hybrid retrieval: evidence hit 20/20, top-1 evidence hit 18/20, avg token recall 1.000.
  - Hybrid + BGE reranker retrieval: evidence hit 20/20, top-1 evidence hit 19/20, avg token recall 1.000.
- Documentation updated:
  - `README.md`
  - `report\benchmark_questions_v2026_06_design.md`
  - `report\README.md`
- Remaining follow-up:
  - Treat hybrid as the current best speed/accuracy setting for `benchmark_questions_v2026_06`.
  - Treat hybrid + BGE reranker as a useful retrieval-quality reference, but not as the default generation setting because latency rose without factual proxy gain.
  - Review Q012 and Q013 manually because generation still missed those answers despite retrieved context.
  - Check Q003, Q014, and Q018 as likely proxy false negatives or partial-answer cases.
  - Next likely technical path: structured patch-note change records for before/after skill changes.
  - Use manual rubric or LLM-as-judge to separate proxy false negatives from real answer failures.
