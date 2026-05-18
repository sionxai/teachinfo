"""네이버 블로그 검색 강사 구인 크롤러 PoC - 모바일 검색 활용"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from bs4 import BeautifulSoup
from models import JobPosting

# 네이버 모바일 검색 (블로그)
SEARCH_URL = "https://m.search.naver.com/search.naver"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

KEYWORDS = ["강사 모집 공고", "강사 구인", "교육강사 채용"]


def crawl_naver_blog(keyword: str = "강사 모집 공고", pages: int = 1) -> list[JobPosting]:
    results = []

    for page in range(1, pages + 1):
        start = (page - 1) * 10 + 1
        params = {
            "where": "m_blog",
            "query": keyword,
            "start": start,
            "sort": 1,  # 최신순
        }

        try:
            resp = httpx.get(SEARCH_URL, params=params, headers=HEADERS, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as e:
            print(f"  [오류] 네이버 검색 실패: {e}")
            continue

        soup = BeautifulSoup(resp.text, "lxml")

        # 모바일 블로그 검색 결과
        items = soup.select(".bx, .blog_item, .view_wrap")
        if not items:
            # HTML 구조 디버깅
            all_links = soup.select("a[href*='blog.naver']")
            print(f"  [디버그] blog.naver 링크 {len(all_links)}개 발견")
            for link in all_links[:15]:
                title = link.get_text(strip=True)
                href = link.get("href", "")
                if title and len(title) > 5 and any(kw in title for kw in ["강사", "모집", "채용", "구인", "위촉"]):
                    # 지역 추출
                    region = ""
                    for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                        if r in title:
                            region = r
                            break

                    org_type = "other"
                    if any(w in title for w in ["시", "구청", "도청", "교육청", "관공서"]):
                        org_type = "government"
                    elif any(w in title for w in ["센터", "복지관", "도서관", "문화", "평생교육", "청년"]):
                        org_type = "quasi_gov"

                    job = JobPosting(
                        title=title,
                        organization="",
                        org_type=org_type,
                        region=region,
                        source_url=href,
                        source_name="네이버 블로그",
                    )
                    results.append(job)

        print(f"  네이버블로그 '{keyword}' 페이지 {page}: {len(results)}개 파싱")

    return results


if __name__ == "__main__":
    print("=== 네이버 블로그 강사 구인 크롤링 PoC ===\n")
    all_jobs = []
    for kw in KEYWORDS:
        print(f"키워드: {kw}")
        jobs = crawl_naver_blog(kw, pages=1)
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
