"""나라일터(gojobs.go.kr) 크롤러 — 국가기관·지자체·교육청·공공기관 강사 공고"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

SEARCH_URL = "https://www.gojobs.go.kr/apmList.do"
DETAIL_URL = "https://www.gojobs.go.kr/apmView.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KEYWORDS = [
    "강사", "시간강사", "외부강사", "위촉강사", "특강",
    "멘토", "튜터", "교관", "코치",
    "방과후", "늘봄", "예술강사", "스포츠강사",
    "기간제교원", "계약제교원",
    "창업강사", "기업가정신", "진로",
]

# 제외 키워드
EXCLUDE_KW = [
    "합격자", "발표", "면접결과", "서류전형", "최종합격",
    "교장", "교감", "전임교원", "시설관리", "미화", "경비",
]

REGIONS = [
    "서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]


def _classify_org_type(org_name: str, title: str) -> tuple[str, str]:
    """기관명에서 orgType, orgSubType 추정"""
    combined = f"{org_name} {title}"

    # 학교 우선: "경기도교육청 안양해솔학교" 등 교육청 산하 학교는 school
    if any(kw in combined for kw in ["초등학교", "중학교", "고등학교", "학교"]):
        return "school", "학교"
    if "교육지원청" in combined:
        return "school", "교육지원청"
    # 교육청 자체는 정부기관 (CRAWLING_RULES.md 기준)
    if "교육청" in combined:
        return "government", "교육청"
    if any(kw in combined for kw in ["대학교", "대학"]):
        return "university", "대학교"
    if any(kw in combined for kw in ["시청", "구청", "군청", "도청"]):
        return "government", "관공서"
    if any(kw in combined for kw in ["센터", "재단", "진흥원", "도서관", "복지관"]):
        return "quasi_gov", "준관공서"
    if any(kw in combined for kw in ["공단", "공사", "연구원"]):
        return "public_institution", "공공기관"
    if any(kw in combined for kw in ["소년원", "법무부", "국방부", "교육부"]):
        return "government", "정부기관"

    return "government", "공공기관"


def _extract_region(org_name: str) -> str:
    for r in REGIONS:
        if r in org_name:
            return r
    return ""


def crawl_gojobs(keyword: str = "강사", pages: int = 5) -> list[JobPosting]:
    """나라일터에서 강사 관련 공고 수집"""
    results = []

    for page in range(1, pages + 1):
        params = {
            "menuNo": "401",
            "mngrMenuYn": "N",
            "searchKeyword": keyword,
            "pageIndex": str(page),
        }

        try:
            resp = httpx.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  나라일터 '{keyword}' p{page} 오류: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        trs = soup.select("table tbody tr")

        if not trs:
            break

        page_count = 0
        for tr in trs:
            tds = tr.select("td")
            if len(tds) < 6:
                continue

            title = tds[1].get_text(strip=True)
            org_name = tds[2].get_text(strip=True)
            posted_date = tds[3].get_text(strip=True)  # YYYY-MM-DD
            deadline_date = tds[4].get_text(strip=True)  # YYYY-MM-DD

            if not title or len(title) < 3:
                continue

            # 제외 키워드 체크
            if any(ex in title for ex in EXCLUDE_KW):
                continue

            # 상세 URL 추출 (javascript:fn_apmView('020', '292716'))
            link = tds[1].select_one("a")
            detail_url = ""
            if link:
                onclick = link.get("onclick", "") or link.get("href", "")
                match = re.search(r"fn_apmView\('(\d+)',\s*'(\d+)'\)", onclick)
                if match:
                    code, sn = match.groups()
                    detail_url = f"{DETAIL_URL}?apmMngrInsttCd={code}&apmSn={sn}&menuNo=401"

            # orgType 분류
            org_type, org_sub = _classify_org_type(org_name, title)

            # 지역 추출
            region = _extract_region(org_name)

            job = JobPosting(
                title=title,
                organization=org_name,
                org_type=org_type,
                org_sub_type=org_sub,
                region=region,
                deadline_text=deadline_date,
                deadline_type="fixed",
                published_at=posted_date,
                source_url=detail_url or SEARCH_URL,
                source_name="나라일터",
                apply_url=detail_url,
            )
            results.append(job)
            page_count += 1

        print(f"  나라일터 '{keyword}' p{page}: {page_count}건")

        # 다음 페이지가 없으면 중단
        if len(trs) < 10:
            break

        time.sleep(1)

    return results


if __name__ == "__main__":
    print("=== 나라일터 강사 공고 크롤링 ===\n")
    all_jobs: list[JobPosting] = []

    for kw in KEYWORDS:
        jobs = crawl_gojobs(kw, pages=5)
        all_jobs.extend(jobs)
        time.sleep(0.5)

    # 중복 제거
    seen = set()
    unique = []
    for j in all_jobs:
        key = j.source_url or j.dedupe_key
        if key not in seen:
            seen.add(key)
            unique.append(j)

    print(f"\n✅ 총 {len(unique)}건 (중복 제거)")

    # 기관유형별
    org_counts: dict[str, int] = {}
    for j in unique:
        label = f"{j.org_type}({j.org_sub_type})"
        org_counts[label] = org_counts.get(label, 0) + 1
    print("\n기관유형별:")
    for t, c in sorted(org_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}건")

    # 분야별
    cat_count: dict[str, int] = {}
    for j in unique:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1
    print("\n분야별:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}건")

    print(f"\n상위 15개:")
    for j in unique[:15]:
        print(f"  [{j.org_type}/{j.org_sub_type}] {j.title[:50]}")
        print(f"    {j.organization} | 마감: {j.deadline_text} | {j.region}")
