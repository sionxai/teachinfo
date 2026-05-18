"use client";

import { collection, getDocs, limit, orderBy, query } from "firebase/firestore";
import { AlertTriangle, CheckCircle, Clock, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { CrawlRun } from "@/types";

const statusConfig: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  success: { icon: <CheckCircle className="h-4 w-4" />, color: "bg-green-100 text-green-800", label: "성공" },
  partial: { icon: <AlertTriangle className="h-4 w-4" />, color: "bg-yellow-100 text-yellow-800", label: "부분 성공" },
  failed: { icon: <XCircle className="h-4 w-4" />, color: "bg-red-100 text-red-800", label: "실패" },
};

export default function CrawlLogsPage() {
  const { isAdmin } = useAuth();
  const [runs, setRuns] = useState<(CrawlRun & { id: string })[]>([]);

  useEffect(() => {
    if (!isAdmin || !db) return;
    getDocs(query(collection(db, "crawlRuns"), orderBy("startedAt", "desc"), limit(50))).then((snap) => {
      setRuns(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as CrawlRun & { id: string }));
    });
  }, [isAdmin]);

  if (!isAdmin) {
    return <div className="mx-auto max-w-4xl px-4 py-8 text-center text-muted-foreground">관리자 권한이 필요합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">크롤링 로그</h1>

      {runs.length ? (
        <div className="space-y-3">
          {runs.map((run) => {
            const cfg = statusConfig[run.status] ?? statusConfig.failed;
            return (
              <Card key={run.id}>
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Badge className={cfg.color}>{cfg.icon}<span className="ml-1">{cfg.label}</span></Badge>
                      <span className="font-medium">{run.sourceName}</span>
                    </div>
                    <div className="flex items-center gap-1 text-sm text-muted-foreground">
                      <Clock className="h-3 w-3" />
                      {run.duration}초
                    </div>
                  </div>
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <span>신규 {run.newCount}</span>
                    <span>업데이트 {run.updatedCount}</span>
                    <span>스킵 {run.skippedCount}</span>
                    {run.errorCount > 0 && <span className="text-destructive">오류 {run.errorCount}</span>}
                    <span>{formatDate(run.startedAt)}</span>
                  </div>
                  {run.errors?.length > 0 && (
                    <div className="rounded bg-red-50 p-2 text-xs text-red-700">
                      {run.errors.slice(0, 3).map((err, i) => <p key={i}>{err}</p>)}
                      {run.errors.length > 3 && <p>...외 {run.errors.length - 3}건</p>}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card><CardContent className="p-10 text-center text-muted-foreground">크롤링 로그가 없습니다.</CardContent></Card>
      )}
    </div>
  );
}
