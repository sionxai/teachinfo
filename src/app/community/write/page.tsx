"use client";

import { addDoc, collection, serverTimestamp } from "firebase/firestore";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { db } from "@/lib/firebase/client";
import type { PostCategory } from "@/types";

const categories: { value: PostCategory; label: string }[] = [
  { value: "free", label: "자유" },
  { value: "info", label: "정보공유" },
  { value: "review", label: "강의후기" },
  { value: "qna", label: "Q&A" },
];

export default function CommunityWritePage() {
  const { firebaseUser, profile } = useAuth();
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState<PostCategory>("free");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit() {
    if (!firebaseUser || !db || !title.trim() || !content.trim()) return;
    setSubmitting(true);
    try {
      const docRef = await addDoc(collection(db, "posts"), {
        authorId: firebaseUser.uid,
        authorName: profile?.displayName ?? "익명",
        category,
        title: title.trim(),
        content: content.trim(),
        viewCount: 0,
        commentCount: 0,
        likeCount: 0,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      });
      router.push(`/community/${docRef.id}`);
    } finally {
      setSubmitting(false);
    }
  }

  if (!firebaseUser) {
    return <div className="mx-auto max-w-2xl px-4 py-8 text-center text-muted-foreground">로그인 후 이용 가능합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <Card>
        <CardHeader><CardTitle>글쓰기</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-2">
            <Label>카테고리</Label>
            <Select value={category} onValueChange={(v) => setCategory(v as PostCategory)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                {categories.map((c) => <SelectItem key={c.value} value={c.value}>{c.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>제목</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="제목을 입력하세요" />
          </div>
          <div className="grid gap-2">
            <Label>내용</Label>
            <Textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="내용을 입력하세요" rows={10} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => router.back()}>취소</Button>
            <Button onClick={handleSubmit} disabled={submitting || !title.trim() || !content.trim()}>
              {submitting ? "등록 중..." : "등록"}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
