import Link from "next/link";
import { ArrowRight, Database, Layers, MessageSquare } from "lucide-react";

import { HeroIllustration } from "@/components/illustrations/HeroIllustration";
import { JobCard } from "@/components/jobs/job-card";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getLatestJobs, getStats, getCategories } from "@/lib/data";
import { Badge } from "@/components/ui/badge";

export default function HomePage() {
  const jobs = getLatestJobs(6);
  const stats = getStats();
  const categories = getCategories();
  const statCards = [
    {
      icon: <Database className="h-5 w-5" />,
      label: "등록 공고",
      value: stats.jobs,
      helper: "실시간 수집 데이터",
      iconClassName: "bg-blue-50 text-blue-600",
      progressClassName: "w-4/5 bg-blue-500",
    },
    {
      icon: <Layers className="h-5 w-5" />,
      label: "수집 소스",
      value: stats.sources,
      helper: "기관·채용 플랫폼",
      iconClassName: "bg-zinc-100 text-zinc-900",
      progressClassName: "w-2/3 bg-zinc-900",
    },
    {
      icon: <MessageSquare className="h-5 w-5" />,
      label: "분야 수",
      value: categories.length,
      helper: "카테고리 필터",
      iconClassName: "bg-blue-100 text-blue-600",
      progressClassName: "w-3/5 bg-blue-600",
    },
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 md:py-12">
      <section className="overflow-hidden rounded-2xl border bg-gradient-to-br from-blue-50 via-white to-zinc-50 px-5 py-8 shadow-sm md:px-10 md:py-12">
        <div className="grid gap-8 md:grid-cols-[1.2fr_0.8fr] md:items-center">
          <div className="space-y-6">
            <div className="inline-flex rounded-full border border-blue-100 bg-white/80 px-3 py-1 text-sm font-medium text-blue-700 shadow-sm">
              강사 공고 수집 · 북마크 · 일정관리
            </div>
            <div className="space-y-4">
              <h1 className="text-3xl font-bold tracking-normal text-zinc-900 md:text-5xl md:leading-tight">
                강사 구인 공고를 한 곳에서 확인하세요
              </h1>
              <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
                관공서·준관공서·기업 등에서 매일 수집되는 강사 구인 정보를 한눈에 확인하고, 분야별로 필터링하세요.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button asChild className="shadow-md shadow-zinc-900/10">
                <Link href="/jobs">
                  구인정보 보기
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild variant="outline" className="bg-white/80">
                <Link href="/community">커뮤니티</Link>
              </Button>
            </div>
          </div>

          <div>
            <HeroIllustration className="mx-auto h-auto w-full max-w-[390px]" />
          </div>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {statCards.map((item) => (
            <StatCard key={item.label} {...item} />
          ))}
        </div>
      </section>

      {/* 분야별 통계 */}
      <section className="mt-10">
        <h2 className="mb-3 text-xl font-semibold">분야별 공고 현황</h2>
        <div className="flex flex-wrap gap-2">
          {categories.map(({ name, count }) => (
            <Link key={name} href={`/jobs?category=${encodeURIComponent(name)}`}>
              <Badge
                variant="secondary"
                className="cursor-pointer px-3 py-1.5 text-sm shadow-sm transition-all duration-200 hover:-translate-y-1 hover:bg-primary hover:text-primary-foreground hover:shadow-md"
              >
                {name} <span className="ml-1 font-bold">{count}</span>
              </Badge>
            </Link>
          ))}
        </div>
      </section>

      {/* 최신 공고 */}
      <section className="mt-10">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-2xl font-semibold">최신 구인</h2>
          <Button asChild variant="ghost" size="sm">
            <Link href="/jobs">전체 보기</Link>
          </Button>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      </section>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  helper,
  iconClassName,
  progressClassName,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  helper: string;
  iconClassName: string;
  progressClassName: string;
}) {
  return (
    <Card className="overflow-hidden border-zinc-200/80 bg-white/85 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
        <span className={`flex h-9 w-9 items-center justify-center rounded-full ${iconClassName}`}>{icon}</span>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-3xl font-bold">{value.toLocaleString("ko-KR")}</div>
        <div className="space-y-1.5">
          <div className="h-1.5 overflow-hidden rounded-full bg-zinc-100">
            <div className={`h-full rounded-full ${progressClassName}`} />
          </div>
          <p className="text-xs text-muted-foreground">{helper}</p>
        </div>
      </CardContent>
    </Card>
  );
}
