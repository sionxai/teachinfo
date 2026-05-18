"use client";

import { Search, Loader2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { JobCard } from "@/components/jobs/job-card";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getJobs, getCategories, getRegions } from "@/lib/data";
import type { Job } from "@/types";

const PAGE_SIZE = 12;

function filterJobs(
  all: Job[],
  opts: { keyword: string; region: string; category: string; orgType: string },
) {
  let filtered = all;
  if (opts.keyword) {
    const kw = opts.keyword.toLowerCase();
    filtered = filtered.filter((j) =>
      [j.title, j.organization, j.description, j.region, j.category]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(kw)),
    );
  }
  if (opts.region !== "all") filtered = filtered.filter((j) => j.region === opts.region);
  if (opts.category !== "all") filtered = filtered.filter((j) => j.category === opts.category);
  if (opts.orgType !== "all") filtered = filtered.filter((j) => j.orgType === opts.orgType);
  return filtered;
}

export default function JobsPage() {
  const allJobs = useMemo(() => getJobs(), []);
  const categories = useMemo(() => getCategories(), []);
  const regions = useMemo(() => getRegions().filter((r) => r.name !== "미분류"), []);

  const [keyword, setKeyword] = useState("");
  const [region, setRegion] = useState("all");
  const [category, setCategory] = useState("all");
  const [orgType, setOrgType] = useState("all");
  const [visibleCount, setVisibleCount] = useState(PAGE_SIZE);
  const [loading, setLoading] = useState(false);

  const sentinelRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(
    () => filterJobs(allJobs, { keyword, region, category, orgType }),
    [allJobs, keyword, region, category, orgType],
  );

  const visible = useMemo(() => filtered.slice(0, visibleCount), [filtered, visibleCount]);
  const hasMore = visibleCount < filtered.length;

  // 필터 변경 시 리셋
  useEffect(() => {
    setVisibleCount(PAGE_SIZE);
  }, [keyword, region, category, orgType]);

  // Intersection Observer로 무한 스크롤
  const loadMore = useCallback(() => {
    if (!hasMore || loading) return;
    setLoading(true);
    // 약간의 딜레이로 자연스러운 로딩 느낌
    setTimeout(() => {
      setVisibleCount((prev) => prev + PAGE_SIZE);
      setLoading(false);
    }, 300);
  }, [hasMore, loading]);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore();
      },
      { rootMargin: "200px" },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [loadMore]);

  function resetFilters() {
    setKeyword("");
    setRegion("all");
    setCategory("all");
    setOrgType("all");
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 space-y-2">
        <h1 className="text-3xl font-bold">구인 목록</h1>
        <p className="text-muted-foreground">
          총 <span className="font-semibold text-foreground">{filtered.length}</span>개의 공고
        </p>
      </div>

      {/* 분야 빠른 필터 */}
      <div className="mb-4 flex flex-wrap gap-1.5">
        <Badge
          variant={category === "all" ? "default" : "secondary"}
          className="cursor-pointer px-3 py-1.5 transition-colors"
          onClick={() => setCategory("all")}
        >
          전체
        </Badge>
        {categories.map(({ name, count }) => (
          <Badge
            key={name}
            variant={category === name ? "default" : "secondary"}
            className="cursor-pointer px-3 py-1.5 transition-colors"
            onClick={() => setCategory(name)}
          >
            {name} ({count})
          </Badge>
        ))}
      </div>

      {/* 상세 필터 */}
      <Card className="mb-6">
        <CardContent className="grid gap-3 p-4 md:grid-cols-[1.4fr_1fr_1fr_auto]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              placeholder="공고명, 기관명 검색"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
            />
          </div>
          <Select value={region} onValueChange={setRegion}>
            <SelectTrigger><SelectValue placeholder="지역" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">지역 전체</SelectItem>
              {regions.map(({ name, count }) => (
                <SelectItem key={name} value={name}>{name} ({count})</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={orgType} onValueChange={setOrgType}>
            <SelectTrigger><SelectValue placeholder="기관유형" /></SelectTrigger>
            <SelectContent>
              <SelectItem value="all">기관유형 전체</SelectItem>
              <SelectItem value="government">관공서</SelectItem>
              <SelectItem value="quasi_gov">준관공서</SelectItem>
              <SelectItem value="university">대학교</SelectItem>
              <SelectItem value="corporate">기업</SelectItem>
              <SelectItem value="other">기타</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={resetFilters}>초기화</Button>
        </CardContent>
      </Card>

      {/* 결과 (무한 스크롤) */}
      {visible.length ? (
        <>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {visible.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          {/* 로딩 인디케이터 + 센티넬 */}
          <div ref={sentinelRef} className="flex justify-center py-8">
            {loading && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm">불러오는 중...</span>
              </div>
            )}
            {!hasMore && visible.length > PAGE_SIZE && (
              <p className="text-sm text-muted-foreground">모든 공고를 확인했습니다.</p>
            )}
          </div>
        </>
      ) : (
        <Card>
          <CardContent className="p-10 text-center text-muted-foreground">
            조건에 맞는 공고가 없습니다.
          </CardContent>
        </Card>
      )}
    </div>
  );
}
