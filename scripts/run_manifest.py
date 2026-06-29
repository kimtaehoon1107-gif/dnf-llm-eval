from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def default_manifest_path(output_path: Path) -> Path:
    return output_path.with_suffix(".manifest.json")


def relative_path(path: Path, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_source(path: Path, base_dir: Path) -> dict[str, Any]:
    source: dict[str, Any] = {
        "path": relative_path(path, base_dir),
        "exists": path.exists(),
    }
    if path.exists() and path.is_file():
        source["sha256"] = sha256_file(path)
        source["bytes"] = path.stat().st_size
    return source


def tree_source(root: Path, base_dir: Path) -> dict[str, Any]:
    source: dict[str, Any] = {
        "path": relative_path(root, base_dir),
        "exists": root.exists(),
        "file_count": 0,
        "sha256": "",
    }
    if not root.exists():
        return source

    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        rel = path.relative_to(root).as_posix()
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
        file_count += 1

    source["file_count"] = file_count
    source["sha256"] = digest.hexdigest()
    return source


def current_git_commit(base_dir: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=base_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return ""
    return result.stdout.strip()


def json_safe(value: Any, base_dir: Path) -> Any:
    if isinstance(value, Path):
        return relative_path(value, base_dir)
    if isinstance(value, dict):
        return {str(k): json_safe(v, base_dir) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v, base_dir) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def build_run_manifest(
    *,
    run_type: str,
    base_dir: Path,
    script_path: Path,
    args: Any,
    output_path: Path,
    questions_path: Path,
    question_set_id: str,
    question_count: int,
    rows: list[dict[str, str]],
    checked_at: str,
    answer_reference_date: str,
    source_reference_date_arg: str,
    metadata_path: Path,
    processed_doc_dir: Path,
    extra_config: dict[str, Any] | None = None,
    extra_sources: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status_counts = Counter(row.get("status", "") for row in rows)

    manifest: dict[str, Any] = {
        "schema_version": 1,
        "run_type": run_type,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": current_git_commit(base_dir),
        "script": relative_path(script_path, base_dir),
        "python_version": sys.version.split()[0],
        "output_csv": relative_path(output_path, base_dir),
        "questions": {
            **file_source(questions_path, base_dir),
            "id": question_set_id,
            "row_count": question_count,
        },
        "dates": {
            "checked_at": checked_at,
            "answer_reference_date": answer_reference_date,
            "source_reference_date_arg": source_reference_date_arg,
        },
        "config": json_safe(vars(args), base_dir),
        "sources": {
            "metadata": file_source(metadata_path, base_dir),
            "processed_docs": tree_source(processed_doc_dir, base_dir),
        },
        "results": {
            "row_count": len(rows),
            "status_counts": dict(sorted(status_counts.items())),
        },
    }

    if extra_config:
        manifest["derived_config"] = json_safe(extra_config, base_dir)

    if extra_sources:
        manifest["sources"].update(json_safe(extra_sources, base_dir))

    return manifest


def write_run_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
