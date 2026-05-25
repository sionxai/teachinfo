"""크롤러 실행 → JSON 파일로 내보내기"""
import sys, os, json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import JobPosting
from sources.saramin import crawl_saramin, KEYWORDS as S_KW
from sources.jobkorea import crawl_jobkorea, KEYWORDS as J_KW
from sources.public_gov import crawl_alio, crawl_kywa, crawl_seoul_job, crawl_g2b, crawl_naver_web_gov, reclassify_org_type
from sources.worknet import crawl_worknet, KEYWORDS as W_KW
from sources.gojobs import crawl_gojobs, KEYWORDS as G_KW
from sources.edu_office import crawl_all_edu_offices


def run_and_export():
    all_jobs: list[JobPosting] = []

    print("📡 사람인 크롤링...")
    for kw in S_KW:
        all_jobs.extend(crawl_saramin(kw, pages=1))

    print("📡 잡코리아 크롤링...")
    for kw in J_KW:
        all_jobs.extend(crawl_jobkorea(kw, pages=1))

    print("\n📡 워크넷 크롤링...")
    for kw in W_KW:
        all_jobs.extend(crawl_worknet(kw, pages=2))

    print("\n📡 나라일터 크롤링...")
    import time as _time
    for kw in G_KW:
        all_jobs.extend(crawl_gojobs(kw, pages=3))
        _time.sleep(0.5)

    print("\n📡 시도교육청 공지사항/채용 크롤링...")
    all_jobs.extend(crawl_all_edu_offices(pages=3))

    print("\n📡 관공서·준관공서 크롤링...")
    print("  → 잡알리오 (공공기관 채용 통합)...")
    all_jobs.extend(crawl_alio(pages=3))
    print("  → 청소년활동진흥원...")
    all_jobs.extend(crawl_kywa(pages=3))
    # 서울시 일자리포털: 404 반복 — 비활성
    # all_jobs.extend(crawl_seoul_job())
    # 나라장터: timeout 반복 — 비활성
    # all_jobs.extend(crawl_g2b())
    print("  → 네이버 웹검색 (관공서/준관공서)...")
    all_jobs.extend(crawl_naver_web_gov())

    # 기관유형 재분류 (사람인/잡코리아 결과에도 관공서/준관공서 포함될 수 있음)
    all_jobs = reclassify_org_type(all_jobs)

    # 중복 제거
    seen_urls: set[str] = set()
    seen_keys: set[str] = set()
    unique: list[JobPosting] = []
    for j in all_jobs:
        url_key = j.source_url.rstrip("/") if j.source_url else ""
        dedup = j.dedupe_key
        if (url_key and url_key in seen_urls) or (dedup and dedup in seen_keys):
            continue
        if url_key:
            seen_urls.add(url_key)
        if dedup:
            seen_keys.add(dedup)
        unique.append(j)

    # ── 품질 필터 ──
    import re as _re
    from datetime import datetime as _dt

    today_str = _dt.now().strftime("%Y-%m-%d")

    before_filter = len(unique)
    filtered: list[JobPosting] = []
    removed_old = 0
    removed_no_deadline = 0
    removed_not_teacher = 0
    removed_expired = 0

    # 제목에 이 중 하나라도 있어야 강사 관련 공고로 인정
    TEACHER_TITLE_KW = [
        "강사", "멘토", "코치", "튜터", "교관",
        "특강", "강의", "교원", "교사",
        "방과후", "늘봄", "지도사",
    ]

    for j in unique:
        # 1) 제목에 강사 관련 키워드가 하나도 없으면 제거
        #    (SNS 마케터, 경영지원 사무보조, 개발자 등 걸러냄)
        if not any(kw in j.title for kw in TEACHER_TITLE_KW):
            removed_not_teacher += 1
            continue

        # 2) 제목에 2025년 이하 연도가 있으면 제거
        old_years = _re.findall(r"20(?:1[0-9]|2[0-5])", j.title)
        if old_years:
            removed_old += 1
            continue

        # 3) 마감일 없는 공고 제거 (상시채용은 유지)
        has_deadline = bool(j.deadline_text and j.deadline_text.strip())
        if not has_deadline:
            removed_no_deadline += 1
            continue

        # 4) 마감일 지난 공고 제거
        dl = j.deadline_text.strip()[:10]
        if len(dl) == 10 and dl[4:5] == "-":
            try:
                if dl < today_str:
                    removed_expired += 1
                    continue
            except Exception:
                pass

        filtered.append(j)

    unique = filtered
    print(f"\n🗑️  필터링: {before_filter}건 → {len(unique)}건")
    print(f"    강사무관 제거: {removed_not_teacher}건")
    print(f"    옛날자료 제거: {removed_old}건")
    print(f"    마감일없음 제거: {removed_no_deadline}건")
    print(f"    마감만료 제거: {removed_expired}건")

    # 기관유형별 통계
    org_counts: dict[str, int] = {}
    for j in unique:
        label = f"{j.org_type}({j.org_sub_type})" if j.org_sub_type else j.org_type
        org_counts[label] = org_counts.get(label, 0) + 1
    print(f"\n✅ {len(unique)}건 (최종)")
    print("  기관유형별:")
    for t, c in sorted(org_counts.items(), key=lambda x: -x[1]):
        print(f"    {t}: {c}건")

    # JSON 변환
    now = datetime.now().isoformat()
    data = []
    for i, j in enumerate(unique):
        d = j.to_dict()
        d["id"] = f"job_{i+1:04d}"
        d["crawledAt"] = now
        d["createdAt"] = now
        d["updatedAt"] = now
        d["publishedAt"] = d["publishedAt"] or now
        # 지역 분리
        region_full = d.get("region", "")
        if region_full:
            for r in ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "세종", "울산", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]:
                if r in region_full:
                    d["regionDetail"] = region_full.replace(r, "").strip()
                    d["region"] = r
                    break
        data.append(d)

    # 프론트엔드에서 읽을 수 있도록 두 곳에 저장
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1) src/data/jobs.json (Next.js import용)
    src_data_path = os.path.join(project_root, "src", "data", "jobs.json")
    os.makedirs(os.path.dirname(src_data_path), exist_ok=True)
    with open(src_data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📁 저장: {src_data_path}")

    # 2) public/data/jobs.json (정적 파일)
    pub_data_path = os.path.join(project_root, "public", "data", "jobs.json")
    os.makedirs(os.path.dirname(pub_data_path), exist_ok=True)
    with open(pub_data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"📁 저장: {pub_data_path}")

    # 분야별 통계도 저장
    stats: dict[str, int] = {}
    for d in data:
        cat = d.get("category", "기타")
        stats[cat] = stats.get(cat, 0) + 1

    # 기관유형별 통계
    org_type_stats: dict[str, int] = {}
    for d in data:
        ot = d.get("orgType", "other")
        org_type_stats[ot] = org_type_stats.get(ot, 0) + 1

    # 소스 목록 자동 수집
    source_names: set[str] = set()
    for d in data:
        if d.get("sourceName"):
            source_names.add(d["sourceName"])

    stats_data = {
        "totalJobs": len(data),
        "categories": stats,
        "orgTypes": org_type_stats,
        "lastUpdated": now,
        "sources": sorted(source_names),
    }
    stats_path = os.path.join(os.path.dirname(pub_data_path), "stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats_data, f, ensure_ascii=False, indent=2)

    print(f"📁 저장: {stats_path}")


if __name__ == "__main__":
    run_and_export()
