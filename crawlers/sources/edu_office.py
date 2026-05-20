"""시도교육청 공지사항/채용 게시판 크롤러 — 강사 모집 공고 수집"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

TEACHER_KW = ["강사", "멘토", "코치", "튜터", "교관", "특강", "강의", "교원", "교사", "방과후", "늘봄", "지도사"]

EXCLUDE_KW = [
    "합격자", "발표", "면접결과", "서류전형", "최종합격",
    "교장", "교감", "전임교원", "시설관리", "미화", "경비",
]

REGIONS = [
    "서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]


def _is_teacher_post(title: str) -> bool:
    """제목에 강사 관련 키워드가 있는지 확인"""
    return any(kw in title for kw in TEACHER_KW)


def _is_excluded(title: str) -> bool:
    """제외 키워드 확인"""
    return any(kw in title for kw in EXCLUDE_KW)


def _extract_region(text: str) -> str:
    for r in REGIONS:
        if r in text:
            return r
    return ""


# ─────────────────────────────────────────────
# 1. 서울시교육청 (SEN) — OpenWorks 4 게시판
# ─────────────────────────────────────────────
SEN_BOARDS = [
    # (게시판ID, 게시판명)
    ("1486", "채용공고"),
    ("1011", "공지사항"),
]

def crawl_sen(pages: int = 3) -> list[JobPosting]:
    """서울시교육청 게시판에서 강사 관련 공고 수집"""
    results = []
    base_url = "https://www.sen.go.kr/user/bbs/BD_selectBbsList.do"

    for bbs_id, bbs_name in SEN_BOARDS:
        for page in range(1, pages + 1):
            params = {
                "q_bbsSn": bbs_id,
                "q_currPage": str(page),
                "q_rowPerPage": "20",
            }
            try:
                resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
                resp.raise_for_status()
            except Exception as e:
                print(f"  서울교육청 {bbs_name} p{page} 오류: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("table.bd-list__tbl tbody tr")
            if not rows:
                break

            page_count = 0
            for row in rows:
                title_td = row.select_one("td.bbs_title")
                if not title_td:
                    continue
                link = title_td.select_one("a")
                if not link:
                    continue

                title = link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                if not _is_teacher_post(title):
                    continue
                if _is_excluded(title):
                    continue

                href = link.get("href", "")
                detail_url = f"https://www.sen.go.kr/user/bbs/{href}" if href.startswith("BD_") else f"https://www.sen.go.kr{href}"

                date_td = row.select_one("td.bbs_date")
                posted_date = date_td.get_text(strip=True) if date_td else ""

                # 마감일 추출 시도 (제목에서)
                deadline = ""
                dl_match = re.search(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", title)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

                job = JobPosting(
                    title=title,
                    organization="서울특별시교육청",
                    org_type="government",
                    org_sub_type="교육청",
                    region="서울",
                    deadline_text=deadline or posted_date,
                    published_at=posted_date,
                    source_url=detail_url,
                    source_name="서울교육청",
                    apply_url=detail_url,
                )
                results.append(job)
                page_count += 1

            print(f"  서울교육청 {bbs_name} p{page}: {page_count}건")
            if len(rows) < 10:
                break
            time.sleep(2)

    return results


# ─────────────────────────────────────────────
# 2. 경기도교육청 (GOE) — eGovFrame 게시판
# ─────────────────────────────────────────────
GOE_BOARDS = [
    # (mi, bbsId, 게시판명)
    ("10963", "2430", "공고등록부"),
]

def crawl_goe(pages: int = 3) -> list[JobPosting]:
    """경기도교육청 게시판에서 강사 관련 공고 수집"""
    results = []
    base_url = "https://www.goe.go.kr/goe/na/ntt/selectNttList.do"

    for mi, bbs_id, bbs_name in GOE_BOARDS:
        for page in range(1, pages + 1):
            params = {
                "mi": mi,
                "bbsId": bbs_id,
                "currPage": str(page),
            }
            try:
                resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
                resp.raise_for_status()
            except Exception as e:
                print(f"  경기교육청 {bbs_name} p{page} 오류: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("div.bbs_ListA table tbody tr")
            if not rows:
                # 대체 선택자
                rows = soup.select("table tbody tr")
            if not rows:
                break

            page_count = 0
            for row in rows:
                title_td = row.select_one("td.bbs_tit")
                if not title_td:
                    continue
                link = title_td.select_one("a.nttInfoBtn")
                if not link:
                    link = title_td.select_one("a")
                if not link:
                    continue

                title_em = link.select_one("em")
                title = title_em.get_text(strip=True) if title_em else link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                if not _is_teacher_post(title):
                    continue
                if _is_excluded(title):
                    continue

                # data-id에서 게시글 번호 추출
                data_id = link.get("data-id", "")
                detail_url = f"https://www.goe.go.kr/goe/na/ntt/selectNttInfo.do?mi={mi}&bbsId={bbs_id}&nttSn={data_id}" if data_id else base_url

                date_td = row.select_one("td[data-table='date']")
                posted_date = ""
                if date_td:
                    # em.mTit ("등록일") 제거 후 순수 날짜만 추출
                    em_label = date_td.select_one("em.mTit")
                    if em_label:
                        em_label.decompose()
                    posted_date = date_td.get_text(strip=True)

                deadline = ""
                dl_match = re.search(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", title)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

                job = JobPosting(
                    title=title,
                    organization="경기도교육청",
                    org_type="government",
                    org_sub_type="교육청",
                    region="경기",
                    deadline_text=deadline or posted_date,
                    published_at=posted_date,
                    source_url=detail_url,
                    source_name="경기교육청",
                    apply_url=detail_url,
                )
                results.append(job)
                page_count += 1

            print(f"  경기교육청 {bbs_name} p{page}: {page_count}건")
            if len(rows) < 10:
                break
            time.sleep(2)

    return results


# ─────────────────────────────────────────────
# 3. 인천시교육청 (ICE) — 채용공고 전용 게시판
# ─────────────────────────────────────────────
def crawl_ice(pages: int = 3) -> list[JobPosting]:
    """인천시교육청 채용공고 게시판에서 강사 관련 공고 수집"""
    results = []
    base_url = "https://www.ice.go.kr/ice/na/ntt/selectNttList.do"
    mi = "10997"
    bbs_id = "1981"

    for page in range(1, pages + 1):
        params = {
            "mi": mi,
            "bbsId": bbs_id,
            "currPage": str(page),
        }
        try:
            resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  인천교육청 채용 p{page} 오류: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("div.bbs_ListA table tbody tr")
        if not rows:
            rows = soup.select("table tbody tr")
        if not rows:
            break

        page_count = 0
        for row in rows:
            tds = row.select("td")
            if len(tds) < 5:
                continue

            title_td = row.select_one("td.bbs_tit")
            if not title_td:
                continue
            link = title_td.select_one("a.nttInfoBtn") or title_td.select_one("a")
            if not link:
                continue

            title_em = link.select_one("em")
            title = title_em.get_text(strip=True) if title_em else link.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if not _is_teacher_post(title):
                continue
            if _is_excluded(title):
                continue

            # 기관명 추출 (3번째 td)
            org_name = ""
            org_tds = row.select("td[data-table='write']")
            if len(org_tds) >= 2:
                org_name = org_tds[1].get_text(strip=True)  # 기관명

            data_id = link.get("data-id", "")
            detail_url = f"https://www.ice.go.kr/ice/na/ntt/selectNttInfo.do?mi={mi}&bbsId={bbs_id}&nttSn={data_id}" if data_id else base_url

            date_td = row.select_one("td[data-table='date']")
            posted_date = date_td.get_text(strip=True) if date_td else ""

            # 채용종료일 추출 (마지막 td들)
            deadline = ""
            for td in reversed(tds):
                text = td.get_text(strip=True)
                dl_match = re.search(r"(\d{4})[.\-](\d{1,2})[.\-](\d{1,2})", text)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"
                    break

            job = JobPosting(
                title=title,
                organization=org_name or "인천광역시교육청",
                org_type="school" if "학교" in org_name else "government",
                org_sub_type="교육청" if "학교" not in org_name else "학교",
                region="인천",
                deadline_text=deadline or posted_date,
                published_at=posted_date,
                source_url=detail_url,
                source_name="인천교육청",
                apply_url=detail_url,
            )
            results.append(job)
            page_count += 1

        print(f"  인천교육청 채용 p{page}: {page_count}건")
        if len(rows) < 10:
            break
        time.sleep(2)

    return results


# ─────────────────────────────────────────────
# 4. 부산시교육청 — 공지사항/채용
# ─────────────────────────────────────────────
def _extract_date_by_label(row, label: str) -> str:
    """eGovFrame 게시판에서 em.mTit 라벨로 날짜 추출 (PEN/DGE 등 data-table 미지원 사이트)"""
    for td in row.select("td"):
        em = td.select_one("em.mTit")
        if em and label in em.get_text(strip=True):
            # em 이후 텍스트 노드에서 날짜 추출
            text = td.get_text(strip=True).replace(em.get_text(strip=True), "").strip()
            return text
    return ""


def crawl_bse(pages: int = 3) -> list[JobPosting]:
    """부산시교육청 학교인력채용 게시판에서 강사 관련 공고 수집"""
    results = []
    base_url = "https://www.pen.go.kr/main/na/ntt/selectNttList.do"
    mi = "30367"
    bbs_id = "2364"

    for page in range(1, pages + 1):
        params = {"mi": mi, "bbsId": bbs_id, "currPage": str(page)}
        try:
            resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  부산교육청 p{page} 오류: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("table tbody tr")
        if not rows:
            break

        page_count = 0
        for row in rows:
            title_td = row.select_one("td.bbs_tit")
            if not title_td:
                continue
            link = title_td.select_one("a.nttInfoBtn") or title_td.select_one("a")
            if not link:
                continue

            title = link.get_text(strip=True)
            # 아이콘 등 제거
            for icon in link.select("span, img, i"):
                icon_text = icon.get_text(strip=True)
                if icon_text:
                    title = title.replace(icon_text, "").strip()
            if not title or len(title) < 5:
                continue
            if not _is_teacher_post(title):
                continue
            if _is_excluded(title):
                continue

            data_id = link.get("data-id", "")
            detail_url = f"https://www.pen.go.kr/main/na/ntt/selectNttInfo.do?mi={mi}&bbsId={bbs_id}&nttSn={data_id}" if data_id else base_url

            # PEN은 data-table 속성 미사용 → em.mTit 라벨로 추출
            posted_date = _extract_date_by_label(row, "등록일")

            # 접수기간에서 마감일 추출 시도
            deadline = ""
            period = _extract_date_by_label(row, "접수기간")
            if period:
                # "2026/05/18 ~ 2026/05/21" 패턴
                dates = re.findall(r"(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})", period)
                if len(dates) >= 2:
                    d = dates[-1]  # 종료일
                    deadline = f"{d[0]}-{d[1].zfill(2)}-{d[2].zfill(2)}"
                elif dates:
                    d = dates[0]
                    deadline = f"{d[0]}-{d[1].zfill(2)}-{d[2].zfill(2)}"

            if not deadline:
                dl_match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", title)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

            # 작성자에서 기관명 추출
            org_name = _extract_date_by_label(row, "작성자") or "부산광역시교육청"

            job = JobPosting(
                title=title,
                organization=org_name,
                org_type="school" if "학교" in org_name else "government",
                org_sub_type="학교" if "학교" in org_name else "교육청",
                region="부산",
                deadline_text=deadline or posted_date,
                published_at=posted_date,
                source_url=detail_url,
                source_name="부산교육청",
                apply_url=detail_url,
            )
            results.append(job)
            page_count += 1

        print(f"  부산교육청 p{page}: {page_count}건")
        if len(rows) < 10:
            break
        time.sleep(2)

    return results


# ─────────────────────────────────────────────
# 5. 대구시교육청
# ─────────────────────────────────────────────
def crawl_dge(pages: int = 3) -> list[JobPosting]:
    """대구시교육청 기간제교사/강사 게시판에서 강사 관련 공고 수집
    DGE는 SSO 인증이 필요해서 httpx.Client로 쿠키 체인을 유지해야 함"""
    results = []
    base_url = "https://www.dge.go.kr/main/na/ntt/selectNttList.do"
    mi = "5186"
    bbs_id = "1047"

    # SSO 세션 확보용 Client
    client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30)

    try:
        # SSO 체인 워밍업: 첫 요청으로 세션 쿠키 확보
        try:
            warmup = client.get(base_url, params={"mi": mi, "bbsId": bbs_id, "currPage": "1"})
            # JS redirect가 있으면 /sso/index.jsp 로 수동 이동
            if "sso" in warmup.text.lower() or warmup.status_code != 200:
                sso_url = "https://www.dge.go.kr/sso/index.jsp"
                client.get(sso_url)
                # SSO 완료 후 다시 본 페이지 요청
                warmup = client.get(base_url, params={"mi": mi, "bbsId": bbs_id, "currPage": "1"})
        except Exception as e:
            print(f"  대구교육청 SSO 초기화 오류: {e}")

        for page in range(1, pages + 1):
            params = {"mi": mi, "bbsId": bbs_id, "currPage": str(page)}
            try:
                if page == 1 and 'warmup' in dir() and warmup.status_code == 200:
                    resp = warmup  # 이미 1페이지 가져옴
                else:
                    resp = client.get(base_url, params=params)
                    resp.raise_for_status()
            except Exception as e:
                print(f"  대구교육청 p{page} 오류: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("table tbody tr")
            if not rows:
                break

            page_count = 0
            for row in rows:
                title_td = row.select_one("td.bbs_tit")
                if not title_td:
                    continue
                link = title_td.select_one("a.nttInfoBtn") or title_td.select_one("a")
                if not link:
                    continue

                title = link.get_text(strip=True)
                for icon in link.select("span, img, i"):
                    icon_text = icon.get_text(strip=True)
                    if icon_text:
                        title = title.replace(icon_text, "").strip()
                if not title or len(title) < 5:
                    continue
                if not _is_teacher_post(title):
                    continue
                if _is_excluded(title):
                    continue

                data_id = link.get("data-id", "")
                detail_url = f"https://www.dge.go.kr/main/na/ntt/selectNttInfo.do?mi={mi}&bbsId={bbs_id}&nttSn={data_id}" if data_id else base_url

                posted_date = _extract_date_by_label(row, "등록일")

                # 마감일 라벨에서 추출
                deadline = ""
                dl_text = _extract_date_by_label(row, "마감일")
                if dl_text:
                    dl_match = re.search(r"(\d{4})[/.\-](\d{1,2})[/.\-](\d{1,2})", dl_text)
                    if dl_match:
                        deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

                if not deadline:
                    dl_match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", title)
                    if dl_match:
                        deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

                # 작성자에서 기관명 추출
                org_name = _extract_date_by_label(row, "작성자") or "대구광역시교육청"

                job = JobPosting(
                    title=title,
                    organization=org_name,
                    org_type="school" if "학교" in org_name else "government",
                    org_sub_type="학교" if "학교" in org_name else "교육청",
                    region="대구",
                    deadline_text=deadline or posted_date,
                    published_at=posted_date,
                    source_url=detail_url,
                    source_name="대구교육청",
                    apply_url=detail_url,
                )
                results.append(job)
                page_count += 1

            print(f"  대구교육청 p{page}: {page_count}건")
            if len(rows) < 10:
                break
            time.sleep(2)
    finally:
        client.close()

    return results


# ─────────────────────────────────────────────
# 6. 제주특별자치도교육청 (JJE) — RFC3 기반 CMS (eGovFrame 아님)
# ─────────────────────────────────────────────
def crawl_jje(pages: int = 3) -> list[JobPosting]:
    """제주교육청 채용정보 게시판에서 강사 관련 공고 수집
    제주는 eGovFrame이 아닌 RFC3 기반 CMS를 사용하므로 별도 파싱 로직 필요"""
    results = []
    base_url = "https://www.jje.go.kr/board/list.jje"
    board_id = "BBS_0000507"
    menu_cd = "DOM_000000103003009000"

    for page in range(1, pages + 1):
        params = {
            "boardId": board_id,
            "menuCd": menu_cd,
            "startPage": str(page),
            "listRow": "20",
            "orderBy": "REGISTER_DATE DESC",
            "paging": "ok",
        }
        try:
            resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  제주교육청 p{page} 오류: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        rows = soup.select("div.board-list table.list01 tbody tr")
        if not rows:
            rows = soup.select("table.list01 tbody tr")
        if not rows:
            break

        page_count = 0
        for row in rows:
            tds = row.select("td")
            if len(tds) < 5:
                continue

            # 제목 (index 1, class="title")
            title_td = row.select_one("td.title")
            if not title_td:
                continue
            link = title_td.select_one("a")
            if not link:
                continue

            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            if not _is_teacher_post(title):
                continue
            if _is_excluded(title):
                continue

            # 상세 URL
            href = link.get("href", "")
            detail_url = f"https://www.jje.go.kr{href}" if href.startswith("/") else href

            # 학교(부서)명 (index 2)
            org_name = tds[2].get_text(strip=True) if len(tds) > 2 else "제주특별자치도교육청"

            # 작성일 (index 3)
            posted_date = tds[3].get_text(strip=True) if len(tds) > 3 else ""

            # 접수마감 (index 4) — 이미 YYYY-MM-DD 형식
            deadline = ""
            if len(tds) > 4:
                dl_text = tds[4].get_text(strip=True)
                dl_match = re.search(r"(\d{4})-(\d{2})-(\d{2})", dl_text)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2)}-{dl_match.group(3)}"

            job = JobPosting(
                title=title,
                organization=org_name or "제주특별자치도교육청",
                org_type="school" if "학교" in (org_name or "") else "government",
                org_sub_type="학교" if "학교" in (org_name or "") else "교육청",
                region="제주",
                deadline_text=deadline or posted_date,
                published_at=posted_date,
                source_url=detail_url,
                source_name="제주교육청",
                apply_url=detail_url,
            )
            results.append(job)
            page_count += 1

        print(f"  제주교육청 p{page}: {page_count}건")
        if len(rows) < 10:
            break
        time.sleep(2)

    return results


# ─────────────────────────────────────────────
# 통합 실행
# ─────────────────────────────────────────────
def crawl_all_edu_offices(pages: int = 3) -> list[JobPosting]:
    """모든 교육청 크롤링 통합"""
    all_jobs: list[JobPosting] = []

    print("  → 서울교육청...")
    all_jobs.extend(crawl_sen(pages))

    print("  → 경기교육청...")
    all_jobs.extend(crawl_goe(pages))

    print("  → 인천교육청...")
    all_jobs.extend(crawl_ice(pages))

    print("  → 부산교육청...")
    all_jobs.extend(crawl_bse(pages))

    print("  → 대구교육청...")
    all_jobs.extend(crawl_dge(pages))

    print("  → 제주교육청...")
    all_jobs.extend(crawl_jje(pages))

    return all_jobs


if __name__ == "__main__":
    print("=== 시도교육청 공지사항/채용 크롤링 ===\n")
    jobs = crawl_all_edu_offices(pages=3)

    seen = set()
    unique = []
    for j in jobs:
        key = j.source_url or j.dedupe_key
        if key not in seen:
            seen.add(key)
            unique.append(j)

    print(f"\n✅ 총 {len(unique)}건 (중복 제거)")
    for j in unique[:15]:
        print(f"  [{j.source_name}] {j.title[:55]}")
        print(f"    {j.organization} | 마감: {j.deadline_text}")
