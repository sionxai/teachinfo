"""관공서·준관공서 크롤러 — 여러 공공 채널에서 강사 구인 수집"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import time
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
# 1. 잡알리오 (공공기관 채용 포털)
# ─────────────────────────────────────────────
def crawl_alio() -> list[JobPosting]:
    """잡알리오 — 공공기관 채용정보 (강사 키워드)"""
    results = []
    url = "https://job.alio.go.kr/recruit/search.do"

    for keyword in ["강사", "교육강사"]:
        params = {
            "query": keyword,
            "tabId": "all",
            "order": "REG_DT",
            "direction": "DESC",
            "pageIndex": 1,
            "recordCountPerPage": 20,
        }
        try:
            resp = httpx.get(url, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            rows = soup.select("table tbody tr, .list_item, .recruit-list li")
            for row in rows:
                links = row.select("a")
                for link in links:
                    title = link.get_text(strip=True)
                    if not title or len(title) < 5 or not is_teacher_post(title):
                        continue
                    href = link.get("href", "")
                    full_url = f"https://job.alio.go.kr{href}" if href.startswith("/") else href

                    cells = row.select("td, span, .info")
                    org = cells[0].get_text(strip=True) if cells else ""
                    deadline = ""
                    for c in cells:
                        t = c.get_text(strip=True)
                        if re.search(r"\d{4}[.\-/]\d{1,2}[.\-/]\d{1,2}", t):
                            deadline = t
                            break

                    results.append(JobPosting(
                        title=title, organization=org,
                        org_type="government", org_sub_type="공공기관",
                        deadline_text=deadline, source_url=full_url,
                        source_name="잡알리오", apply_url=full_url,
                    ))

            print(f"  잡알리오 '{keyword}': {len(results)}건")
        except Exception as e:
            print(f"  잡알리오 '{keyword}' 오류: {e}")

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

                results.append(JobPosting(
                    title=title, organization="",
                    org_type=org_type, org_sub_type=org_sub,
                    region=region, source_url=href,
                    source_name="네이버 검색(공공)",
                ))

            print(f"  네이버웹 '{keyword}': 누적 {len(results)}건")
        except Exception as e:
            print(f"  네이버웹 '{keyword}' 오류: {e}")

        # 403 방지 딜레이
        time.sleep(2)

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
