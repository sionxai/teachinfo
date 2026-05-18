import type { Job } from "@/types";
import jobsRaw from "@/data/jobs.json";

// JSON 데이터를 Job 타입으로 캐스팅
const allJobs: Job[] = (jobsRaw as unknown as Job[]).map((j) => ({
  ...j,
  status: j.status ?? "active",
  viewCount: j.viewCount ?? 0,
  bookmarkCount: j.bookmarkCount ?? 0,
  attachments: j.attachments ?? [],
  deadlineType: j.deadlineType ?? ("unknown" as const),
}));

export function getJobs(): Job[] {
  const today = new Date().toISOString().slice(0, 10);

  return allJobs
    .filter((j) => j.status === "active")
    .sort((a, b) => {
      const dlA = a.deadlineText?.slice(0, 10) ?? "";
      const dlB = b.deadlineText?.slice(0, 10) ?? "";
      const isDateA = /^\d{4}-\d{2}-\d{2}$/.test(dlA);
      const isDateB = /^\d{4}-\d{2}-\d{2}$/.test(dlB);

      // 마감일 없는 공고는 뒤로
      if (isDateA && !isDateB) return -1;
      if (!isDateA && isDateB) return 1;
      if (!isDateA && !isDateB) return 0;

      // 이미 마감된 공고는 뒤로
      const expiredA = dlA < today;
      const expiredB = dlB < today;
      if (!expiredA && expiredB) return -1;
      if (expiredA && !expiredB) return 1;

      // 마감임박순 (가까운 날짜 먼저)
      return dlA.localeCompare(dlB);
    });
}

export function getJobById(id: string): Job | null {
  return allJobs.find((j) => j.id === id) ?? null;
}

export function getLatestJobs(count: number): Job[] {
  return getJobs().slice(0, count);
}

export function searchJobs(opts: {
  keyword?: string;
  region?: string;
  category?: string;
  orgType?: string;
  page?: number;
  pageSize?: number;
}): { jobs: Job[]; total: number; hasMore: boolean } {
  let filtered = getJobs();

  if (opts.keyword) {
    const kw = opts.keyword.toLowerCase();
    filtered = filtered.filter((j) =>
      [j.title, j.organization, j.description, j.region, j.category]
        .filter(Boolean)
        .some((v) => String(v).toLowerCase().includes(kw)),
    );
  }
  if (opts.region && opts.region !== "all") {
    filtered = filtered.filter((j) => j.region === opts.region);
  }
  if (opts.category && opts.category !== "all") {
    filtered = filtered.filter((j) => j.category === opts.category);
  }
  if (opts.orgType && opts.orgType !== "all") {
    filtered = filtered.filter((j) => j.orgType === opts.orgType);
  }

  const total = filtered.length;
  const page = opts.page ?? 1;
  const pageSize = opts.pageSize ?? 9;
  const start = (page - 1) * pageSize;
  const paged = filtered.slice(start, start + pageSize);

  return { jobs: paged, total, hasMore: start + pageSize < total };
}

export function getCategories(): { name: string; count: number }[] {
  const counts: Record<string, number> = {};
  for (const j of getJobs()) {
    counts[j.category] = (counts[j.category] ?? 0) + 1;
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

export function getRegions(): { name: string; count: number }[] {
  const counts: Record<string, number> = {};
  for (const j of getJobs()) {
    const r = j.region || "미분류";
    counts[r] = (counts[r] ?? 0) + 1;
  }
  return Object.entries(counts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

export function getStats() {
  const jobs = getJobs();
  return {
    jobs: jobs.length,
    sources: new Set(jobs.map((j) => j.sourceName)).size,
    posts: 0,
  };
}
