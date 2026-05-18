"use client";

import { collection, getDocs, limit, orderBy, query, where, type QueryConstraint } from "firebase/firestore";
import { MessageSquare, PenLine } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { Post, PostCategory } from "@/types";

const categoryLabels: Record<PostCategory | "all", string> = {
  all: "전체",
  free: "자유",
  info: "정보공유",
  review: "강의후기",
  qna: "Q&A",
};

export default function CommunityPage() {
  const { firebaseUser } = useAuth();
  const [posts, setPosts] = useState<(Post & { id: string })[]>([]);
  const [tab, setTab] = useState<PostCategory | "all">("all");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!db) return;
    setLoading(true);
    const constraints: QueryConstraint[] = [orderBy("createdAt", "desc"), limit(30)];
    if (tab !== "all") constraints.unshift(where("category", "==", tab));

    getDocs(query(collection(db, "posts"), ...constraints))
      .then((snap) => setPosts(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Post & { id: string })))
      .finally(() => setLoading(false));
  }, [tab]);

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">커뮤니티</h1>
          <p className="text-muted-foreground">강사들의 정보 교류 공간</p>
        </div>
        {firebaseUser && (
          <Button asChild><Link href="/community/write"><PenLine className="mr-1 h-4 w-4" />글쓰기</Link></Button>
        )}
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as PostCategory | "all")} className="mb-4">
        <TabsList>
          {Object.entries(categoryLabels).map(([k, v]) => (
            <TabsTrigger key={k} value={k}>{v}</TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {loading ? (
        <Card><CardContent className="p-10 text-center text-muted-foreground">불러오는 중...</CardContent></Card>
      ) : posts.length ? (
        <div className="space-y-2">
          {posts.map((post) => (
            <Link key={post.id} href={`/community/${post.id}`}>
              <Card className="hover:bg-muted/50 transition-colors">
                <CardContent className="flex items-center justify-between p-4">
                  <div className="min-w-0 flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{categoryLabels[post.category] ?? post.category}</Badge>
                      <span className="truncate font-medium">{post.title}</span>
                    </div>
                    <div className="flex gap-3 text-xs text-muted-foreground">
                      <span>{post.authorName}</span>
                      <span>{formatDate(post.createdAt)}</span>
                      <span className="flex items-center gap-1"><MessageSquare className="h-3 w-3" />{post.commentCount ?? 0}</span>
                      <span>조회 {post.viewCount ?? 0}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-10 text-center text-muted-foreground">게시글이 없습니다.</CardContent></Card>
      )}
    </div>
  );
}
