from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = BASE_DIR / "data" / "snapshots" / "2026-06-official-updates"
DOC_DIR = SNAPSHOT_DIR / "processed_md"
HAND_RECORDS = SNAPSHOT_DIR / "structured" / "change_records.json"

OUTPUT = BASE_DIR / "eval" / "auto_extracted_change_records_v1.json"

ARROW_RE = re.compile(r"^-?\s*(?P<before>.+?)\s*(?:→|->)\s*(?P<after>.+?)\s*$")
ADD_REMOVE_RE = re.compile(
    r"^(?P<subject>[^-]{1,20})\s*-\s*(?P<detail>.+?)(?P<verb>추가|제거|삭제)(?:됩니다|된다)\.?$"
)
BRACKET_RE = re.compile(r"^\[(?P<name>[^\]]{1,20})\]$")


def extract_arrow_pairs(doc_id: str, lines: list[str]) -> list[dict[str, object]]:
    records = []
    for i, line in enumerate(lines):
        m = ARROW_RE.match(line.strip())
        if not m:
            continue
        # nearest preceding non-empty line as context label
        context = ""
        for j in range(i - 1, max(i - 4, -1), -1):
            candidate = lines[j].strip()
            if candidate:
                context = candidate
                break
        records.append(
            {
                "doc_id": doc_id,
                "pattern": "arrow_bullet",
                "context": context,
                "before": m.group("before").strip(),
                "after": m.group("after").strip(),
            }
        )
    return records


def extract_add_remove(doc_id: str, lines: list[str]) -> list[dict[str, object]]:
    records = []
    for line in lines:
        m = ADD_REMOVE_RE.match(line.strip())
        if not m:
            continue
        records.append(
            {
                "doc_id": doc_id,
                "pattern": "prose_add_remove",
                "subject": m.group("subject").strip(),
                "detail": m.group("detail").strip(),
                "change_type": m.group("verb"),
            }
        )
    return records


def extract_before_after_blocks(doc_id: str, lines: list[str]) -> list[dict[str, object]]:
    records = []
    for i, line in enumerate(lines):
        if line.strip() != "변경 전":
            continue
        if i + 1 >= len(lines) or lines[i + 1].strip() != "변경 후":
            continue

        # collect the body until a blank line or the next "- '...' 스킬 개화" bullet
        body: list[str] = []
        j = i + 2
        while j < len(lines):
            stripped = lines[j].strip()
            if stripped == "" or stripped.startswith("- '") or stripped.startswith("버그수정"):
                break
            body.append(stripped)
            j += 1

        bracket_positions = [k for k, text in enumerate(body) if BRACKET_RE.match(text)]
        if len(bracket_positions) < 2:
            continue
        # first bracket marks start of "before" block, second marks start of "after" block
        before_block = body[bracket_positions[0]: bracket_positions[1]]
        after_block = body[bracket_positions[1]:]

        skill_name = BRACKET_RE.match(body[bracket_positions[0]]).group("name")
        records.append(
            {
                "doc_id": doc_id,
                "pattern": "before_after_block",
                "skill_or_option": skill_name,
                "before_block_text": " / ".join(before_block[1:]),
                "after_block_text": " / ".join(after_block[1:]),
            }
        )
    return records


def main() -> None:
    all_records: list[dict[str, object]] = []
    for path in sorted(DOC_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        doc_id = path.stem.split("_")[0]

        all_records.extend(extract_arrow_pairs(doc_id, lines))
        all_records.extend(extract_add_remove(doc_id, lines))
        all_records.extend(extract_before_after_blocks(doc_id, lines))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(all_records, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[DONE] extracted {len(all_records)} candidate records from {DOC_DIR}")
    by_pattern: dict[str, int] = {}
    for r in all_records:
        by_pattern[r["pattern"]] = by_pattern.get(r["pattern"], 0) + 1
    for pattern, count in by_pattern.items():
        print(f"  {pattern}: {count}")
    print(f"[DONE] saved: {OUTPUT}")

    if HAND_RECORDS.exists():
        hand = json.loads(HAND_RECORDS.read_text(encoding="utf-8"))
        print(f"[REF] hand-authored records: {len(hand)} (see {HAND_RECORDS})")


if __name__ == "__main__":
    main()
