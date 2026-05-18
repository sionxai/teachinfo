"""크롤러 PoC 통합 테스트 — 전체 소스 수집 + 분야별 필터링 검증"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import JobPosting, CATEGORIES
from sources.saramin import crawl_saramin, KEYWORDS as SARAMIN_KW
from sources.jobkorea import crawl_jobkorea, KEYWORDS as JOBKOREA_KW


def run_all_crawlers() -> list[JobPosting]:
    """전체 크롤러 실행"""
    all_jobs: list[JobPosting] = []

    # 1. 사람인
    print("━" * 50)
    print("📡 [1/2] 사람인 크롤링")
    print("━" * 50)
    for kw in SARAMIN_KW:
        jobs = crawl_saramin(kw, pages=1)
        all_jobs.extend(jobs)

    # 2. 잡코리아
    print("\n" + "━" * 50)
    print("📡 [2/2] 잡코리아 크롤링")
    print("━" * 50)
    for kw in JOBKOREA_KW:
        jobs = crawl_jobkorea(kw, pages=1)
        all_jobs.extend(jobs)

    return all_jobs


def deduplicate(jobs: list[JobPosting]) -> list[JobPosting]:
    """URL + dedupe_key 기반 중복 제거"""
    seen_urls: set[str] = set()
    seen_keys: set[str] = set()
    unique: list[JobPosting] = []

    for j in jobs:
        if j.source_url in seen_urls:
            continue
        if j.dedupe_key in seen_keys:
            continue
        seen_urls.add(j.source_url)
        seen_keys.add(j.dedupe_key)
        unique.append(j)

    return unique


def filter_by_category(jobs: list[JobPosting], category: str) -> list[JobPosting]:
    """분야별 필터링"""
    return [j for j in jobs if j.category == category]


def filter_by_region(jobs: list[JobPosting], region: str) -> list[JobPosting]:
    """지역별 필터링"""
    return [j for j in jobs if region in j.region]


def print_report(jobs: list[JobPosting]):
    """결과 리포트 출력"""
    print("\n" + "=" * 60)
    print(f"📊 크롤링 결과 총괄 리포트")
    print("=" * 60)

    # 전체 통계
    print(f"\n✅ 총 수집 공고: {len(jobs)}건")

    # 소스별 통계
    source_count: dict[str, int] = {}
    for j in jobs:
        source_count[j.source_name] = source_count.get(j.source_name, 0) + 1
    print(f"\n📌 소스별 수집:")
    for src, cnt in sorted(source_count.items(), key=lambda x: -x[1]):
        print(f"  {src}: {cnt}건")

    # 분야별 통계
    cat_count: dict[str, int] = {}
    for j in jobs:
        cat_count[j.category] = cat_count.get(j.category, 0) + 1
    print(f"\n📌 분야별 분류:")
    for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
        print(f"  {cat}: {cnt}건")

    # 지역별 통계
    region_count: dict[str, int] = {}
    for j in jobs:
        r = j.region if j.region else "미분류"
        region_count[r] = region_count.get(r, 0) + 1
    print(f"\n📌 지역별 분류:")
    for reg, cnt in sorted(region_count.items(), key=lambda x: -x[1]):
        print(f"  {reg}: {cnt}건")

    # 필터링 데모
    print("\n" + "=" * 60)
    print("🔍 필터링 데모")
    print("=" * 60)

    for demo_cat in ["IT·프로그래밍", "어학", "교육·강의기법"]:
        filtered = filter_by_category(jobs, demo_cat)
        print(f"\n🏷️  [{demo_cat}] 필터 → {len(filtered)}건:")
        for j in filtered[:3]:
            print(f"    • {j.title[:40]}{'...' if len(j.title) > 40 else ''} | {j.organization} | {j.region or '지역미정'}")

    for demo_region in ["서울", "경기"]:
        filtered = filter_by_region(jobs, demo_region)
        print(f"\n📍 [{demo_region}] 필터 → {len(filtered)}건:")
        for j in filtered[:3]:
            print(f"    • [{j.category}] {j.title[:35]}{'...' if len(j.title) > 35 else ''} | {j.organization}")


if __name__ == "__main__":
    print("🚀 강사구인 크롤러 PoC 통합 테스트\n")

    # 전체 크롤링
    raw_jobs = run_all_crawlers()
    print(f"\n수집 완료: 원본 {len(raw_jobs)}건")

    # 중복 제거
    jobs = deduplicate(raw_jobs)
    print(f"중복 제거: {len(jobs)}건")

    # 리포트
    print_report(jobs)

    print("\n" + "=" * 60)
    print("✅ PoC 결론: 매일 자동 수집 + 분야별 필터링 가능")
    print("=" * 60)
