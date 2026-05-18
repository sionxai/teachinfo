"use client";

import { doc, updateDoc, serverTimestamp } from "firebase/firestore";
import { Bell } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { db } from "@/lib/firebase/client";

export default function SettingsPage() {
  const { firebaseUser, profile } = useAuth();
  const [emailNotif, setEmailNotif] = useState(true);
  const [pushNotif, setPushNotif] = useState(false);
  const [keywords, setKeywords] = useState("");
  const [notiRegions, setNotiRegions] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile?.notificationSettings) {
      const ns = profile.notificationSettings;
      setEmailNotif(ns.email);
      setPushNotif(ns.push);
      setKeywords(ns.keywords?.join(", ") ?? "");
      setNotiRegions(ns.regions?.join(", ") ?? "");
    }
  }, [profile]);

  async function save() {
    if (!firebaseUser || !db) return;
    setSaving(true);
    try {
      await updateDoc(doc(db, "users", firebaseUser.uid), {
        notificationSettings: {
          email: emailNotif,
          push: pushNotif,
          keywords: keywords.split(",").map((s) => s.trim()).filter(Boolean),
          regions: notiRegions.split(",").map((s) => s.trim()).filter(Boolean),
          orgTypes: profile?.notificationSettings?.orgTypes ?? [],
        },
        updatedAt: serverTimestamp(),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  if (!firebaseUser) {
    return <div className="mx-auto max-w-2xl px-4 py-8 text-center text-muted-foreground">로그인 후 이용 가능합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2"><Bell className="h-7 w-7" />알림 설정</h1>

      <Card>
        <CardHeader><CardTitle>알림 방식</CardTitle></CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Label>이메일 알림</Label>
            <Switch checked={emailNotif} onCheckedChange={setEmailNotif} />
          </div>
          <div className="flex items-center justify-between">
            <Label>푸시 알림 (준비 중)</Label>
            <Switch checked={pushNotif} onCheckedChange={setPushNotif} />
          </div>
        </CardContent>
      </Card>

      <Card className="mt-4">
        <CardHeader><CardTitle>맞춤 알림</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>키워드 (쉼표로 구분)</Label>
            <Input value={keywords} onChange={(e) => setKeywords(e.target.value)} placeholder="IT, 리더십, 코딩" />
            <div className="flex flex-wrap gap-1">
              {keywords.split(",").map((s) => s.trim()).filter(Boolean).map((s) => <Badge key={s} variant="secondary">{s}</Badge>)}
            </div>
          </div>
          <div className="grid gap-2">
            <Label>관심 지역 (쉼표로 구분)</Label>
            <Input value={notiRegions} onChange={(e) => setNotiRegions(e.target.value)} placeholder="서울, 경기" />
            <div className="flex flex-wrap gap-1">
              {notiRegions.split(",").map((s) => s.trim()).filter(Boolean).map((s) => <Badge key={s} variant="outline">{s}</Badge>)}
            </div>
          </div>
          <Button onClick={save} disabled={saving}>{saved ? "저장 완료!" : saving ? "저장 중..." : "저장"}</Button>
        </CardContent>
      </Card>
    </div>
  );
}
