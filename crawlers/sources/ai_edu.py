"""AI·디지털 교육 강사 특화 소스 크롤러

AI 강사 공고의 실제 발원지를 직접 크롤링한다:
- SW미래채움 통합포털 (sweduhub.or.kr) — 13개 지역센터 SW·AI 강사 공고 집약
- 디지털배움터 (NIA) — 전국 디지털역량교육 강사 모집 통합공고
- 시청자미디어재단 (kcmf.or.kr) — 미디어교육 강사 모집
- 제주평생교육장학진흥원 (jiles.or.kr) — 도민 강사/평생교육 강사
- 제주콘텐츠진흥원 (ofjeju.kr) — 웹툰·미디어 강사풀

제주테크노파크(jejutp.or.kr)는 robots.txt가 Disallow: / (전체 금지)라 제외.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import time
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

REGIONS = [
    "서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]

# 게시일 기준 이보다 오래된 공고는 수집하지 않음 (마감일 없는 게시판 대응)
FRESH_DAYS = 120

_FULL_DATE = re.compile(r"(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})")


def _parse_ymd(raw: str) -> str:
    """'2026.06.29' / '2026-06-29' / ISO8601 → '2026-06-29'"""
    m = _FULL_DATE.search(str(raw or ""))
    if not m:
        return ""
    return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"


def _is_fresh(posted_iso: str) -> bool:
    """게시일이 FRESH_DAYS 이내인가 (파싱 실패 시 보수적으로 통과)"""
    if not posted_iso:
        return True
    try:
        posted = datetime.strptime(posted_iso, "%Y-%m-%d")
    except ValueError:
        return True
    return posted >= datetime.now() - timedelta(days=FRESH_DAYS)


def _deadline_from_title(title: str, posted_iso: str = "") -> str:
    """제목 안의 마감 표기 추출. '(~5.11, 17:00까지)' 류는 게시 연도로 보정."""
    # 연도 포함 풀 날짜 + 마감 신호
    if "까지" in title or "~" in title or "~" in title:
        m = _FULL_DATE.search(title)
        if m:
            return f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        # 연도 없는 ~M.D 표기
        m2 = re.search(r"[~~]\s*(\d{1,2})\s*[./]\s*(\d{1,2})", title)
        if m2 and posted_iso:
            return f"{posted_iso[:4]}-{int(m2.group(1)):02d}-{int(m2.group(2)):02d}"
    return ""


# ─────────────────────────────────────────────
# 1. SW미래채움 통합포털 — 13개 지역센터 SW·AI 강사 공고
# ─────────────────────────────────────────────
def crawl_sweduhub(pages: int = 3) -> list[JobPosting]:
    """sweduhub.or.kr 공지사항에서 제목 '강사' 검색 (서버측 검색 지원).

    React SPA지만 공개 JSON API(POST /api/post/list)가 열려 있다.
    robots.txt 전체 허용 확인됨.
    """
    results: list[JobPosting] = []
    api = "https://sweduhub.or.kr/api/post/list"
    seen_no: set = set()  # 고정공지(isFixed)가 페이지마다 반복 → postNo로 중복 제거

    for page in range(1, pages + 1):
        try:
            resp = httpx.post(api, json={
                "boardType": "notice", "region": "ALL",
                "searchType": "title", "search": "강사",
                "pageNo": page, "pageSize": 50, "inOrder": "DESC",
            }, headers={**HEADERS, "Content-Type": "application/json"}, timeout=15)
            resp.raise_for_status()
            posts = (resp.json().get("data") or {}).get("posts") or []
        except Exception as e:
            print(f"  SW미래채움 p{page} 오류: {e}")
            break

        if not posts:
            break

        for p in posts:
            title = (p.get("title") or "").strip()
            if not title:
                continue
            if p.get("postNo") in seen_no:
                continue
            seen_no.add(p.get("postNo"))
            # 모집/채용성 공고만 (일정 안내, 커리큘럼 안내, 개념서 배부 등 제외)
            if not any(kw in title for kw in ["모집", "채용", "위촉", "공고", "자격시험"]):
                continue
            posted = _parse_ymd(p.get("createDate", ""))
            if not _is_fresh(posted):
                continue

            region = (p.get("region") or "").strip()
            if region not in REGIONS:
                region = next((r for r in REGIONS if r in title), "")

            deadline = _deadline_from_title(title, posted)
            post_no = p.get("postNo")

            results.append(JobPosting(
                title=title,
                organization=f"{region} SW미래채움" if region else "SW미래채움",
                org_type="quasi_gov", org_sub_type="SW미래채움",
                region=region,
                deadline_text=deadline or "채용시까지",
                deadline_type="fixed" if deadline else "until_filled",
                published_at=posted,
                source_url=f"https://www.sweduhub.or.kr/notice/detail/{post_no}",
                source_name="SW미래채움",
                apply_url=f"https://www.sweduhub.or.kr/notice/detail/{post_no}",
            ))

        print(f"  SW미래채움 p{page}: 누적 {len(results)}건")
        time.sleep(1)

    return results


# ─────────────────────────────────────────────
# 2. 디지털배움터 (NIA) — 공지사항의 강사 모집 공고
# ─────────────────────────────────────────────
def crawl_digital_baeumteo() -> list[JobPosting]:
    """디지털배움터 공지사항(bbs_id=5) JSON API.

    x-nia-header / x-nia-token 헤더가 빈 값이라도 반드시 있어야 한다.
    연 1~2건꼴 강사 모집이라 1요청(psize=100)으로 전체 커버.
    """
    results: list[JobPosting] = []
    host = "https://www.xn--2z1bw8k1pjz5ccumkb.kr"  # www.디지털배움터.kr

    try:
        resp = httpx.post(f"{host}/api/cmm/front/board/list.do", data={
            "page_no": "1", "psize": "100", "bbs_id": "5",
            "sch_type_cd": "", "sch_date_cd": "", "sch_st_dt": "", "sch_end_dt": "",
            "sch_key_cd": "", "sch_key": "",
        }, headers={**HEADERS, "x-nia-header": "", "x-nia-token": ""}, timeout=15)
        resp.raise_for_status()
        rows = resp.json().get("RK_RESULT_BBS_ATCL") or []
    except Exception as e:
        print(f"  디지털배움터 오류: {e}")
        return results

    for r in rows:
        title = (r.get("title") or "").strip()
        if not title or not any(kw in title for kw in ["강사", "튜터"]):
            continue
        # 주의: 이 게시판의 close_yn은 최신 글도 'Y'라 마감 지표가 아님 — 사용 금지
        posted = _parse_ymd(r.get("reg_dtm_ymd", ""))
        if not _is_fresh(posted):
            continue

        no = r.get("bbs_atcl_no")
        detail = f"{host}/cmm/front/boarddetail/5.do?bbs_atcl_no={no}&titlename=공지사항"
        deadline = _deadline_from_title(title, posted)

        results.append(JobPosting(
            title=title,
            organization="디지털배움터(한국지능정보사회진흥원)",
            org_type="quasi_gov", org_sub_type="디지털배움터",
            region=next((rg for rg in REGIONS if rg in title), ""),
            deadline_text=deadline or "채용시까지",
            deadline_type="fixed" if deadline else "until_filled",
            published_at=posted,
            source_url=detail,
            source_name="디지털배움터",
            apply_url=detail,
        ))

    print(f"  디지털배움터: {len(results)}건")
    return results


# ─────────────────────────────────────────────
# 3. 시청자미디어재단 — 미디어교육 강사 모집 (본부 공지)
# ─────────────────────────────────────────────
def crawl_kcmf(pages: int = 3) -> list[JobPosting]:
    """kcmf.or.kr 본부 공지사항. 강사 모집은 매년 1~3월 집중.

    고정공지가 모든 페이지에 반복되므로 글ID로 중복 제거.
    """
    results: list[JobPosting] = []
    board = "https://kcmf.or.kr/KCMF/contents/KCMF020100.do"
    seen_ids: set[str] = set()

    for page in range(1, pages + 1):
        try:
            resp = httpx.get(board, params={"page": page, "viewCount": 30},
                             headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"  시청자미디어재단 p{page} 오류: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("table.board tbody tr")
        if not rows:
            break

        for row in rows:
            tds = row.select("td")
            if len(tds) < 5:
                continue
            link = tds[1].select_one("a")
            if not link:
                continue
            title = link.get_text(strip=True)
            # 강사 모집만 (직원채용·수강생모집·발표문 제외)
            if "강사" not in title:
                continue
            if not any(kw in title for kw in ["모집", "공고", "채용"]):
                continue

            id_m = re.search(r"fn_goView\('(\d+)'\)", link.get("onclick", ""))
            post_id = id_m.group(1) if id_m else ""
            if post_id and post_id in seen_ids:
                continue
            if post_id:
                seen_ids.add(post_id)

            posted = _parse_ymd(tds[4].get_text(strip=True))
            if not _is_fresh(posted):
                continue

            detail = f"{board}?schM=view&page=1&viewCount=10&id={post_id}" if post_id else board
            deadline = _deadline_from_title(title, posted)

            results.append(JobPosting(
                title=title,
                organization="시청자미디어재단",
                org_type="quasi_gov", org_sub_type="미디어센터",
                region=next((rg for rg in REGIONS if rg in title), ""),
                deadline_text=deadline or "채용시까지",
                deadline_type="fixed" if deadline else "until_filled",
                published_at=posted,
                source_url=detail,
                source_name="시청자미디어재단",
                apply_url=detail,
            ))

        print(f"  시청자미디어재단 p{page}: 누적 {len(results)}건")
        time.sleep(1)

    return results


# ─────────────────────────────────────────────
# 4. 제주 준관공서 게시판 (같은 CMS 계열 2곳)
# ─────────────────────────────────────────────
def _crawl_jeju_board(name: str, list_url: str, params: dict,
                      date_sel: str, org_name: str, sub_type: str) -> list[JobPosting]:
    """jiles/ofjeju 공용 파서 — table.table-list 계열 CMS"""
    results: list[JobPosting] = []
    try:
        resp = httpx.get(list_url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  {name} 오류: {e}")
        return results

    soup = BeautifulSoup(resp.text, "lxml")
    # 데스크톱/모바일 테이블이 공존 (모바일=table.m-table-list.table-list) → 데스크톱만
    rows = soup.select("table.table-list:not(.m-table-list) tbody tr")

    for row in rows:
        title_td = row.select_one("td.title")
        if not title_td:
            continue
        link = title_td.select_one("a")
        if not link:
            continue
        # 제목이 ..으로 잘리는 경우 title 속성이 풀 텍스트
        title = (link.get("title") or title_td.get("title") or link.get_text(strip=True)).strip()
        if "강사" not in title:
            continue
        # 모집성 공고만 (심사 결과·선정 결과 안내문 제외)
        if not any(kw in title for kw in ["모집", "채용", "위촉", "공고"]):
            continue
        if "결과" in title:
            continue

        date_td = row.select_one(date_sel)
        posted = _parse_ymd(date_td.get_text(strip=True)) if date_td else ""
        if not posted:  # 날짜 없는 행 = 반복 고정공지 → 스킵
            continue
        if not _is_fresh(posted):
            continue

        href = link.get("href", "")
        detail = href if href.startswith("http") else f"{list_url.split('/community')[0]}{href}"
        deadline = _deadline_from_title(title, posted)

        results.append(JobPosting(
            title=title,
            organization=org_name,
            org_type="quasi_gov", org_sub_type=sub_type,
            region="제주",
            deadline_text=deadline or "채용시까지",
            deadline_type="fixed" if deadline else "until_filled",
            published_at=posted,
            source_url=detail,
            source_name=name,
            apply_url=detail,
        ))

    print(f"  {name}: {len(results)}건")
    return results


def crawl_jeju_quasi_gov(pages: int = 2) -> list[JobPosting]:
    """제주평생교육장학진흥원 + 제주콘텐츠진흥원 공지 게시판 (제목 '강사' 검색)"""
    collected: list[JobPosting] = []

    for page in range(1, pages + 1):
        # 제주평생교육장학진흥원 — 도민 강사/평생교육 강사
        collected.extend(_crawl_jeju_board(
            "제주평생교육장학진흥원",
            "https://www.jiles.or.kr/community/notice/notice.htm",
            {"qtype": "title", "query": "강사", "page": page},
            "td.wdate",
            "제주평생교육장학진흥원", "평생교육",
        ))
        time.sleep(1)
        # 제주콘텐츠진흥원 — 웹툰·미디어 강사풀
        collected.extend(_crawl_jeju_board(
            "제주콘텐츠진흥원",
            "https://www.ofjeju.kr/communication/notifications.htm",
            {"qType": "title", "q": "강사", "page": page},
            "td.date",
            "제주콘텐츠진흥원", "콘텐츠진흥원",
        ))
        time.sleep(1)

    # 페이지 간 고정공지 반복 대비 URL 중복 제거
    seen_urls: set = set()
    results: list[JobPosting] = []
    for j in collected:
        if j.source_url in seen_urls:
            continue
        seen_urls.add(j.source_url)
        results.append(j)
    return results


# ─────────────────────────────────────────────
# 통합 실행
# ─────────────────────────────────────────────
def crawl_all_ai_edu() -> list[JobPosting]:
    all_jobs: list[JobPosting] = []
    print("  → SW미래채움 통합포털...")
    all_jobs.extend(crawl_sweduhub())
    print("  → 디지털배움터(NIA)...")
    all_jobs.extend(crawl_digital_baeumteo())
    print("  → 시청자미디어재단...")
    all_jobs.extend(crawl_kcmf())
    print("  → 제주 준관공서 (평생교육진흥원/콘텐츠진흥원)...")
    all_jobs.extend(crawl_jeju_quasi_gov())
    return all_jobs


if __name__ == "__main__":
    jobs = crawl_all_ai_edu()
    print(f"\n✅ AI·디지털 교육 특화 소스: {len(jobs)}건")
    for j in jobs[:20]:
        print(f"  ~{j.deadline_text} [{j.region or '?'}] {j.title[:55]} | {j.source_name}")
