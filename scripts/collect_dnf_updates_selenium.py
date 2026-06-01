from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
import argparse
import csv
import re
import time
import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


# ============================================================
# 1. 프로젝트 기본 경로 설정
# ============================================================
# 현재 파일:
# dnf-llm-eval/scripts/collect_dnf_updates_selenium.py
#
# BASE_DIR:
# 프로젝트 루트 디렉터리. 실제 경로는 __file__ 기준으로 자동 계산된다.
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw_html"
MD_DIR = DATA_DIR / "processed_md"

DISCOVERED_FILE = DATA_DIR / "discovered_update_urls.csv"
META_FILE = DATA_DIR / "metadata.csv"
DEBUG_HTML_FILE = DATA_DIR / "debug_update_list_selenium.html"
DEBUG_ONCLICK_FILE = DATA_DIR / "debug_onclicks.csv"

RAW_DIR.mkdir(parents=True, exist_ok=True)
MD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2. 수집 대상 URL
# ============================================================

BASE_URL = "https://df.nexon.com"
UPDATE_LIST_URL = "https://df.nexon.com/community/news/update/list"


# ============================================================
# 3. requests용 header
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; dnf-llm-eval-project/0.3; educational use)"
}


# ============================================================
# 4. 파일명 정리 함수
# ============================================================
# Windows에서 파일명으로 쓸 수 없는 문자 제거
# ============================================================

def clean_filename(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]", "_", text)
    text = re.sub(r"\s+", "_", text.strip())
    return text[:90]


# ============================================================
# 5. 상세 페이지 HTML 가져오기
# ============================================================
# 목록 페이지는 Selenium으로 찾고,
# 상세 페이지 저장은 requests로 빠르게 처리함.
# ============================================================

def fetch_page(url: str) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response.text


# ============================================================
# 6. 문서 유형 추론
# ============================================================
# 제목/카테고리 기반으로 문서 타입 자동 분류
# ============================================================

def infer_doc_type(title: str, category: str = "") -> str:
    text = f"{category} {title}"

    if "퍼스트" in text:
        return "first_server"

    if "던파ON" in text:
        return "df_on"

    if "대규모" in text or "시즌" in title or "Act" in title:
        return "major_update"

    if "주요" in text:
        return "main_update"

    if "정기점검" in title:
        return "regular_update"

    return "update"


# ============================================================
# 7. 상세 페이지 제목 추출
# ============================================================

