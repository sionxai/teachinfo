"""사람인 강사 구인 크롤러 PoC"""
import httpx
from bs4 import BeautifulSoup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import JobPosting

SEARCH_URL = "https://www.saramin.co.kr/zf_user/search/recruit"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KEYWORDS = [
    "강사 모집", "강사 채용", "교육 강사", "특강 강사",
    "창업 강사", "기업가정신 강사", "멘탈 강사", "동기부여 강사",
    "코칭 강사", "리더십 강사", "스타트업 멘토",
]


def crawl_saramin(keyword: str = "강사 모집", pages: int = 1) -> list[JobPosting]:
    """사람인에서 강사 구인 공고 검색"""
    results = []

    for page in range(1, pages + 1):
        params = {
            "searchType": "search",
            "searchword": keyword,
            "recruitPage": page,
            "recruitSort": "relation",
            "recruitPageCount": 20,
        }

        try:
            resp = httpx.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [오류] 사람인 요청 실패: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")
        items = soup.select(".item_recruit")

        if not items:
            print(f"  [참고] '{keyword}' 페이지 {page}: 결과 없음 (선택자 확인 필요)")
            # 대체 선택자 시도
            items = soup.select("[class*='recruit']")
            if items:
                print(f"  [참고] 대체 선택자로 {len(items)}개 요소 발견")

        for item in items:
            try:
                # 제목
                title_el = item.select_one(".job_tit a, .recruit_title a, h2 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)

                # 회사명
                corp_el = item.select_one(".corp_name a, .company_name a")
                org = corp_el.get_text(strip=True) if corp_el else ""

                # 링크
                href = title_el.get("href", "")
                url = f"https://www.saramin.co.kr{href}" if href.startswith("/") else href

                # 조건 (지역, 경력 등)
                conditions = item.select(".job_condition span, .recruit_condition span")
                region = ""
                for cond in conditions:
                    text = cond.get_text(strip=True)
                    if any(r in text for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]):
                        region = text.split()[0] if text else ""
                        break

                # 마감
                deadline_el = item.select_one(".job_date .date, .recruit_date")
                deadline = deadline_el.get_text(strip=True) if deadline_el else ""

                job = JobPosting(
                    title=title,
                    organization=org,
                    org_type="corporate",
                    region=region,
                    deadline_text=deadline,
                    source_url=url,
                    source_name="사람인",
                    apply_url=url,
                )
                results.append(job)
            except Exception as e:
                print(f"  [오류] 항목 파싱 실패: {e}")
                continue

        print(f"  사람인 '{keyword}' 페이지 {page}: {len(items)}개 항목 → {len(results)}개 파싱 완료")

    return results


if __name__ == "__main__":
    print("=== 사람인 강사 구인 크롤링 PoC ===\n")
    all_jobs = []
    for kw in KEYWORDS:
        print(f"\n키워드: {kw}")
        jobs = crawl_saramin(kw, pages=1)
        all_jobs.extend(jobs)

    # 중복 제거 (URL 기준)
    seen = set()
    unique = []
    for j in all_jobs:
        if j.source_url not in seen:
            seen.add(j.source_url)
            unique.append(j)

    print(f"\n=== 결과: 총 {len(unique)}개 공고 (중복 제거 후) ===\n")

    # 분야별 통계
    cat_count: dict[str, int] = {}
    for j in unique:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1

    print("📊 분야별 분류:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}건")

    print(f"\n📋 상세 목록 (상위 10개):")
    for j in unique[:10]:
        print(f"  {j.summary()}")
