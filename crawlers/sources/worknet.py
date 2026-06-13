"""워크넷(고용노동부) 강사 구인 크롤러 — 수정판"""
import sys, os, re, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

SEARCH_URL = "https://www.work.go.kr/empInfo/empInfoSrch/list/dtlEmpSrchList.do"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KEYWORDS = [
    "강사", "교육강사", "특강강사",
    "창업강사", "멘토", "코칭강사", "리더십강사",
    "영상강사", "미디어강사",
]

TEACHER_KW = ["강사", "교관", "교육", "멘토", "코치", "튜터", "지도사", "연수", "위촉"]

REGIONS = [
    "서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산",
    "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주",
]


def crawl_worknet(keyword: str = "강사", pages: int = 2) -> list[JobPosting]:
    """워크넷에서 강사 구인 공고 검색 (구조: table > tr > 5 td)"""
    results = []

    for page in range(1, pages + 1):
        params = {
            "srcKeyword": keyword,
            "resultCnt": 20,
            "pageIndex": page,
            "sortField": "DATE",
            "sortOrderBy": "DESC",
        }

        try:
            resp = httpx.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  워크넷 '{keyword}' p{page} 오류: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # 각 공고는 <tr> 안에 .cp-info-in 블록이 있음
        trs = soup.select("table tbody tr")
        page_count = 0

        for tr in trs:
            cp_block = tr.select_one(".cp-info-in")
            if not cp_block:
                continue

            link = cp_block.select_one("a[href*='empDetail'], a[href*='work24']")
            if not link:
                continue

            title = link.get_text(strip=True)
            if not title or len(title) < 3:
                continue

            # 강사 관련 키워드 필터
            if not any(kw in title for kw in TEACHER_KW):
                continue

            href = link.get("href", "")

            # td[1]: 회사명 (워크넷인증 텍스트 제거)
            tds = tr.select("td")
            org = ""
            if len(tds) > 1:
                org_text = tds[1].get_text(strip=True)
                # "워크넷인증" 이후 텍스트 제거
                org = re.split(r"워크넷", org_text)[0].strip()

            # td[2]: 제목 + 경력 + 학력 + 지역
            region = ""
            region_detail = ""
            if len(tds) > 2:
                loc_text = tds[2].get_text(strip=True)
                for r in REGIONS:
                    if r in loc_text:
                        region = r
                        # 상세 지역 추출
                        match = re.search(rf"{r}\S*\s+(\S+구|\S+시|\S+군)", loc_text)
                        if match:
                            region_detail = match.group(1)
                        break

            # td[3]: 급여 — HTML에 공백이 많으므로 정규식으로 정리
            pay = ""
            if len(tds) > 3:
                pay_raw = re.sub(r"\s+", "", tds[3].get_text())  # 모든 공백 제거
                pay_type = ""
                if "월급" in pay_raw:
                    pay_type = "월급"
                elif "연봉" in pay_raw:
                    pay_type = "연봉"
                elif "시급" in pay_raw:
                    pay_type = "시급"
                nums = re.findall(r"[\d,]+", pay_raw)
                if nums and pay_type:
                    pay = f"{pay_type} {nums[0]}만원"

            # td[4]: 등록일/마감일
            deadline = ""
            if len(tds) > 4:
                date_text = tds[4].get_text(strip=True)
                deadline_match = re.search(r"(\d{2}/\d{2}/\d{2})\s*마감", date_text)
                if deadline_match:
                    deadline = deadline_match.group(1) + " 마감"
                elif "채용시" in date_text or "상시" in date_text:
                    deadline = "상시채용"

            job = JobPosting(
                title=title,
                organization=org,
                org_type="corporate",  # reclassify에서 재분류됨
                region=region,
                region_detail=region_detail,
                pay=pay,
                deadline_text=deadline,
                source_url=href,
                source_name="워크넷",
                apply_url=href,
            )
            results.append(job)
            page_count += 1

        print(f"  워크넷 '{keyword}' p{page}: {page_count}건")

        if page < pages:
            time.sleep(1)

    return results


if __name__ == "__main__":
    print("=== 워크넷 강사 구인 크롤링 ===\n")
    all_jobs: list[JobPosting] = []
    for kw in KEYWORDS:
        jobs = crawl_worknet(kw, pages=2)
        all_jobs.extend(jobs)
        time.sleep(0.5)

    seen = set()
    unique = [j for j in all_jobs if j.source_url not in seen and not seen.add(j.source_url)]  # type: ignore

    print(f"\n✅ 총 {len(unique)}건 (중복 제거)")

    cat_count: dict[str, int] = {}
    for j in unique:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1
    print("\n분야별:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}건")

    print(f"\n상세 (상위 10개):")
    for j in unique[:10]:
        print(f"  {j.summary()}")
        print(f"    기관: {j.organization} | 급여: {j.pay} | 마감: {j.deadline_text}")
