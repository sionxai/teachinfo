"use client";

import { addDoc, collection, deleteDoc, doc, getDoc, getDocs, orderBy, query, serverTimestamp, updateDoc, increment } from "firebase/firestore";
import { ArrowLeft, MessageSquare, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { Comment, Post, PostCategory } from "@/types";

const categoryLabels: Record<PostCategory, string> = { free: "자유", info: "정보공유", review: "강의후기", qna: "Q&A" };

export default function PostDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { firebaseUser, profile, isAdmin } = useAuth();
  const [post, setPost] = useState<(Post & { id: string }) | null>(null);
  const [comments, setComments] = useState<(Comment & { id: string })[]>([]);
  const [commentText, setCommentText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!db || !id) return;
    const postRef = doc(db, "posts", id);
    getDoc(postRef).then((snap) => {
      if (snap.exists()) {
        setPost({ id: snap.id, ...snap.data() } as Post & { id: string });
        updateDoc(postRef, { viewCount: increment(1) }).catch(() => {});
      }
    });
    getDocs(query(collection(db, "posts", id, "comments"), orderBy("createdAt", "asc"))).then((snap) => {
      setComments(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as Comment & { id: string }));
    });
  }, [id]);

  async function addComment() {
    if (!firebaseUser || !db || !id || !commentText.trim()) return;
    setSubmitting(true);
    try {
      const data = {
        authorId: firebaseUser.uid,
        authorName: profile?.displayName ?? "익명",
        content: commentText.trim(),
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp(),
      };
      const docRef = await addDoc(collection(db, "posts", id, "comments"), data);
      setComments((prev) => [...prev, { id: docRef.id, ...data }]);
      setCommentText("");
      await updateDoc(doc(db, "posts", id), { commentCount: increment(1) });
    } finally {
      setSubmitting(false);
    }
  }

  async function deleteComment(commentId: string) {
    if (!db || !id) return;
    await deleteDoc(doc(db, "posts", id, "comments", commentId));
    setComments((prev) => prev.filter((c) => c.id !== commentId));
    await updateDoc(doc(db, "posts", id), { commentCount: increment(-1) }).catch(() => {});
  }

  async function deletePost() {
    if (!db || !id) return;
    await deleteDoc(doc(db, "posts", id));
    router.push("/community");
  }

  if (!post) return <div className="mx-auto max-w-3xl px-4 py-8 text-center text-muted-foreground">불러오는 중...</div>;

  const canDelete = firebaseUser?.uid === post.authorId || isAdmin;

  return (
    <div className="mx-auto max-w-3xl px-4 py-8 space-y-6">
      <Button variant="ghost" size="sm" asChild><Link href="/community"><ArrowLeft className="mr-1 h-4 w-4" />목록으로</Link></Button>

      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{categoryLabels[post.category] ?? post.category}</Badge>
            <span className="text-xs text-muted-foreground">{post.authorName} · {formatDate(post.createdAt)} · 조회 {post.viewCount ?? 0}</span>
          </div>
          <CardTitle className="text-2xl">{post.title}</CardTitle>
          {canDelete && (
            <Button variant="destructive" size="sm" onClick={deletePost}><Trash2 className="mr-1 h-4 w-4" />삭제</Button>
          )}
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap leading-7">{post.content}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg"><MessageSquare className="h-5 w-5" />댓글 {comments.length}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {comments.map((c) => (
            <div key={c.id}>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">{c.authorName}</span>
                    <span className="text-muted-foreground">{formatDate(c.createdAt)}</span>
                  </div>
                  <p className="text-sm">{c.content}</p>
                </div>
                {(firebaseUser?.uid === c.authorId || isAdmin) && (
                  <Button variant="ghost" size="icon" onClick={() => deleteComment(c.id)}>
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                )}
              </div>
              <Separator className="mt-3" />
            </div>
          ))}

          {firebaseUser ? (
            <div className="flex gap-2">
              <Textarea value={commentText} onChange={(e) => setCommentText(e.target.value)} placeholder="댓글을 작성하세요" rows={2} className="flex-1" />
              <Button onClick={addComment} disabled={submitting || !commentText.trim()}>등록</Button>
            </div>
          ) : (
            <p className="text-center text-sm text-muted-foreground">로그인 후 댓글을 작성할 수 있습니다.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
