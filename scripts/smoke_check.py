from __future__ import annotations

import argparse
import csv
import json
import py_compile
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

PYTHON_SCRIPTS = (
    BASE_DIR / "scripts" / "ask_dnf_rag.py",
    BASE_DIR / "scripts" / "build_structured_shop_data.py",
    BASE_DIR / "scripts" / "collect_dnf_updates_selenium.py",
    BASE_DIR / "scripts" / "run_local_llm_eval.py",
    BASE_DIR / "scripts" / "run_rag_local_llm_eval.py",
    BASE_DIR / "scripts" / "score_answer_runs.py",
    BASE_DIR / "scripts" / "score_retrieval_runs.py",
)

REQUIRED_FILES = (
    BASE_DIR / "README.md",
    BASE_DIR / "index.html",
    BASE_DIR / "requirements.txt",
    BASE_DIR / "questions" / "benchmark_questions.csv",
    BASE_DIR / "questions" / "adversarial_questions.csv",
    BASE_DIR / "eval" / "evaluation_rubric.md",
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
    BASE_DIR / "questions" / "adversarial_questions.csv": {
        "question_id",
        "question",
        "expected_behavior",
    },
}


def check_required_files() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"missing required file: {path.relative_to(BASE_DIR)}")
    return errors


def check_python_syntax() -> list[str]:
    errors: list[str] = []
    for path in PYTHON_SCRIPTS:
        if not path.exists():
            errors.append(f"missing Python script: {path.relative_to(BASE_DIR)}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            errors.append(f"syntax error in {path.relative_to(BASE_DIR)}: {exc.msg}")
    return errors


def check_csv_headers() -> list[str]:
    errors: list[str] = []
    for path, required_columns in CSV_REQUIRED_COLUMNS.items():
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            fieldnames = set(reader.fieldnames or [])
        missing = sorted(required_columns - fieldnames)
        if missing:
            errors.append(
                f"{path.relative_to(BASE_DIR)} missing columns: {', '.join(missing)}"
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
        return [f"{path.relative_to(BASE_DIR)} must contain a JSON list"]

    required_keys = {
        "record_id",
        "doc_id",
        "item_name",
        "price_text",
        "purchase_limit_text",
    }
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            errors.append(f"{path.relative_to(BASE_DIR)} record {index} is not an object")
            continue
        missing = sorted(required_keys - set(record))
        if missing:
            errors.append(
                f"{path.relative_to(BASE_DIR)} record {index} missing keys: "
                f"{', '.join(missing)}"
            )
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
        ("CSV headers", check_csv_headers),
        ("structured data", check_structured_data),
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
