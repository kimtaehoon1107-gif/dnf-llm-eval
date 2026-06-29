from __future__ import annotations

import argparse
import csv
import importlib.util
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

PYTHON_SCRIPTS = (
    BASE_DIR / "scripts" / "ask_dnf_rag.py",
    BASE_DIR / "scripts" / "build_corpus_snapshot.py",
    BASE_DIR / "scripts" / "build_structured_shop_data.py",
    BASE_DIR / "scripts" / "collect_dnf_updates_selenium.py",
    BASE_DIR / "scripts" / "run_local_llm_eval.py",
    BASE_DIR / "scripts" / "run_manifest.py",
    BASE_DIR / "scripts" / "run_rag_local_llm_eval.py",
    BASE_DIR / "scripts" / "score_answer_runs.py",
    BASE_DIR / "scripts" / "score_retrieval_runs.py",
)

REQUIRED_FILES = (
    BASE_DIR / "README.md",
    BASE_DIR / "index.html",
    BASE_DIR / "requirements.txt",
    BASE_DIR / "questions" / "benchmark_questions.csv",
    BASE_DIR / "questions" / "benchmark_questions_v2026_05.csv",
    BASE_DIR / "questions" / "question_sets.json",
    BASE_DIR / "questions" / "adversarial_questions.csv",
    BASE_DIR / "eval" / "evaluation_rubric.md",
    BASE_DIR / "data" / "corpus_snapshot.json",
    BASE_DIR / "data" / "structured" / "shop_items.json",
)

CSV_REQUIRED_COLUMNS = {
    BASE_DIR / "questions" / "benchmark_questions.csv": {
        "question_id",
        "doc_id",
        "question",
        "gold_answer",
        "evidence",
        "expected_behavior",
    },
    BASE_DIR / "questions" / "benchmark_questions_v2026_05.csv": {
        "question_id",
        "doc_id",
        "question",
        "gold_answer",
        "evidence",
        "expected_behavior",
    },
    BASE_DIR / "questions" / "adversarial_questions.csv": {
        "question_id",
        "question",
        "expected_behavior",
    },
}


