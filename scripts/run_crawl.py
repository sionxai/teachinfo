#!/usr/bin/env python3
"""
강사구인 크롤링 통합 러너

백업 → 크롤링 → 검증 → 비교 → 리포트를 한 번에 처리한다.
스킬 문서(SKILL.md)는 이 스크립트만 실행하면 된다.

Usage:
    python3 scripts/run_crawl.py          # 일반 실행
    python3 scripts/run_crawl.py --dry    # 크롤링 없이 검증만 (이전 데이터 기준)
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 경로 설정 ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CRAWLERS_DIR = PROJECT_ROOT / "crawlers"
SRC_JOBS = PROJECT_ROOT / "src" / "data" / "jobs.json"
PUB_JOBS = PROJECT_ROOT / "public" / "data" / "jobs.json"
PUB_STATS = PROJECT_ROOT / "public" / "data" / "stats.json"
BACKUP_BASE = PROJECT_ROOT / "backups" / "crawls"
LOG_DIR = PROJECT_ROOT / "logs" / "crawls"

TIMEOUT_SEC = 360
# 이전 대비 이 비율 이하로 떨어지면 경고 (50%)
DROP_THRESHOLD = 0.5
# 소스별 이전 건수 대비 이 이하면 경고 (0건)
SOURCE_ZERO_WARN = True

# 필수 필드 (jobs.json 각 항목에 존재해야 함)
REQUIRED_FIELDS = ["title", "organization", "sourceUrl", "sourceName", "deadlineText"]


def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_json(path: Path) -> dict | list | None:
    """JSON 파일을 안전하게 로드. 실패 시 None 반환."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  [WARN] JSON 로드 실패: {path} — {e}")
        return None


def _source_counts(jobs: list[dict]) -> dict[str, int]:
    """소스별 건수 집계."""
    counts: dict[str, int] = {}
    for j in jobs:
        src = j.get("sourceName", "unknown")
        counts[src] = counts.get(src, 0) + 1
    return counts


# ────────────────────────────────────────────────
# 1. Preflight
# ────────────────────────────────────────────────
def preflight() -> bool:
    """실행 전 환경 확인."""
    ok = True
    export_py = CRAWLERS_DIR / "export_json.py"
    if not export_py.exists():
        print(f"[FAIL] export_json.py 없음: {export_py}")
        ok = False
    # Python 패키지 확인
    for pkg in ["httpx", "bs4", "lxml"]:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[FAIL] Python 패키지 누락: {pkg}")
            print(f"       → pip install httpx beautifulsoup4 lxml")
            ok = False
    return ok


# ────────────────────────────────────────────────
# 2. Backup
# ────────────────────────────────────────────────
def backup(run_id: str) -> Path:
    """현재 데이터 파일을 백업 디렉토리에 복사."""
    backup_dir = BACKUP_BASE / run_id
    backup_dir.mkdir(parents=True, exist_ok=True)
    for src_path, name in [
        (SRC_JOBS, "jobs.before.json"),
        (PUB_JOBS, "public_jobs.before.json"),
        (PUB_STATS, "stats.before.json"),
    ]:
        if src_path.exists():
            shutil.copy2(src_path, backup_dir / name)
    print(f"  백업 완료: {backup_dir}")
    return backup_dir


