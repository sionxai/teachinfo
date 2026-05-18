"use client";

import { doc, updateDoc, serverTimestamp } from "firebase/firestore";
import { User as UserIcon } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { db } from "@/lib/firebase/client";

export default function MyPage() {
  const { firebaseUser, profile } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [bio, setBio] = useState("");
  const [specialties, setSpecialties] = useState("");
  const [regions, setRegions] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile) {
      setDisplayName(profile.displayName ?? "");
      setBio(profile.bio ?? "");
      setSpecialties(profile.specialties?.join(", ") ?? "");
      setRegions(profile.regions?.join(", ") ?? "");
    }
  }, [profile]);

  async function save() {
    if (!firebaseUser || !db) return;
    setSaving(true);
    try {
      await updateDoc(doc(db, "users", firebaseUser.uid), {
        displayName: displayName.trim(),
        bio: bio.trim(),
        specialties: specialties.split(",").map((s) => s.trim()).filter(Boolean),
        regions: regions.split(",").map((s) => s.trim()).filter(Boolean),
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
    <div className="mx-auto max-w-2xl px-4 py-8 space-y-6">
      <h1 className="text-3xl font-bold">마이페이지</h1>

      <div className="flex gap-2">
        <Button variant="outline" size="sm" asChild><Link href="/mypage/bookmarks">북마크</Link></Button>
        <Button variant="outline" size="sm" asChild><Link href="/mypage/settings">알림 설정</Link></Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><UserIcon className="h-5 w-5" />프로필 수정</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>이메일</Label>
            <Input value={profile?.email ?? ""} disabled />
          </div>
          <div className="grid gap-2">
            <Label>이름</Label>
            <Input value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>자기소개</Label>
            <Textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={3} />
          </div>
          <div className="grid gap-2">
            <Label>전문 분야 (쉼표로 구분)</Label>
            <Input value={specialties} onChange={(e) => setSpecialties(e.target.value)} placeholder="IT, 마케팅, 자기계발" />
            <div className="flex flex-wrap gap-1">
              {specialties.split(",").map((s) => s.trim()).filter(Boolean).map((s) => <Badge key={s} variant="secondary">{s}</Badge>)}
            </div>
          </div>
          <div className="grid gap-2">
            <Label>활동 지역 (쉼표로 구분)</Label>
            <Input value={regions} onChange={(e) => setRegions(e.target.value)} placeholder="서울, 경기" />
            <div className="flex flex-wrap gap-1">
              {regions.split(",").map((s) => s.trim()).filter(Boolean).map((s) => <Badge key={s} variant="outline">{s}</Badge>)}
            </div>
          </div>
          <Button onClick={save} disabled={saving}>{saved ? "저장 완료!" : saving ? "저장 중..." : "저장"}</Button>
        </CardContent>
      </Card>
    </div>
  );
}
