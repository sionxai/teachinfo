"use client";

import { collection, getDocs, limit, orderBy, query, where } from "firebase/firestore";
import { Activity, AlertTriangle, CheckCircle, Database, Radar } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { CrawlRun, Source } from "@/types";

export default function AdminPage() {
  const { isAdmin } = useAuth();
  const [stats, setStats] = useState({ jobs: 0, sources: 0, activeSources: 0 });
  const [recentRuns, setRecentRuns] = useState<(CrawlRun & { id: string })[]>([]);

  useEffect(() => {
    if (!isAdmin || !db) return;
    Promise.all([
      getDocs(query(collection(db, "jobs"), where("status", "==", "active"), limit(1000))),
      getDocs(collection(db, "sources")),
      getDocs(query(collection(db, "crawlRuns"), orderBy("startedAt", "desc"), limit(10))),
    ]).then(([jobsSnap, sourcesSnap, runsSnap]) => {
      const sources = sourcesSnap.docs.map((d) => d.data() as Source);
      setStats({
        jobs: jobsSnap.size,
        sources: sources.length,
        activeSources: sources.filter((s) => s.enabled).length,
      });
      setRecentRuns(runsSnap.docs.map((d) => ({ id: d.id, ...d.data() }) as CrawlRun & { id: string }));
    });
  }, [isAdmin]);

  if (!isAdmin) {
    return <div className="mx-auto max-w-4xl px-4 py-8 text-center text-muted-foreground">관리자 권한이 필요합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">관리자 대시보드</h1>

      <div className="grid gap-4 md:grid-cols-3 mb-8">
        <StatCard icon={<Database className="h-5 w-5" />} label="활성 공고" value={stats.jobs} href="/admin/jobs" />
        <StatCard icon={<Radar className="h-5 w-5" />} label="크롤링 소스" value={`${stats.activeSources} / ${stats.sources}`} href="/admin/sources" />
        <StatCard icon={<Activity className="h-5 w-5" />} label="최근 크롤링" value={recentRuns.length} href="/admin/crawl-logs" />
      </div>

      <Card>
        <CardHeader><CardTitle>최근 크롤링 실행</CardTitle></CardHeader>
        <CardContent>
          {recentRuns.length ? (
            <div className="space-y-2">
              {recentRuns.slice(0, 5).map((run) => (
                <div key={run.id} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                  <div className="flex items-center gap-2">
                    {run.status === "success" ? <CheckCircle className="h-4 w-4 text-green-600" /> : <AlertTriangle className="h-4 w-4 text-yellow-600" />}
                    <span className="font-medium">{run.sourceName}</span>
                  </div>
                  <div className="flex gap-4 text-muted-foreground">
                    <span>+{run.newCount} 신규</span>
                    <span>{run.duration}초</span>
                    <span>{formatDate(run.startedAt)}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-center text-muted-foreground py-4">크롤링 기록이 없습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ icon, label, value, href }: { icon: React.ReactNode; label: string; value: number | string; href: string }) {
  return (
    <Link href={href}>
      <Card className="hover:bg-muted/50 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
          <span className="text-primary">{icon}</span>
        </CardHeader>
        <CardContent><div className="text-3xl font-bold">{value}</div></CardContent>
      </Card>
    </Link>
  );
}