# ────────────────────────────────────────────────
# 3. Crawl (with timeout & log)
# ────────────────────────────────────────────────
def crawl(run_id: str) -> tuple[int, float, Path]:
    """export_json.py를 subprocess로 실행. (returncode, duration_sec, log_path) 반환."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / f"crawl_{run_id}.log"

    cmd = [sys.executable, "-u", str(CRAWLERS_DIR / "export_json.py")]
    start = time.time()

    with open(log_path, "w", encoding="utf-8") as log_f:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                stdout=log_f,
                stderr=subprocess.STDOUT,
                timeout=TIMEOUT_SEC,
                check=False,
            )
            rc = result.returncode
        except subprocess.TimeoutExpired:
            log_f.write(f"\n[TIMEOUT] {TIMEOUT_SEC}초 초과\n")
            rc = 124

    duration = time.time() - start
    print(f"  크롤링 완료: exit={rc}, {duration:.1f}s, 로그={log_path}")
    return rc, duration, log_path


# ────────────────────────────────────────────────
# 4. Validate
# ────────────────────────────────────────────────
def validate(backup_dir: Path, log_path: Path | None = None) -> tuple[str, list[str]]:
    """
    데이터 무결성 검증.
    Returns: (status, warnings)
        status: "OK" | "WARNING" | "FAILED"
    """
    warnings: list[str] = []
    failed = False

    # 파일 존재
    for p in [SRC_JOBS, PUB_JOBS, PUB_STATS]:
        if not p.exists():
            warnings.append(f"파일 없음: {p.name}")
            failed = True

    # JSON 파싱
    jobs = _load_json(SRC_JOBS)
    if jobs is None:
        warnings.append("src/data/jobs.json 파싱 실패")
        failed = True
    elif not isinstance(jobs, list):
        warnings.append("jobs.json이 배열이 아님")
        failed = True
    elif len(jobs) == 0:
        warnings.append("jobs.json이 비어 있음 (0건)")
        failed = True
    else:
        # 필수 필드 검사 (첫 10건 샘플)
        sample = jobs[:10]
        for i, j in enumerate(sample):
            missing = [f for f in REQUIRED_FIELDS if not j.get(f)]
            if missing:
                warnings.append(f"job[{i}] 필수필드 누락: {missing}")

        # 이전 대비 급감 확인
        prev_stats = _load_json(backup_dir / "stats.before.json")
        if prev_stats and isinstance(prev_stats, dict):
            prev_total = prev_stats.get("totalJobs", 0)
            curr_total = len(jobs)
            if prev_total > 50 and curr_total < prev_total * DROP_THRESHOLD:
                warnings.append(
                    f"총 건수 급감: {prev_total} → {curr_total} "
                    f"({curr_total/prev_total*100:.0f}%)"
                )

        # 소스별 급감 확인
        prev_jobs = _load_json(backup_dir / "jobs.before.json")
        if prev_jobs and isinstance(prev_jobs, list):
            prev_src = _source_counts(prev_jobs)
            curr_src = _source_counts(jobs)

            # 로그에서 "건너뜀" 표시된 소스 수집 (사이트 점검 등)
            skipped_sources: set[str] = set()
            if log_path.exists():
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        if "건너뜀" in line:
                            for src_name in prev_src:
                                if src_name.replace("교육청", "") in line:
                                    skipped_sources.add(src_name)

            for src, prev_cnt in prev_src.items():
                curr_cnt = curr_src.get(src, 0)
                if prev_cnt >= 10 and curr_cnt == 0:
                    if src in skipped_sources:
                        warnings.append(
                            f"소스 일시중단: {src} (사이트 점검/접속불가 — 건너뜀)"
                        )
                    else:
                        warnings.append(
                            f"소스 급감: {src} {prev_cnt}건 → 0건 (구조변경 가능성)"
                        )

    stats = _load_json(PUB_STATS)
    if stats is None:
        warnings.append("stats.json 파싱 실패")

    if failed:
        return "FAILED", warnings
    elif warnings:
        return "WARNING", warnings
    return "OK", warnings


# ────────────────────────────────────────────────
# 5. Rollback (검증 실패 시)
# ────────────────────────────────────────────────
def rollback(backup_dir: Path):
    """검증 실패 시 이전 데이터로 복원."""
    restored = 0
    for backup_name, target in [
        ("jobs.before.json", SRC_JOBS),
        ("public_jobs.before.json", PUB_JOBS),
        ("stats.before.json", PUB_STATS),
    ]:
        src = backup_dir / backup_name
        if src.exists():
            shutil.copy2(src, target)
            restored += 1
    print(f"  [ROLLBACK] {restored}개 파일 복원 완료")


# ────────────────────────────────────────────────
# 6. Diff & Report
# ────────────────────────────────────────────────
def generate_report(
    run_id: str,
    backup_dir: Path,
    crawl_rc: int,
    duration: float,
    log_path: Path,
    status: str,
    warnings: list[str],
) -> str:
    """리포트 문자열 생성."""
    lines: list[str] = []
    sep = "=" * 60

    lines.append(sep)
    lines.append(f"  강사구인 크롤링 리포트")
    lines.append(f"  실행 ID: {run_id}")
    lines.append(f"  상태: {status}")
    lines.append(f"  소요 시간: {duration:.0f}초")
    lines.append(sep)

    # 현재 데이터
    jobs = _load_json(SRC_JOBS)
    stats = _load_json(PUB_STATS)
    curr_total = len(jobs) if isinstance(jobs, list) else 0

    # 이전 데이터
    prev_stats = _load_json(backup_dir / "stats.before.json")
    prev_total = prev_stats.get("totalJobs", 0) if isinstance(prev_stats, dict) else 0

    lines.append(f"\n총 공고: {curr_total}건")
    if prev_total:
        diff = curr_total - prev_total
        sign = "+" if diff >= 0 else ""
        lines.append(f"이전 대비: {prev_total} → {curr_total} ({sign}{diff})")

    # 소스별
    if isinstance(jobs, list):
        curr_src = _source_counts(jobs)
        prev_jobs = _load_json(backup_dir / "jobs.before.json")
        prev_src = _source_counts(prev_jobs) if isinstance(prev_jobs, list) else {}

        lines.append("\n소스별:")
        all_sources = sorted(
            set(list(curr_src.keys()) + list(prev_src.keys())),
            key=lambda s: curr_src.get(s, 0),
            reverse=True,
        )
        for src in all_sources:
            c = curr_src.get(src, 0)
            p = prev_src.get(src, 0)
            delta = ""
            if p:
                d = c - p
                delta = f" ({'+' if d >= 0 else ''}{d})"
            warn = ""
            if p >= 10 and c == 0:
                warn = " ⚠️ 급감"
            lines.append(f"  {src}: {c}건{delta}{warn}")

    # 기관유형별
    if isinstance(stats, dict) and "orgTypes" in stats:
        lines.append("\n기관유형별:")
        for ot, cnt in sorted(stats["orgTypes"].items(), key=lambda x: -x[1]):
            lines.append(f"  {ot}: {cnt}건")

    # 분야별
    if isinstance(stats, dict) and "categories" in stats:
        lines.append("\n분야별:")
        for cat, cnt in sorted(stats["categories"].items(), key=lambda x: -x[1]):
            lines.append(f"  {cat}: {cnt}건")

    # 경고
    if warnings:
        lines.append("\n⚠️ 경고:")
        for w in warnings:
            lines.append(f"  - {w}")

    # 로그 에러 스캔
    if log_path.exists():
        import re

        error_pattern = re.compile(
            r"오류|에러|error|fail|exception|traceback|timeout|403|404|429|500|502|503"
            r"|connection reset|blocked|forbidden",
            re.IGNORECASE,
        )
        error_lines = []
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if error_pattern.search(line):
                    error_lines.append(line.strip())
        if error_lines:
            lines.append(f"\n로그 에러 ({len(error_lines)}건):")
            for el in error_lines[:10]:
                lines.append(f"  {el[:120]}")
            if len(error_lines) > 10:
                lines.append(f"  ... 외 {len(error_lines)-10}건")

    # 마감 임박
    if isinstance(jobs, list):
        from datetime import timedelta

        today = datetime.now().strftime("%Y-%m-%d")
        soon = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        urgent = [
            j for j in jobs
            if j.get("deadlineText", "")[:10] >= today
            and j.get("deadlineText", "")[:10] <= soon
        ]
        if urgent:
            lines.append(f"\n마감 임박 (3일 이내): {len(urgent)}건")
            for j in urgent[:5]:
                lines.append(f"  - {j['title'][:60]}")
                lines.append(f"    {j.get('organization','')} | 마감: {j.get('deadlineText','')[:10]}")

    lines.append(f"\n{sep}")
    lines.append(f"  로그: {log_path}")
    lines.append(f"  백업: {backup_dir}")
    lines.append(sep)

    return "\n".join(lines)


# ────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────
def main():
    dry_run = "--dry" in sys.argv
    run_id = _now_id()

    print(f"\n{'='*60}")
    print(f"  강사구인 크롤링 시작 — {run_id}")
    print(f"{'='*60}\n")

    # 1. Preflight
    print("[1/6] Preflight...")
    if not preflight():
        print("[ABORT] 환경 확인 실패")
        sys.exit(1)
    print("  OK\n")

    # 2. Backup
    print("[2/6] 백업...")
    backup_dir = backup(run_id)
    print()

    # 3. Crawl
    if dry_run:
        print("[3/6] 크롤링 건너뜀 (--dry)\n")
        crawl_rc, duration, log_path = 0, 0.0, LOG_DIR / "dry.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("dry run\n")
    else:
        print("[3/6] 크롤링...")
        crawl_rc, duration, log_path = crawl(run_id)
        if crawl_rc == 124:
            print(f"  [TIMEOUT] {TIMEOUT_SEC}초 초과!")
        elif crawl_rc != 0:
            print(f"  [ERROR] exit code = {crawl_rc}")
        print()

    # 4. Validate
    print("[4/6] 데이터 검증...")
    status, warnings = validate(backup_dir, log_path)
    if status == "FAILED" and not dry_run:
        print(f"  [FAILED] 검증 실패 — 이전 데이터로 복원합니다")
        rollback(backup_dir)
        status = "FAILED+ROLLBACK"
    elif status == "WARNING":
        print(f"  [WARNING] {len(warnings)}건의 경고")
    else:
        print(f"  OK")
    print()

    # Override status if crawl itself failed
    if crawl_rc == 124:
        status = "TIMEOUT"
    elif crawl_rc != 0 and status == "OK":
        status = "WARNING"

    # 5. Report
    print("[5/6] 리포트 생성...")
    report = generate_report(
        run_id, backup_dir, crawl_rc, duration, log_path, status, warnings
    )
    print(report)

    # Save report to file
    report_path = backup_dir / "report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(f"\n리포트 저장: {report_path}")

    # 6. Summary
    print(f"\n[6/6] 완료: {status}")

    # exit code
    if status in ("FAILED", "FAILED+ROLLBACK", "TIMEOUT"):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