def relative(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


def check_required_files() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file: {relative(path)}")
    return errors


def check_python_syntax() -> list[str]:
    errors: list[str] = []
    for path in PYTHON_SCRIPTS:
        if not path.exists():
            errors.append(f"missing Python script: {relative(path)}")
            continue
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec", dont_inherit=True)
        except SyntaxError as exc:
            location = f"{relative(path)}:{exc.lineno or 0}:{exc.offset or 0}"
            errors.append(f"syntax error in {location}: {exc.msg}")
        except UnicodeDecodeError as exc:
            errors.append(f"cannot decode {relative(path)} as UTF-8: {exc}")
    return errors


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def processed_doc_ids() -> set[str]:
    processed_dir = BASE_DIR / "data" / "processed_md"
    return {
        path.name.split("_", 1)[0]
        for pattern in ("DOC-*.md", "DNF-*.md")
        for path in processed_dir.glob(pattern)
    }


def check_csv_inputs() -> list[str]:
    errors: list[str] = []
    for path, required_columns in CSV_REQUIRED_COLUMNS.items():
        if not path.exists():
            continue
        rows = read_csv_rows(path)
        fieldnames = set(rows[0].keys()) if rows else set()
        missing = sorted(required_columns - fieldnames)
        if missing:
            errors.append(f"{relative(path)} missing columns: {', '.join(missing)}")
        if not rows:
            errors.append(f"{relative(path)} has no data rows")

    benchmark_path = BASE_DIR / "questions" / "benchmark_questions.csv"
    if benchmark_path.exists():
        rows = read_csv_rows(benchmark_path)
        seen_question_ids: set[str] = set()
        known_doc_ids = processed_doc_ids()
        for index, row in enumerate(rows, start=2):
            question_id = row.get("question_id", "").strip()
            doc_id = row.get("doc_id", "").strip()
            if not question_id:
                errors.append(f"{relative(benchmark_path)} row {index} has empty question_id")
            elif question_id in seen_question_ids:
                errors.append(f"{relative(benchmark_path)} duplicate question_id: {question_id}")
            seen_question_ids.add(question_id)

            if not doc_id:
                errors.append(f"{relative(benchmark_path)} row {index} has empty doc_id")
            elif doc_id not in known_doc_ids:
                errors.append(
                    f"{relative(benchmark_path)} row {index} references missing doc_id: {doc_id}"
                )
    return errors


def check_structured_data() -> list[str]:
    path = BASE_DIR / "data" / "structured" / "shop_items.json"
    if not path.exists():
        return []

    errors: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        records = json.load(f)
    if not isinstance(records, list):
        return [f"{relative(path)} must contain a JSON list"]

    required_keys = {
        "record_id",
        "doc_id",
        "item_name",
        "price_text",
        "purchase_limit_text",
    }
    seen_record_ids: set[str] = set()
    known_doc_ids = processed_doc_ids()
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append(f"{relative(path)} record {index} is not an object")
            continue
        missing = sorted(required_keys - set(record))
        if missing:
            errors.append(
                f"{relative(path)} record {index} missing keys: "
                f"{', '.join(missing)}"
            )

        record_id = str(record.get("record_id", "")).strip()
        doc_id = str(record.get("doc_id", "")).strip()
        if not record_id:
            errors.append(f"{relative(path)} record {index} has empty record_id")
        elif record_id in seen_record_ids:
            errors.append(f"{relative(path)} duplicate record_id: {record_id}")
        seen_record_ids.add(record_id)

        if not doc_id:
            errors.append(f"{relative(path)} record {index} has empty doc_id")
        elif doc_id not in known_doc_ids:
            errors.append(f"{relative(path)} record {index} references missing doc_id: {doc_id}")
    return errors


def check_corpus_snapshot() -> list[str]:
    metadata_path = BASE_DIR / "data" / "metadata.csv"
    snapshot_path = BASE_DIR / "data" / "corpus_snapshot.json"
    errors: list[str] = []

    if not metadata_path.exists() or not snapshot_path.exists():
        return errors

    rows = read_csv_rows(metadata_path)
    required_columns = {"doc_id", "source_post_id", "processed_path", "url", "status"}
    fieldnames = set(rows[0].keys()) if rows else set()
    missing = sorted(required_columns - fieldnames)
    if missing:
        errors.append(f"{relative(metadata_path)} missing columns: {', '.join(missing)}")

    seen_source_post_ids: set[str] = set()
    metadata_doc_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        doc_id = row.get("doc_id", "").strip()
        source_post_id = row.get("source_post_id", "").strip()
        processed_path = row.get("processed_path", "").strip()

        if not doc_id:
            errors.append(f"{relative(metadata_path)} row {index} has empty doc_id")
        else:
            metadata_doc_ids.add(doc_id)

        if not source_post_id:
            errors.append(f"{relative(metadata_path)} row {index} has empty source_post_id")
        elif source_post_id in seen_source_post_ids:
            errors.append(f"{relative(metadata_path)} duplicate source_post_id: {source_post_id}")
        seen_source_post_ids.add(source_post_id)

        if processed_path and not (BASE_DIR / processed_path).exists():
            errors.append(f"{relative(metadata_path)} row {index} missing processed file: {processed_path}")

    with snapshot_path.open("r", encoding="utf-8") as f:
        snapshot = json.load(f)

    documents = snapshot.get("documents", [])
    if not isinstance(documents, list):
        errors.append(f"{relative(snapshot_path)} documents must be a list")
        documents = []

    snapshot_doc_ids = {
        str(doc.get("doc_id", "")).strip()
        for doc in documents
        if isinstance(doc, dict)
    }
    if snapshot_doc_ids != metadata_doc_ids:
        errors.append(f"{relative(snapshot_path)} document IDs do not match metadata.csv")

    summary_count = snapshot.get("summary", {}).get("document_count")
    if summary_count != len(rows):
        errors.append(f"{relative(snapshot_path)} summary.document_count must be {len(rows)}")

    processed_docs = snapshot.get("processed_docs", {})
    if not processed_docs.get("sha256"):
        errors.append(f"{relative(snapshot_path)} processed_docs.sha256 is missing")

    return errors


def check_question_sets() -> list[str]:
    path = BASE_DIR / "questions" / "question_sets.json"
    if not path.exists():
        return []

    errors: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    active_id = str(manifest.get("active_question_set_id", "")).strip()
    question_sets = manifest.get("question_sets", [])
    if not isinstance(question_sets, list):
        return [f"{relative(path)} question_sets must be a list"]

    seen_ids: set[str] = set()
    active_seen = False
    for index, question_set in enumerate(question_sets, start=1):
        if not isinstance(question_set, dict):
            errors.append(f"{relative(path)} question_sets[{index}] must be an object")
            continue

        question_set_id = str(question_set.get("id", "")).strip()
        question_path = str(question_set.get("path", "")).strip()
        status = str(question_set.get("status", "")).strip()

        if not question_set_id:
            errors.append(f"{relative(path)} question_sets[{index}] has empty id")
        elif question_set_id in seen_ids:
            errors.append(f"{relative(path)} duplicate question set id: {question_set_id}")
        seen_ids.add(question_set_id)
        active_seen = active_seen or question_set_id == active_id

        if status != "planned":
            if not question_path:
                errors.append(f"{relative(path)} question set {question_set_id} has empty path")
            elif not (BASE_DIR / question_path).exists():
                errors.append(f"{relative(path)} question set {question_set_id} missing path: {question_path}")

        corpus_snapshot_path = str(question_set.get("corpus_snapshot_path", "")).strip()
        if corpus_snapshot_path and not (BASE_DIR / corpus_snapshot_path).exists():
            errors.append(
                f"{relative(path)} question set {question_set_id} missing corpus snapshot: "
                f"{corpus_snapshot_path}"
            )

    if active_id and not active_seen:
        errors.append(f"{relative(path)} active_question_set_id is not listed: {active_id}")

    return errors


def check_collector_doc_id_logic() -> list[str]:
    collector_path = BASE_DIR / "scripts" / "collect_dnf_updates_selenium.py"
    spec = importlib.util.spec_from_file_location("collect_dnf_updates_selenium", collector_path)
    if spec is None or spec.loader is None:
        return [f"cannot load collector module spec from {relative(collector_path)}"]

    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)

    errors: list[str] = []
    major_update_row = {
        "source_post_id": "2927617",
        "title": "시즌 11 Act 2. 제국의 파도 ＆ 폭권",
        "url": "https://df.nexon.com/pr/actupdate/MDAxNzI",
    }
    if collector.make_doc_id(major_update_row, 1) != "DNF-2927617":
        errors.append("collector must prefer source_post_id for data-url posts")

    regular_update_row = {
        "source_post_id": "",
        "title": "6/18(목) 정기점검 업데이트 안내",
        "url": "https://df.nexon.com/community/news/update/2927756?categoryType=0",
    }
    if collector.make_doc_id(regular_update_row, 2) != "DNF-2927756":
        errors.append("collector must fall back to URL post ID when source_post_id is empty")

    unknown_row = {"source_post_id": "", "title": "external", "url": "https://example.com"}
    if collector.make_doc_id(unknown_row, 3) != "DOC-03":
        errors.append("collector must keep DOC fallback when no stable post ID exists")

    try:
        collector.validate_unique_source_post_ids([major_update_row, major_update_row])
    except ValueError:
        pass
    else:
        errors.append("collector must reject duplicate source_post_id values")

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run dependency-light repository smoke checks."
    )
    parser.add_argument(
        "--skip-syntax",
        action="store_true",
        help="Skip Python syntax compilation checks.",
    )
    args = parser.parse_args()

    checks = [
        ("required files", check_required_files),
        ("CSV inputs", check_csv_inputs),
        ("structured data", check_structured_data),
        ("corpus snapshot", check_corpus_snapshot),
        ("question sets", check_question_sets),
        ("collector doc_id logic", check_collector_doc_id_logic),
    ]
    if not args.skip_syntax:
        checks.insert(1, ("Python syntax", check_python_syntax))

    errors: list[str] = []
    for label, check in checks:
        check_errors = check()
        if check_errors:
            print(f"[FAIL] {label}")
            for error in check_errors:
                print(f"  - {error}")
            errors.extend(check_errors)
        else:
            print(f"[OK] {label}")

    if errors:
        raise SystemExit(1)

    print("[DONE] smoke checks passed")


if __name__ == "__main__":
    main()
