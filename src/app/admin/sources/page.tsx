"use client";

import { addDoc, collection, deleteDoc, doc, getDocs, updateDoc } from "firebase/firestore";
import { Plus, Power, PowerOff, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { Source } from "@/types";

const sourceTypes = ["government", "quasi_gov", "university", "corporate", "blog"];
const sourceTypeLabels: Record<string, string> = {
  government: "관공서", quasi_gov: "준관공서", university: "대학교", corporate: "기업", blog: "블로그/SNS",
};

export default function AdminSourcesPage() {
  const { isAdmin } = useAuth();
  const [sources, setSources] = useState<(Source & { id: string })[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: "", url: "", type: "government", subType: "", region: "", parserType: "custom" });

  useEffect(() => {
    if (!isAdmin || !db) return;
    getDocs(collection(db, "sources")).then((snap) => {
      setSources(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Source & { id: string }));
    });
  }, [isAdmin]);

  async function addSource() {
    if (!db || !form.name.trim() || !form.url.trim()) return;
    const data: Omit<Source, "id"> = {
      name: form.name.trim(),
      url: form.url.trim(),
      type: form.type,
      subType: form.subType.trim(),
      region: form.region.trim(),
      parserType: form.parserType,
      crawlerModule: "",
      enabled: true,
      rateLimit: 2,
      timeout: 30,
      maxRetries: 3,
      robotsPolicy: "respect",
      failureCount: 0,
      totalCrawled: 0,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    const docRef = await addDoc(collection(db, "sources"), data);
    setSources((prev) => [...prev, { id: docRef.id, ...data }]);
    setForm({ name: "", url: "", type: "government", subType: "", region: "", parserType: "custom" });
    setDialogOpen(false);
  }

  async function toggleEnabled(source: Source & { id: string }) {
    if (!db) return;
    await updateDoc(doc(db, "sources", source.id), { enabled: !source.enabled });
    setSources((prev) => prev.map((s) => s.id === source.id ? { ...s, enabled: !s.enabled } : s));
  }

  async function removeSource(id: string) {
    if (!db) return;
    await deleteDoc(doc(db, "sources", id));
    setSources((prev) => prev.filter((s) => s.id !== id));
  }

  if (!isAdmin) {
    return <div className="mx-auto max-w-4xl px-4 py-8 text-center text-muted-foreground">관리자 권한이 필요합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-3xl font-bold">크롤링 소스 관리</h1>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild><Button><Plus className="mr-1 h-4 w-4" />소스 추가</Button></DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>새 크롤링 소스</DialogTitle></DialogHeader>
            <div className="grid gap-4 py-2">
              <div className="grid gap-2"><Label>소스명</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="서울시 청년센터" /></div>
              <div className="grid gap-2"><Label>URL</Label><Input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} placeholder="https://..." /></div>
              <div className="grid gap-2">
                <Label>유형</Label>
                <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>{sourceTypes.map((t) => <SelectItem key={t} value={t}>{sourceTypeLabels[t]}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="grid gap-2"><Label>세부 유형</Label><Input value={form.subType} onChange={(e) => setForm({ ...form, subType: e.target.value })} placeholder="청년센터, 창업지원센터 등" /></div>
              <div className="grid gap-2"><Label>지역</Label><Input value={form.region} onChange={(e) => setForm({ ...form, region: e.target.value })} placeholder="서울" /></div>
              <Button onClick={addSource} disabled={!form.name.trim() || !form.url.trim()}>추가</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-2">
        {sources.map((source) => (
          <Card key={source.id}>
            <CardContent className="flex items-center justify-between p-4">
              <div className="min-w-0 flex-1 space-y-1">
                <div className="flex items-center gap-2">
                  <Badge className={source.enabled ? "bg-green-100 text-green-800" : "bg-gray-100 text-gray-500"}>
                    {source.enabled ? "활성" : "비활성"}
                  </Badge>
                  <Badge variant="secondary">{sourceTypeLabels[source.type] ?? source.type}</Badge>
                  <span className="font-medium">{source.name}</span>
                </div>
                <div className="flex gap-3 text-xs text-muted-foreground">
                  <span>{source.url}</span>
                  {source.region && <span>· {source.region}</span>}
                  <span>· 수집 {source.totalCrawled}건</span>
                  {source.lastSuccessAt && <span>· 최근 성공 {formatDate(source.lastSuccessAt)}</span>}
                  {source.failureCount > 0 && <span className="text-destructive">· 연속 실패 {source.failureCount}회</span>}
                </div>
              </div>
              <div className="flex gap-1">
                <Button variant="ghost" size="icon" onClick={() => toggleEnabled(source)}>
                  {source.enabled ? <PowerOff className="h-4 w-4" /> : <Power className="h-4 w-4" />}
                </Button>
                <Button variant="ghost" size="icon" onClick={() => removeSource(source.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
        {!sources.length && (
          <Card><CardContent className="p-10 text-center text-muted-foreground">등록된 소스가 없습니다.</CardContent></Card>
        )}
      </div>
    </div>
  );
}
