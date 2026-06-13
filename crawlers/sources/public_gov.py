"""관공서·준관공서 크롤러 — 여러 공공 채널에서 강사 구인 수집"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import time
import concurrent.futures
import httpx
from bs4 import BeautifulSoup
from models import JobPosting

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

TEACHER_KW = ["강사", "교육", "특강", "위촉", "교관", "멘토", "코치", "튜터", "지도사", "연수"]


def is_teacher_post(title: str) -> bool:
    return any(kw in title for kw in TEACHER_KW)


# ─────────────────────────────────────────────
# 1. 잡알리오 (공공기관 채용정보 통합 포털)
#    복지관, 청소년센터, 문화재단, 평생교육원 등 전 분야 공공기관 채용 집약
# ─────────────────────────────────────────────
ALIO_KEYWORDS = ["강사", "멘토", "코치", "튜터", "교관", "특강", "영상", "미디어"]

QUASI_GOV_ORG_KW = [
    "센터", "재단", "진흥원", "진흥", "도서관", "복지관", "문화원",
    "평생교육", "평생학습", "청소년", "수련", "여성", "청년",
    "협회", "연구원", "공사", "공단",
]

def _classify_alio_org(org_name: str) -> tuple[str, str]:
    """잡알리오 기관명에서 orgType/orgSubType 분류"""
    if any(kw in org_name for kw in ["대학교", "대학"]):
        return "university", "대학교"
    if any(kw in org_name for kw in ["교육청", "시청", "구청", "군청", "도청", "국립"]):
        return "government", "관공서"
    if any(kw in org_name for kw in QUASI_GOV_ORG_KW):
        for kw in QUASI_GOV_ORG_KW:
            if kw in org_name:
                return "quasi_gov", kw
    return "public_institution", "공공기관"


def crawl_alio(pages: int = 3) -> list[JobPosting]:
    """잡알리오 — 공공기관 채용정보 (강사/교육/멘토 키워드)
    table.tbl.type_03: 번호, 채용제목, 기관명, 근무지, 고용형태, 등록일, 마감일, 상태"""
    results = []
    url = "https://job.alio.go.kr/recruit.do"

    for keyword in ALIO_KEYWORDS:
        for page in range(1, pages + 1):
            params = {"keyword": keyword, "search_type": "title", "pageNo": str(page)}
            try:
                resp = httpx.get(url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
                resp.raise_for_status()
            except Exception as e:
                print(f"  잡알리오 '{keyword}' p{page} 오류: {e}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            rows = soup.select("table.type_03 tbody tr")
            if not rows:
                break

            page_count = 0
            for row in rows:
                tds = row.select("td")
                if len(tds) < 8:
                    continue

                # td[2]: 채용제목 + link
                link = tds[2].select_one("a")
                if not link:
                    continue
                title = link.get_text(strip=True)
                if not title or len(title) < 5:
                    continue
                # 키워드 검색이 이미 제목 필터 역할 → is_teacher_post 중복 체크 불필요

                href = link.get("href", "")
                detail_url = f"https://job.alio.go.kr{href}" if href.startswith("/") else href

                # td[3]: 기관명
                org_name = tds[3].get_text(strip=True)
                # td[4]: 근무지
                region_text = tds[4].get_text(strip=True)
                region = ""
                for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종",
                           "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                    if r in region_text:
                        region = r
                        break

                # td[6]: 등록일 (2026.05.22)
                posted_date = tds[6].get_text(strip=True).strip()
                # td[7]: 마감일 (26.06.08D-13)
                deadline_raw = tds[7].get_text(strip=True).strip()
                # "26.06.08D-13" → "2026-06-08"
                deadline = ""
                dl_match = re.search(r"(\d{2,4})[.](\d{2})[.](\d{2})", deadline_raw)
                if dl_match:
                    y, m, d = dl_match.groups()
                    if len(y) == 2:
                        y = f"20{y}"
                    deadline = f"{y}-{m}-{d}"

                org_type, org_sub = _classify_alio_org(org_name)

                results.append(JobPosting(
                    title=title, organization=org_name,
                    org_type=org_type, org_sub_type=org_sub,
                    region=region,
                    deadline_text=deadline or deadline_raw,
                    published_at=posted_date,
                    source_url=detail_url,
                    source_name="잡알리오",
                    apply_url=detail_url,
                ))
                page_count += 1

            print(f"  잡알리오 '{keyword}' p{page}: {page_count}건")
            if len(rows) < 10:
                break
            time.sleep(1)

    return results


# ─────────────────────────────────────────────
# 1-2. 한국청소년활동진흥원 (kywa.or.kr) — 청소년센터/수련관 채용
# ─────────────────────────────────────────────
def crawl_kywa(pages: int = 3) -> list[JobPosting]:
    """한국청소년활동진흥원 채용공고 — 청소년수련관/센터 강사·교관 채용 집약
    table.t-type02: 번호, 제목, 작성자, 작성일, 조회수"""
    results = []
    base_url = "https://kywa.or.kr/about/about05_5.jsp"

    for page in range(1, pages + 1):
        params = {
            "bgubun": "",
            "cate": "C3A4BFEB",
            "currPage": str(page),
            "searchText": "",
            "searchColumn": "",
        }
        try:
            resp = httpx.get(base_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            # EUC-KR 인코딩 처리
            try:
                text = resp.content.decode("euc-kr")
            except UnicodeDecodeError:
                text = resp.text
        except Exception as e:
            print(f"  청소년활동진흥원 p{page} 오류: {e}")
            break

        soup = BeautifulSoup(text, "lxml")
        rows = soup.select("table.t-type02 tbody tr, table.t-type02 tr")
        # 첫 행이 헤더면 건너뛰기
        if rows and rows[0].select("th"):
            rows = rows[1:]
        if not rows:
            break

        page_count = 0
        for row in rows:
            tds = row.select("td")
            if len(tds) < 4:
                continue

            # td[1]: 제목 + link
            link = tds[1].select_one("a") if len(tds) > 1 else None
            if not link:
                continue
            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                continue
            # 청소년활동진흥원 채용 게시판은 산하기관 전체 채용 → 넓게 수집
            # (export_json.py의 TEACHER_TITLE_KW 필터가 최종 걸러냄)

            href = link.get("href", "")
            if href and not href.startswith("http"):
                detail_url = f"https://kywa.or.kr/about/{href}"
            else:
                detail_url = href

            # td[2]: 작성자, td[3]: 작성일
            writer = tds[2].get_text(strip=True) if len(tds) > 2 else ""
            posted_date = tds[3].get_text(strip=True) if len(tds) > 3 else ""

            # 마감일은 제목에서 추출 시도
            deadline = ""
            dl_match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", title)
            if dl_match:
                deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

            results.append(JobPosting(
                title=title,
                organization=writer or "한국청소년활동진흥원",
                org_type="quasi_gov",
                org_sub_type="청소년센터",
                deadline_text=deadline or posted_date,
                published_at=posted_date,
                source_url=detail_url,
                source_name="청소년활동진흥원",
                apply_url=detail_url,
            ))
            page_count += 1

        print(f"  청소년활동진흥원 p{page}: {page_count}건")
        if len(rows) < 10:
            break
        time.sleep(1)

    return results


# ─────────────────────────────────────────────
# 2. 서울시 일자리포털 (서울시 산하기관 채용)
# ─────────────────────────────────────────────
def crawl_seoul_job() -> list[JobPosting]:
    """서울시 일자리포털 — 강사 관련 공고"""
    results = []
    url = "https://job.seoul.go.kr/www/openApiList.do"

    # 서울시 공공일자리 검색
    search_url = "https://job.seoul.go.kr/www/job_offer/list.do"
    for keyword in ["강사", "교육"]:
        params = {"sSearchText": keyword, "pageIndex": 1, "pageUnit": 20}
        try:
            resp = httpx.get(search_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            rows = soup.select("table tbody tr, .board-list li, .list-group-item")
            for row in rows:
                link = row.select_one("a")
                if not link:
                    continue
                title = link.get_text(strip=True)
                if not title or len(title) < 5 or not is_teacher_post(title):
                    continue
                href = link.get("href", "")
                full_url = f"https://job.seoul.go.kr{href}" if href.startswith("/") else href

                cells = row.select("td, span")
                org = ""
                deadline = ""
                for c in cells:
                    t = c.get_text(strip=True)
                    if any(w in t for w in ["센터", "재단", "관", "원", "시"]) and not org:
                        org = t
                    if re.search(r"\d{2,4}[.\-/]\d{1,2}[.\-/]\d{1,2}", t):
                        deadline = t

                results.append(JobPosting(
                    title=title, organization=org or "서울시 산하기관",
                    org_type="quasi_gov", org_sub_type="서울시",
                    region="서울", deadline_text=deadline,
                    source_url=full_url, source_name="서울시 일자리포털",
                    apply_url=full_url,
                ))

            print(f"  서울시 일자리 '{keyword}': {len(results)}건")
        except Exception as e:
            print(f"  서울시 일자리 '{keyword}' 오류: {e}")

    return results


# ─────────────────────────────────────────────
# 3. 나라장터 (조달청 입찰 — 교육용역)
# ─────────────────────────────────────────────
def crawl_g2b() -> list[JobPosting]:
    """나라장터 — 교육/강사 관련 용역 입찰"""
    results = []
    url = "https://www.g2b.go.kr:8101/ep/tbid/tbidList.do"

    params = {
        "taskClCds": "5",  # 용역
        "bidNm": "강사",
        "fromBidDt": "",
        "toBidDt": "",
        "radOrgan": "1",
        "instNm": "",
        "area": "",
        "regYn": "Y",
        "recordCountPerPage": 20,
        "currentPageNo": 1,
    }
    try:
        resp = httpx.get(url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        rows = soup.select("table tbody tr, .results_list tr")
        for row in rows:
            cells = row.select("td")
            if len(cells) < 3:
                continue
            link = row.select_one("a")
            if not link:
                continue
            title = link.get_text(strip=True)
            if not title or len(title) < 5:
                continue

            href = link.get("href", "")
            full_url = f"https://www.g2b.go.kr:8101{href}" if href.startswith("/") else href
            org = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            deadline = cells[-1].get_text(strip=True) if cells else ""

            results.append(JobPosting(
                title=title, organization=org,
                org_type="government", org_sub_type="조달청 입찰",
                deadline_text=deadline, source_url=full_url,
                source_name="나라장터", apply_url=full_url,
            ))

        print(f"  나라장터: {len(results)}건")
    except Exception as e:
        print(f"  나라장터 오류: {e}")

    return results


# ─────────────────────────────────────────────
# 4. 사람인에서 관공서/준관공서 필터 (orgType 재분류)
# ─────────────────────────────────────────────
def reclassify_org_type(jobs: list[JobPosting]) -> list[JobPosting]:
    """기관명(organization)에서 관공서/준관공서 재분류.
    title만으로 판단하면 '행정직원' 같은 단어에 오분류됨 → 기관명 우선."""
    gov_keywords = ["시청", "구청", "군청", "도청", "교육청", "교육부", "지방자치", "공단"]
    quasi_keywords = [
        "청년센터", "창업지원센터", "창업진흥", "평생교육", "평생학습",
        "문화재단", "문화센터", "복지관", "도서관", "여성새로일하기",
        "고용센터", "직업훈련", "인력개발", "사회적경제",
        "주민센터", "건강가정", "다문화", "자원봉사", "체육회",
        "재단", "진흥원", "연구원", "협회", "공사",
        "센터",  # 가장 넓은 매칭은 마지막에
    ]
    uni_keywords = ["대학교", "대학"]

    for j in jobs:
        # 이미 public_gov 크롤러에서 분류한 것은 건드리지 않음
        if j.source_name in ("잡알리오", "서울시 일자리포털", "나라장터", "네이버 검색(공공)", "나라일터"):
            continue

        org = j.organization
        if not org:
            continue

        # 기관명 기반 분류 (title은 보조)
        if any(kw in org for kw in gov_keywords):
            j.org_type = "government"
            j.org_sub_type = "관공서"
        elif any(kw in org for kw in quasi_keywords):
            j.org_type = "quasi_gov"
            for kw in quasi_keywords:
                if kw in org:
                    j.org_sub_type = kw
                    break
        elif any(kw in org for kw in uni_keywords):
            j.org_type = "university"
            j.org_sub_type = "대학교"
    return jobs


# ─────────────────────────────────────────────
# 5. 네이버 검색 — 관공서/준관공서 강사 공고 (웹 검색)
# ─────────────────────────────────────────────

# 본문 날짜 패턴: 2026.4.24 / 2026-04-24 / 2026년 4월 24일 / 2026. 4. 24.
_DATE_PAT = re.compile(r"(20\d{2})\s*[.\-/년]\s*(\d{1,2})\s*[.\-/월]\s*(\d{1,2})")


def _extract_deadline_from_page(url: str) -> str:
    """상세 페이지 본문에서 접수 마감일(ISO yyyy-mm-dd)을 추출한다.

    '까지/~/마감/접수/종료' 같은 마감 신호가 붙은 날짜만 채택한다.
    명확한 신호가 없으면 빈 문자열을 반환해 호출부가 '채용시까지'를 유지하게 한다.
    이렇게 해야 뉴스 본문의 무관한 날짜(게재일 등)를 마감일로 오인하지 않는다.
    """
    if not url or not url.startswith("http"):
        return ""
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=6, follow_redirects=True)
    except Exception:
        return ""
    if resp.status_code != 200 or "html" not in resp.headers.get("content-type", ""):
        return ""

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text(" ", strip=True)
    except Exception:
        return ""

    candidates: list[tuple[int, str]] = []
    for m in _DATE_PAT.finditer(text):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (2024 <= y <= 2027 and 1 <= mo <= 12 and 1 <= d <= 31):
            continue
        iso = f"{y:04d}-{mo:02d}-{d:02d}"
        before = text[max(0, m.start() - 30):m.start()]
        after = text[m.end():m.end() + 10]
        near = "~" in before[-8:] or "∼" in before[-8:]  # 날짜 직전 범위기호 = 종료일
        # 마감 신호 강도로 점수화 — '접수/모집기간' 레이블이 가장 확실
        if any(k in before for k in ["접수", "모집기간", "신청기간", "지원기간", "접수기간"]):
            score = 5 if near else 4  # 종료일(~ 뒤)이면 가점
        elif "까지" in after:
            score = 3
        elif near:
            score = 2
        elif any(k in (before + after) for k in ["마감", "종료"]):
            score = 1
        else:
            score = 0  # 무관한 날짜 — 채택하지 않음
        if score > 0:
            candidates.append((score, iso))

    if not candidates:
        return ""
    # 점수 높은 것 우선, 동점이면 가장 늦은 날짜(=접수 종료일)
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return candidates[0][1]


def _enrich_naver_deadlines(results: list[JobPosting]) -> None:
    """마감일을 못 잡은 네이버 결과의 원문을 병렬 방문해 마감일을 보강한다.

    추출된 날짜가 과거면 export_json.py의 마감만료 필터가 자동 제거한다.
    중복 URL은 한 번만 요청한다.
    """
    need: dict[str, str] = {}
    for j in results:
        if j.deadline_type == "until_filled" and j.source_url.startswith("http"):
            need.setdefault(j.source_url, "")
    if not need:
        return

    print(f"  네이버웹: 상세 마감일 추출 {len(need)}건...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futs = {ex.submit(_extract_deadline_from_page, u): u for u in need}
        for fut in concurrent.futures.as_completed(futs):
            u = futs[fut]
            try:
                need[u] = fut.result()
            except Exception:
                need[u] = ""

    applied = 0
    for j in results:
        dl = need.get(j.source_url)
        if dl:
            j.deadline_text = dl
            j.deadline_type = "fixed"
            applied += 1
    print(f"  네이버웹: 마감일 추출 성공 {applied}건 (나머지는 '채용시까지' 유지)")


def crawl_naver_web_gov() -> list[JobPosting]:
    """네이버 웹 검색으로 관공서/준관공서 강사 공고 수집"""
    results = []
    search_url = "https://search.naver.com/search.naver"

    keywords = [
        # 준관공서
        "청년센터 강사 모집",
        "평생교육원 강사 모집",
        "창업지원센터 강사 채용",
        "문화센터 강사 모집 공고",
        "복지관 강사 구인",
        "도서관 강사 모집",
        "고용센터 교육 강사",
        "여성새로일하기센터 강사",
        # 관공서
        "교육청 강사 채용",
        "시청 강사 모집",
        "구청 강사 채용",
        "공공기관 강사 모집 공고",
        # 분야별 (멘탈·창업·기업가정신)
        "기업가정신 강사 모집",
        "창업 멘토 모집 공고",
        "동기부여 강사 채용",
        "멘탈코칭 강사 모집",
        "리더십 강사 모집 공고",
        # 영상/미디어
        "시청자미디어센터 강사 모집",
        "미디어교육 강사 모집",
        "영상제작 강사 채용",
        "유튜브 강사 모집 공고",
        # AI/디지털
        "AI 강사 모집",
        "인공지능 교육 강사 채용",
        "디지털 강사 모집 공고",
        "코딩 강사 모집",
        "소프트웨어 교육 강사 채용",
        "제주 AI 디지털 강사 모집",
    ]

    for keyword in keywords:
        params = {"where": "web", "query": keyword, "sort": 1}  # 최신순
        try:
            resp = httpx.get(search_url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # 웹 검색 결과
            items = soup.select(".total_wrap, .api_txt_lines, .total_tit a, .link_tit")
            if not items:
                items = soup.select("a[href]")

            for item in items:
                if item.name == "a":
                    link = item
                else:
                    link = item.select_one("a")
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get("href", "")

                if not title or len(title) < 8:
                    continue
                if not is_teacher_post(title):
                    continue
                # 광고/쇼핑 제외
                if any(x in href for x in ["ad.search", "shopping", "smartstore", "blog.me"]):
                    continue

                # 기관유형 추정
                org_type = "quasi_gov"
                org_sub = ""
                # 관공서 키워드 먼저 체크
                for gk in ["교육청", "시청", "구청", "공공기관"]:
                    if gk in title or gk in keyword:
                        org_type = "government"
                        org_sub = "관공서"
                        break
                if org_type != "government":
                    for qt in ["청년센터", "평생교육", "창업지원", "문화센터", "복지관", "도서관", "고용센터", "새로일하기", "여성"]:
                        if qt in title or qt in keyword:
                            org_sub = qt
                            break

                # 지역 추출
                region = ""
                for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                    if r in title:
                        region = r
                        break

                # 제목에서 마감일 추출 시도
                deadline = ""
                dl_match = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", title)
                if dl_match:
                    deadline = f"{dl_match.group(1)}-{dl_match.group(2).zfill(2)}-{dl_match.group(3).zfill(2)}"

                results.append(JobPosting(
                    title=title, organization="",
                    org_type=org_type, org_sub_type=org_sub,
                    region=region, source_url=href,
                    source_name="네이버 검색(공공)",
                    deadline_text=deadline or "채용시까지",
                    deadline_type="until_filled" if not deadline else "fixed",
                ))

            print(f"  네이버웹 '{keyword}': 누적 {len(results)}건")
        except Exception as e:
            print(f"  네이버웹 '{keyword}' 오류: {e}")

        # 403 방지 딜레이
        time.sleep(2)

    # 마감일 못 잡은 결과는 원문 방문해 접수 마감일 보강 (지난 건 후속 필터가 제거)
    _enrich_naver_deadlines(results)

    return results


# ─────────────────────────────────────────────
# 통합 실행
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=== 관공서·준관공서 강사 구인 크롤링 ===\n")

    all_jobs: list[JobPosting] = []

    print("📡 1) 잡알리오 (공공기관 채용)")
    all_jobs.extend(crawl_alio())

    print("\n📡 2) 서울시 일자리포털")
    all_jobs.extend(crawl_seoul_job())

    print("\n📡 3) 나라장터 (교육용역)")
    all_jobs.extend(crawl_g2b())

    print("\n📡 4) 네이버 웹검색 (관공서/준관공서)")
    all_jobs.extend(crawl_naver_web_gov())

    # 중복 제거
    seen = set()
    unique = []
    for j in all_jobs:
        key = j.source_url or j.dedupe_key
        if key not in seen:
            seen.add(key)
            unique.append(j)

    print(f"\n{'='*50}")
    print(f"✅ 관공서·준관공서 수집: {len(unique)}건")
    print(f"{'='*50}")

    # 기관유형별
    type_count: dict[str, int] = {}
    for j in unique:
        label = f"{j.org_type}({j.org_sub_type})" if j.org_sub_type else j.org_type
        type_count[label] = type_count.get(label, 0) + 1
    print("\n📌 기관유형별:")
    for t, c in sorted(type_count.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}건")

    # 분야별
    cat_count: dict[str, int] = {}
    for j in unique:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1
    print("\n📌 분야별:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}건")

    print("\n📋 상세 목록 (상위 15개):")
    for j in unique[:15]:
        print(f"  [{j.org_type}/{j.org_sub_type}] {j.summary()}")
