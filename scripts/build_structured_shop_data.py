from __future__ import annotations

import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DOC_DIR = BASE_DIR / "data" / "processed_md"
OUTPUT_FILE = BASE_DIR / "data" / "structured" / "shop_items.json"

SHOP_ITEM_NAMES = (
    "태초 광휘의 의지",
    "태초 소울 1개 상자",
    "에픽 소울 1개 상자",
    "영롱한 조율의 추 1개 상자",
    "광휘의 잔영 1개 상자 (계정귀속)",
)

SECTION_END_MARKERS = (
    "개선 및 변경 사항",
    "버그수정",
    "아포칼립스 : 안티엔바이 1,2단계 클리어",
    "아포칼립스 : 안티엔바이 1, 2단계 클리어",
)


def extract_doc_id(path: Path) -> str:
    match = re.match(r"((?:DOC|DNF)-\d+)_", path.name)
    return match.group(1) if match else path.stem


def iter_processed_doc_paths() -> list[Path]:
    return sorted(
        {
            *DOC_DIR.glob("DOC-*.md"),
            *DOC_DIR.glob("DNF-*.md"),
        }
    )


def clean_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip() and line.strip() != "---"]


def extract_title(lines: list[str], doc_id: str) -> str:
    if lines and lines[0].startswith("# "):
        return lines[0].lstrip("# ").strip()
    return doc_id


def parse_price(price_text: str) -> dict[str, object]:
    match = re.search(r"(.+?)\s*(\d[\d,]*)개", price_text)
    if not match:
        return {
            "price_currency": "",
            "price_quantity": None,
            "price_text": price_text,
        }

    return {
        "price_currency": match.group(1).strip(),
        "price_quantity": int(match.group(2).replace(",", "")),
        "price_text": price_text,
    }


def parse_limit(limit_text: str) -> dict[str, object]:
    period = ""
    if "월" in limit_text:
        period = "monthly"
    elif "주" in limit_text:
        period = "weekly"
    elif "1회" in limit_text:
        period = "once"

    match = re.search(r"(\d+)회", limit_text)
    count = int(match.group(1)) if match else None

    return {
        "purchase_limit_period": period,
        "purchase_limit_count": count,
        "purchase_limit_text": limit_text,
    }


def parse_shop_section(lines: list[str], doc_id: str, title: str) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    item_name_set = set(SHOP_ITEM_NAMES)

    for index, line in enumerate(lines):
        if line not in item_name_set:
            continue

        # Only parse shop rows that are followed by price/limit fields.
        # In the flattened Markdown, each row ends at the first "계정당 ..." limit line.
        block: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line in item_name_set or next_line in SECTION_END_MARKERS:
                break
            block.append(next_line)
            if next_line.startswith("계정당"):
                break

        price_line = next((item for item in block if re.match(r"^광휘의\s*잔영\s*\d", item)), "")
        limit_line = next((item for item in block if item.startswith("계정당")), "")
        trade_type = next((item for item in block if item in {"계정귀속", "교환불가"}), "")
        carryover = next((item for item in block if "이월" in item), "")

        if not price_line or not limit_line:
            continue

        description_parts = [
            item
            for item in block
            if item not in {price_line, limit_line, trade_type}
            and not item.startswith("<구매 가능 횟수>")
            and not item.startswith("- 월")
            and "이월" not in item
        ]

        price = parse_price(price_line)
        limit = parse_limit(limit_line)

        records.append(
            {
                "record_id": f"{doc_id}-SHOP-{len(records) + 1:02d}",
                "doc_id": doc_id,
                "title": title,
                "table_type": "npc_shop_item",
                "npc": "켈돈 자비",
                "item_name": line,
                "description": " ".join(description_parts),
                "trade_type": trade_type,
                "carryover_text": carryover,
                **price,
                **limit,
            }
        )

    return records


def main() -> None:
    all_records: list[dict[str, object]] = []

    for path in iter_processed_doc_paths():
        doc_id = extract_doc_id(path)
        lines = clean_lines(path.read_text(encoding="utf-8"))
        title = extract_title(lines, doc_id)
        all_records.extend(parse_shop_section(lines, doc_id, title))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(all_records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"[DONE] structured shop records={len(all_records)} saved={OUTPUT_FILE}")


if __name__ == "__main__":
    main()