def extract_title_from_detail(html: str, fallback_title: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.select_one("h3")

    if title_tag:
        title = title_tag.get_text(" ", strip=True)
        if title:
            return title

    return fallback_title


# ============================================================
# 8. 상세 페이지 본문만 추출
# ============================================================
# 메뉴, 로그인, footer를 제외하고 실제 공지 본문만 가져옴.
# ============================================================

def extract_article_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    content = (
        soup.select_one("div.operation_guide")
        or soup.select_one("div.bd_viewcont")
        or soup.select_one("article.bview_btarea")
        or soup.select_one("section.content.news")
    )

    if content is None:
        content = soup

    body_text = content.get_text("\n")

    lines = [line.strip() for line in body_text.splitlines()]
    lines = [line for line in lines if line]

    category_words = {"업데이트", "이벤트", "개발자노트", "공지사항", "퍼스트서버"}

    if lines and lines[0] in category_words:
        lines = lines[1:]

    return "\n".join(lines)


# ============================================================
# 9. Selenium 브라우저 준비
# ============================================================
# show_browser 옵션:
# - False면 브라우저 창을 숨김
# - True면 브라우저 창을 실제로 보여줌
#
# 처음 디버깅할 때는 --show-browser 추천
# ============================================================

def make_driver(show_browser: bool = False):
    options = Options()

    if not show_browser:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    return driver


# ============================================================
# 10. onclick 또는 href에서 상세 공지 번호 추출
# ============================================================
# 던파 목록 페이지는 일반 href가 아니라 onclick/js 방식일 수 있음.
#
# 예시 가능성:
# - /community/news/update/2927399
# - goView('2927399')
# - fnView(2927399)
#
# 그래서 href, onclick, outerHTML 전체에서 숫자 ID를 찾음.
# ============================================================

def extract_update_id_from_element_text(raw: str) -> str:
    if not raw:
        return ""

    # 패턴 1: /community/news/update/2927399
    m = re.search(r"/community/news/update/(\d+)", raw)
    if m:
        return m.group(1)

    # 패턴 2: update/2927399
    m = re.search(r"update/(\d+)", raw)
    if m:
        return m.group(1)

    # 패턴 3: onclick 안에 들어 있는 6자리 이상 숫자
    # 예: goView('2927399')
    m = re.search(r"['\"](\d{6,})['\"]", raw)
    if m:
        return m.group(1)

    m = re.search(r"\((\d{6,})\)", raw)
    if m:
        return m.group(1)

    return ""


# ============================================================
# 11. 부모 영역 텍스트에서 카테고리/날짜 추출
# ============================================================

def infer_category_from_text(text: str) -> str:
    for candidate in ["대규모", "주요", "일반", "퍼스트서버", "던파ON"]:
        if candidate in text:
            return candidate
    return ""


def infer_posted_date_from_text(text: str) -> str:
    m = re.search(r"20\d{2}\.\d{2}\.\d{2}", text)
    return m.group(0) if m else ""


def normalize_posted_date(raw_date: str, title: str) -> str:
    raw_date = raw_date.strip()

    if re.fullmatch(r"20\d{2}\.\d{2}\.\d{2}", raw_date):
        return raw_date

    # 최신 글은 목록에서 날짜 대신 15:00 같은 시간만 표시될 수 있다.
    # 이 경우 제목의 5/28(목) 패턴을 이용해 게시일을 보정한다.
    m = re.search(r"(\d{1,2})/(\d{1,2})", title)
    if m:
        month = int(m.group(1))
        day = int(m.group(2))
        year = datetime.now().year
        return f"{year}.{month:02d}.{day:02d}"

    return raw_date


# ============================================================
# 12. Selenium으로 업데이트 상세 링크 자동 발견
# ============================================================
# 핵심 함수.
#
# 1. 업데이트 목록 페이지를 실제 브라우저로 열기
# 2. 렌더링 완료 후 page_source 저장
# 3. a[href], [onclick] 요소를 모두 검사
# 4. href/onclick/outerHTML에서 update ID 추출
# 5. 상세 URL을 직접 조립
# ============================================================

def discover_update_links_with_selenium(show_browser: bool = False) -> list[dict]:
    """
    Selenium으로 업데이트 목록 페이지를 연 뒤,
    article.board_list.news_list 안의 ul 목록을 읽어서
    data-no 기반으로 상세 업데이트 URL을 만든다.

    던파 업데이트 목록은 일반적인 <a href="..."> 구조가 아니라,
    아래처럼 li.title에 data-no가 들어 있다.

    예:
    <li class="category">퍼스트서버</li>
    <li class="title" data-no="2927399">5/20(수) 퍼스트 서버 업데이트 안내</li>
    <li class="date">2026.05.20</li>

    그래서 href/onclick을 찾는 방식이 아니라 data-no를 읽어야 한다.
    """

    driver = make_driver(show_browser=show_browser)

    try:
        print("[BROWSER] 업데이트 목록 페이지 열기")
        print(f"          {UPDATE_LIST_URL}")

        driver.get(UPDATE_LIST_URL)

        # 페이지 렌더링 대기
        time.sleep(3)

        # 디버그용 HTML 저장
        page_source = driver.page_source
        DEBUG_HTML_FILE.write_text(page_source, encoding="utf-8")

        print(f"[DEBUG] 렌더링된 HTML 저장: {DEBUG_HTML_FILE}")

        # Selenium으로 받은 HTML을 BeautifulSoup으로 다시 파싱
        soup = BeautifulSoup(page_source, "html.parser")

        # 업데이트 목록 영역 찾기
        list_area = soup.select_one("article.board_list.news_list")

        if list_area is None:
            print("[ERROR] article.board_list.news_list 영역을 찾지 못했습니다.")
            return []

        found = []
        seen_urls = set()

        # 목록의 각 ul이 하나의 공지 행
        for item in list_area.select("ul"):
            category_tag = item.select_one("li.category")
            title_tag = item.select_one("li.title")
            date_tag = item.select_one("li.date")

            if title_tag is None:
                continue

            # data-no가 상세 글 번호
            data_no = title_tag.get("data-no", "").strip()

            # 대규모 업데이트는 data-url이 별도로 있는 경우가 있음
            data_url = title_tag.get("data-url", "").strip()

            title = title_tag.get_text(" ", strip=True)
            category = category_tag.get_text(" ", strip=True) if category_tag else ""
            raw_posted_date = date_tag.get_text(" ", strip=True) if date_tag else ""
            posted_date = normalize_posted_date(raw_posted_date, title)

            if not title:
                continue

            # 상세 URL 만들기
            if data_url:
                # 예: /pr/actupdate/MDAxNzE
                detail_url = urljoin(BASE_URL, data_url)
            elif data_no:
                # 예: /community/news/update/2927399?categoryType=0
                detail_url = f"{BASE_URL}/community/news/update/{data_no}?categoryType=0"
            else:
                continue

            if detail_url in seen_urls:
                continue

            seen_urls.add(detail_url)

            found.append({
                "title": title,
                "url": detail_url,
                "category": category,
                "posted_date": posted_date,
            })

        print(f"[DEBUG] 목록에서 {len(found)}개 공지 발견")

        # 디버그 CSV 저장
        with open(DEBUG_ONCLICK_FILE, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["title", "category", "posted_date", "url"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(found)

        print(f"[DEBUG] 발견한 공지 목록 저장: {DEBUG_ONCLICK_FILE}")

        return found

    finally:
        driver.quit()


# ============================================================
# 13. CSV 저장 함수
# ============================================================

def save_discovered_links(rows: list[dict]):
    with open(DISCOVERED_FILE, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = ["doc_id", "doc_type", "category", "posted_date", "title", "url"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_metadata(rows: list[dict]):
    with open(META_FILE, "w", newline="", encoding="utf-8-sig") as f:
        fieldnames = [
            "doc_id",
            "doc_type",
            "category",
            "posted_date",
            "title",
            "url",
            "fetched_at",
            "raw_path",
            "processed_path",
            "status",
            "error",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def make_doc_id(index: int) -> str:
    return f"DOC-{index:02d}"


def to_project_relative_path(path: Path) -> str:
    return path.relative_to(BASE_DIR).as_posix()


# ============================================================
# 14. 메인 실행 함수
# ============================================================

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--max", type=int, default=5, help="수집할 최대 문서 수")
    parser.add_argument("--sleep", type=float, default=1.5, help="요청 사이 대기 시간")

    parser.add_argument(
        "--type",
        type=str,
        default="all",
        choices=[
            "all",
            "first_server",
            "regular_update",
            "major_update",
            "main_update",
            "df_on",
            "update",
        ],
        help="수집할 문서 유형 필터"
    )

    parser.add_argument(
        "--show-browser",
        action="store_true",
        help="브라우저 창을 실제로 보여주며 실행"
    )

    args = parser.parse_args()
    fetched_at = datetime.now().isoformat(timespec="seconds")

    # 1. Selenium으로 상세 링크 발견
    discovered = discover_update_links_with_selenium(show_browser=args.show_browser)

    if not discovered:
        print()
        print("[ERROR] Selenium으로도 업데이트 상세 링크를 찾지 못했습니다.")
        print(f"        디버그 HTML 확인: {DEBUG_HTML_FILE}")
        print(f"        onclick/href 후보 확인: {DEBUG_ONCLICK_FILE}")
        return

    # 2. 문서 유형 추론 및 필터링
    rows = []

    for item in discovered:
        doc_type = infer_doc_type(item["title"], item["category"])

        if args.type != "all" and doc_type != args.type:
            continue

        rows.append({
            "doc_id": "",
            "doc_type": doc_type,
            "category": item["category"],
            "posted_date": item["posted_date"],
            "title": item["title"],
            "url": item["url"],
        })

    # 3. 최대 개수 제한
    rows = rows[:args.max]

    # 4. doc_id 부여
    for i, row in enumerate(rows, start=1):
        row["doc_id"] = make_doc_id(i)

    save_discovered_links(rows)

    print()
    print(f"[DISCOVERED] {len(rows)}개 상세 URL 발견")
    print(f"[SAVED] {DISCOVERED_FILE}")

    metadata_rows = []

    # 5. 상세 페이지 수집
    for row in rows:
        doc_id = row["doc_id"]
        doc_type = row["doc_type"]
        category = row["category"]
        posted_date = row["posted_date"]
        title_from_list = row["title"]
        url = row["url"]

        print()
        print(f"[FETCH] {doc_id} | {doc_type} | {title_from_list}")
        print(f"        {url}")

        try:
            html = fetch_page(url)

            title = title_from_list
            text = extract_article_text(html)

            safe_title = clean_filename(title)

            raw_path = RAW_DIR / f"{doc_id}_{safe_title}.html"
            md_path = MD_DIR / f"{doc_id}_{safe_title}.md"

            raw_path.write_text(html, encoding="utf-8")

            md_content = f"""# {title}

- doc_id: {doc_id}
- doc_type: {doc_type}
- category: {category}
- posted_date: {posted_date}
- source_url: {url}
- fetched_at: {fetched_at}

---

{text}
"""

            md_path.write_text(md_content, encoding="utf-8")

            metadata_rows.append({
                "doc_id": doc_id,
                "doc_type": doc_type,
                "category": category,
                "posted_date": posted_date,
                "title": title,
                "url": url,
                "fetched_at": fetched_at,
                "raw_path": to_project_relative_path(raw_path),
                "processed_path": to_project_relative_path(md_path),
                "status": "success",
                "error": "",
            })

            print(f"[OK] 저장 완료: {md_path}")

            time.sleep(args.sleep)

        except Exception as e:
            print(f"[ERROR] {doc_id}: {e}")

            metadata_rows.append({
                "doc_id": doc_id,
                "doc_type": doc_type,
                "category": category,
                "posted_date": posted_date,
                "title": title_from_list,
                "url": url,
                "fetched_at": fetched_at,
                "raw_path": "",
                "processed_path": "",
                "status": "failed",
                "error": str(e),
            })

    save_metadata(metadata_rows)

    print()
    print(f"[DONE] metadata saved to {META_FILE}")


if __name__ == "__main__":
    main()
