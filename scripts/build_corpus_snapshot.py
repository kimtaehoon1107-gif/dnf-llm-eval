from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_manifest import (
    current_git_commit,
    file_source,
    relative_path,
    tree_source,
)


BASE_DIR = Path(__file__).resolve().parents[1]
METADATA_FILE = BASE_DIR / "data" / "metadata.csv"
DOC_DIR = BASE_DIR / "data" / "processed_md"
DEFAULT_OUTPUT = BASE_DIR / "data" / "corpus_snapshot.json"
SOURCE_LIST_URL = "https://df.nexon.com/community/news/update/list"


def read_metadata(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def extract_source_post_id(url: str) -> str:
    match = re.search(r"/community/news/update/(\d+)", url)
    return match.group(1) if match else ""


def normalize_doc(row: dict[str, str]) -> dict[str, str]:
    source_post_id = row.get("source_post_id", "").strip() or extract_source_post_id(
        row.get("url", "")
    )
    return {
        "doc_id": row.get("doc_id", ""),
        "source_post_id": source_post_id,
        "doc_type": row.get("doc_type", ""),
        "category": row.get("category", ""),
        "posted_date": row.get("posted_date", ""),
        "title": row.get("title", ""),
        "url": row.get("url", ""),
        "processed_path": row.get("processed_path", ""),
        "status": row.get("status", ""),
    }


def build_snapshot(
    *,
    corpus_id: str,
    description: str,
    metadata_path: Path = METADATA_FILE,
    doc_dir: Path = DOC_DIR,
) -> dict[str, Any]:
    rows = read_metadata(metadata_path)
    docs = [normalize_doc(row) for row in rows]
    status_counts = Counter(doc["status"] for doc in docs)
    doc_types = Counter(doc["doc_type"] for doc in docs)
    posted_dates = sorted(doc["posted_date"] for doc in docs if doc["posted_date"])

    return {
        "schema_version": 1,
        "corpus_id": corpus_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "description": description,
        "source": {
            "name": "Dungeon & Fighter official update notices",
            "list_url": SOURCE_LIST_URL,
        },
        "doc_id_policy": (
            "This checked-in snapshot keeps the original DOC-* benchmark IDs for "
            "backward-compatible questions. The collector assigns DNF-<source_post_id> "
            "for refreshed official update documents."
        ),
        "generated_from_git_commit": current_git_commit(BASE_DIR),
        "metadata": file_source(metadata_path, BASE_DIR),
        "processed_docs": tree_source(doc_dir, BASE_DIR),
        "summary": {
            "document_count": len(docs),
            "posted_date_min": posted_dates[0] if posted_dates else "",
            "posted_date_max": posted_dates[-1] if posted_dates else "",
            "status_counts": dict(sorted(status_counts.items())),
            "doc_type_counts": dict(sorted(doc_types.items())),
        },
        "documents": docs,
    }


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a JSON manifest for the checked-in corpus.")
    parser.add_argument(
        "--corpus-id",
        default="dnf-official-updates-2026-05-doc-snapshot",
        help="Stable identifier for this corpus snapshot.",
    )
    parser.add_argument(
        "--description",
        default=(
            "Checked-in 2026-05 DNF official update corpus used by the original "
            "DOC-* benchmark questions."
        ),
        help="Human-readable snapshot description.",
    )
    parser.add_argument("--metadata", type=Path, default=METADATA_FILE)
    parser.add_argument("--doc-dir", type=Path, default=DOC_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    snapshot = build_snapshot(
        corpus_id=args.corpus_id,
        description=args.description,
        metadata_path=args.metadata,
        doc_dir=args.doc_dir,
    )
    write_snapshot(args.output, snapshot)
    print(f"[DONE] corpus snapshot: {relative_path(args.output, BASE_DIR)}")


if __name__ == "__main__":
    main()
