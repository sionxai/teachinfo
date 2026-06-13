"""잡코리아 강사 구인 크롤러 PoC"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

SEARCH_URL = "https://www.jobkorea.co.kr/Search/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KEYWORDS = [
    "강사 모집", "교육 강사", "강사 채용",
    "창업 강사", "기업가정신 강사", "멘탈 강사", "동기부여 강사",
    "코칭 강사", "리더십 강사", "스타트업 멘토",
    # 영상/미디어
    "영상 강사", "미디어 강사", "콘텐츠 강사", "유튜브 강사", "크리에이터 강사",
]


def crawl_jobkorea(keyword: str = "강사 모집", pages: int = 1) -> list[JobPosting]:
    results = []

    for page in range(1, pages + 1):
        params = {
            "stext": keyword,
            "tabType": "recruit",
            "Page_No": page,
        }

        try:
            resp = httpx.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [오류] 잡코리아 요청 실패: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # 채용 목록
        items = soup.select(".list-default .list-post, .recruit-info, .post-list-info")
        if not items:
            items = soup.select("table.list tbody tr, .tplList .list-post")

        if not items:
            # 대체: 모든 채용공고 링크
            links = soup.select("a[href*='/Recruit/']")
            print(f"  [디버그] 채용 링크 {len(links)}개 발견")

            for link in links:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if not title or len(title) < 5:
                    continue

                url = f"https://www.jobkorea.co.kr{href}" if href.startswith("/") else href

                # 부모에서 회사명, 마감일, 지역 추출
                parent = link.find_parent("tr") or link.find_parent("li") or link.find_parent("div")
                org = ""
                deadline = ""
                region = ""
                if parent:
                    corp_el = parent.select_one(".name, .corp-name a, [class*='company']")
                    if corp_el:
                        org = corp_el.get_text(strip=True)

                    # 마감일: ~MM/DD, D-숫자, 오늘마감 등
                    parent_text = parent.get_text(" ", strip=True)
                    import re
                    dl_match = re.search(r"~\s*(\d{1,2}/\d{1,2})", parent_text)
                    if dl_match:
                        deadline = f"~ {dl_match.group(1)}"
                    elif "오늘마감" in parent_text or "오늘 마감" in parent_text:
                        deadline = "오늘마감"
                    elif "상시" in parent_text:
                        deadline = "상시채용"
                    else:
                        d_match = re.search(r"D-(\d+)", parent_text)
                        if d_match:
                            deadline = f"D-{d_match.group(1)}"

                    # 지역
                    for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                        if r in parent_text:
                            region = r
                            break

                job = JobPosting(
                    title=title,
                    organization=org,
                    org_type="corporate",
                    region=region,
                    deadline_text=deadline,
                    source_url=url,
                    source_name="잡코리아",
                    apply_url=url,
                )
                results.append(job)
        else:
            for item in items:
                try:
                    title_el = item.select_one(".title, .tit a, a")
                    if not title_el:
                        continue
                    title = title_el.get_text(strip=True)
                    href = title_el.get("href", "")
                    url = f"https://www.jobkorea.co.kr{href}" if href.startswith("/") else href

                    corp_el = item.select_one(".name, .corp-name a")
                    org = corp_el.get_text(strip=True) if corp_el else ""

                    # 지역
                    region = ""
                    opt_els = item.select(".opt, .option span, .etc span")
                    for el in opt_els:
                        text = el.get_text(strip=True)
                        for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                            if r in text:
                                region = r
                                break

                    job = JobPosting(
                        title=title,
                        organization=org,
                        org_type="corporate",
                        region=region,
                        source_url=url,
                        source_name="잡코리아",
                        apply_url=url,
                    )
                    results.append(job)
                except Exception:
                    continue

        print(f"  잡코리아 '{keyword}' 페이지 {page}: {len(results)}개 파싱")

    return results


if __name__ == "__main__":
    print("=== 잡코리아 강사 구인 크롤링 PoC ===\n")
    all_jobs = []
    for kw in KEYWORDS:
        print(f"키워드: {kw}")
        jobs = crawl_jobkorea(kw, pages=1)
        all_jobs.extend(jobs)

    seen = set()
    unique = [j for j in all_jobs if j.source_url not in seen and not seen.add(j.source_url)]

    print(f"\n=== 결과: 총 {len(unique)}개 공고 ===\n")

    cat_count: dict[str, int] = {}
    for j in unique:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1

    if cat_count:
        print("📊 분야별 분류:")
        for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {cnt}건")

    print(f"\n📋 상세 목록:")
    for j in unique[:10]:
        print(f"  {j.summary()}")
