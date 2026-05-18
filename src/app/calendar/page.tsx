"use client";

import { addDoc, collection, deleteDoc, doc, getDocs, orderBy, query, Timestamp } from "firebase/firestore";
import { CalendarDays, Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { db } from "@/lib/firebase/client";
import { toDate } from "@/lib/date";
import type { CalendarEvent, CalendarEventType } from "@/types";

const eventTypeLabels: Record<CalendarEventType, string> = {
  deadline: "마감일",
  interview: "면접",
  lecture: "강의",
  custom: "기타",
};

const eventTypeColors: Record<CalendarEventType, string> = {
  deadline: "bg-red-100 text-red-800",
  interview: "bg-blue-100 text-blue-800",
  lecture: "bg-green-100 text-green-800",
  custom: "bg-gray-100 text-gray-800",
};

export default function CalendarPage() {
  const { firebaseUser } = useAuth();
  const [events, setEvents] = useState<(CalendarEvent & { id: string })[]>([]);
  const [selectedDate, setSelectedDate] = useState<Date>(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [eventType, setEventType] = useState<CalendarEventType>("custom");
  const [memo, setMemo] = useState("");

  useEffect(() => {
    if (!firebaseUser || !db) return;
    const ref = collection(db, "users", firebaseUser.uid, "calendarEvents");
    getDocs(query(ref, orderBy("date", "asc"))).then((snap) => {
      setEvents(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as CalendarEvent & { id: string }));
    });
  }, [firebaseUser]);

  const eventDates = events.map((e) => toDate(e.date)).filter(Boolean) as Date[];

  const dayEvents = events.filter((e) => {
    const d = toDate(e.date);
    return d && d.toDateString() === selectedDate.toDateString();
  });

  async function addEvent() {
    if (!firebaseUser || !db || !title.trim()) return;
    const ref = collection(db, "users", firebaseUser.uid, "calendarEvents");
    const data = {
      title: title.trim(),
      date: Timestamp.fromDate(selectedDate),
      type: eventType,
      memo: memo.trim(),
      reminder: true,
      createdAt: Timestamp.now(),
    };
    const docRef = await addDoc(ref, data);
    setEvents((prev) => [...prev, { id: docRef.id, ...data }]);
    setTitle("");
    setMemo("");
    setDialogOpen(false);
  }

  async function removeEvent(eventId: string) {
    if (!firebaseUser || !db) return;
    await deleteDoc(doc(db, "users", firebaseUser.uid, "calendarEvents", eventId));
    setEvents((prev) => prev.filter((e) => e.id !== eventId));
  }

  if (!firebaseUser) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-8 text-center text-muted-foreground">
        로그인 후 이용 가능합니다.
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">일정 관리</h1>
          <p className="text-muted-foreground">마감일과 강의 일정을 관리하세요.</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button><Plus className="mr-1 h-4 w-4" />일정 추가</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>새 일정 추가</DialogTitle></DialogHeader>
            <div className="grid gap-4 py-2">
              <div className="grid gap-2">
                <Label>제목</Label>
                <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="일정 제목" />
              </div>
              <div className="grid gap-2">
                <Label>유형</Label>
                <Select value={eventType} onValueChange={(v) => setEventType(v as CalendarEventType)}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(eventTypeLabels).map(([k, v]) => (
                      <SelectItem key={k} value={k}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <Label>날짜: {selectedDate.toLocaleDateString("ko-KR")}</Label>
              </div>
              <div className="grid gap-2">
                <Label>메모</Label>
                <Textarea value={memo} onChange={(e) => setMemo(e.target.value)} placeholder="메모 (선택)" />
              </div>
              <Button onClick={addEvent} disabled={!title.trim()}>추가</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <div className="grid gap-6 md:grid-cols-[auto_1fr]">
        <Card>
          <CardContent className="p-4">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(d) => d && setSelectedDate(d)}
              modifiers={{ hasEvent: eventDates }}
              modifiersClassNames={{ hasEvent: "bg-primary/20 font-bold" }}
            />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <CalendarDays className="h-5 w-5" />
              {selectedDate.toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric" })}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dayEvents.length ? (
              <div className="space-y-3">
                {dayEvents.map((ev) => (
                  <div key={ev.id} className="flex items-start justify-between rounded-lg border p-3">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge className={eventTypeColors[ev.type]}>{eventTypeLabels[ev.type]}</Badge>
                        <span className="font-medium">{ev.title}</span>
                      </div>
                      {ev.memo && <p className="text-sm text-muted-foreground">{ev.memo}</p>}
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => removeEvent(ev.id)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-muted-foreground py-8">이 날짜에 일정이 없습니다.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
