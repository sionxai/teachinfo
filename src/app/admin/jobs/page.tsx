"use client";

import { collection, deleteDoc, doc, getDocs, limit, orderBy, query, updateDoc, where, type QueryConstraint } from "firebase/firestore";
import { Eye, EyeOff, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { Job, JobStatus } from "@/types";

const statusLabels: Record<JobStatus, string> = { active: "활성", expired: "만료", closed: "마감", hidden: "숨김" };

export default function AdminJobsPage() {
  const { isAdmin } = useAuth();
  const [jobs, setJobs] = useState<(Job & { id: string })[]>([]);
  const [statusFilter, setStatusFilter] = useState<JobStatus | "all">("active");
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!isAdmin || !db) return;
    const constraints: QueryConstraint[] = [orderBy("createdAt", "desc"), limit(50)];
    if (statusFilter !== "all") constraints.unshift(where("status", "==", statusFilter));
    getDocs(query(collection(db, "jobs"), ...constraints)).then((snap) => {
      setJobs(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Job & { id: string }));
    });
  }, [isAdmin, statusFilter]);

  const filtered = search.trim()
    ? jobs.filter((j) => [j.title, j.organization].some((v) => v?.toLowerCase().includes(search.toLowerCase())))
    : jobs;

  async function toggleHidden(job: Job & { id: string }) {
    if (!db) return;
    const newStatus: JobStatus = job.status === "hidden" ? "active" : "hidden";
    await updateDoc(doc(db, "jobs", job.id), { status: newStatus });
    setJobs((prev) => prev.map((j) => j.id === job.id ? { ...j, status: newStatus } : j));
  }

  async function removeJob(id: string) {
    if (!db) return;
    await deleteDoc(doc(db, "jobs", id));
    setJobs((prev) => prev.filter((j) => j.id !== id));
  }

  if (!isAdmin) {
    return <div className="mx-auto max-w-4xl px-4 py-8 text-center text-muted-foreground">관리자 권한이 필요합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">공고 관리</h1>

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <Tabs value={statusFilter} onValueChange={(v) => setStatusFilter(v as JobStatus | "all")}>
          <TabsList>
            <TabsTrigger value="all">전체</TabsTrigger>
            {Object.entries(statusLabels).map(([k, v]) => <TabsTrigger key={k} value={k}>{v}</TabsTrigger>)}
          </TabsList>
        </Tabs>
        <Input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="제목/기관명 검색" className="max-w-xs" />
      </div>

      <div className="space-y-2">
        {filtered.map((job) => (
          <Card key={job.id}>
            <CardContent className="flex items-center justify-between p-4">
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <Badge variant={job.status === "active" ? "default" : "secondary"}>{statusLabels[job.status]}</Badge>
                  <span className="font-medium truncate">{job.title}</span>
                </div>
                <div className="flex gap-3 text-xs text-muted-foreground">
                  <span>{job.organization}</span>
                  <span>{job.region}</span>
                  <span>마감 {job.deadlineText || formatDate(job.deadlineAt)}</span>
                  <span>조회 {job.viewCount ?? 0}</span>
                  {job.sourceName && <span>출처: {job.sourceName}</span>}
                </div>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" onClick={() => toggleHidden(job)} title={job.status === "hidden" ? "공개" : "숨기기"}>
                  {job.status === "hidden" ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                </Button>
                <Button variant="ghost" size="icon" onClick={() => removeJob(job.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {!filtered.length && (
          <Card><CardContent className="p-10 text-center text-muted-foreground">공고가 없습니다.</CardContent></Card>
        )}
      </div>
    </div>
  );
}
