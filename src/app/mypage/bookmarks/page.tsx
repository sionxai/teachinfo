"use client";

import { collection, deleteDoc, doc, getDocs, orderBy, query } from "firebase/firestore";
import { Bookmark, Trash2 } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { db } from "@/lib/firebase/client";
import { formatDate } from "@/lib/date";
import type { Bookmark as BookmarkType } from "@/types";

export default function BookmarksPage() {
  const { firebaseUser } = useAuth();
  const [bookmarks, setBookmarks] = useState<(BookmarkType & { id: string })[]>([]);

  useEffect(() => {
    if (!firebaseUser || !db) return;
    const ref = collection(db, "users", firebaseUser.uid, "bookmarks");
    getDocs(query(ref, orderBy("createdAt", "desc"))).then((snap) => {
      setBookmarks(snap.docs.map((d) => ({ id: d.id, ...d.data() }) as BookmarkType & { id: string }));
    });
  }, [firebaseUser]);

  async function remove(bookmarkId: string) {
    if (!firebaseUser || !db) return;
    await deleteDoc(doc(db, "users", firebaseUser.uid, "bookmarks", bookmarkId));
    setBookmarks((prev) => prev.filter((b) => b.id !== bookmarkId));
  }

  if (!firebaseUser) {
    return <div className="mx-auto max-w-2xl px-4 py-8 text-center text-muted-foreground">로그인 후 이용 가능합니다.</div>;
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="text-3xl font-bold mb-6 flex items-center gap-2"><Bookmark className="h-7 w-7" />북마크</h1>

      {bookmarks.length ? (
        <div className="space-y-2">
          {bookmarks.map((bm) => (
            <Card key={bm.id} className="hover:bg-muted/50 transition-colors">
              <CardContent className="flex items-center justify-between p-4">
                <Link href={`/jobs/${bm.id}`} className="min-w-0 flex-1 space-y-1">
                  <p className="font-medium truncate">{bm.jobTitle}</p>
                  <p className="text-sm text-muted-foreground">{bm.organization} · 마감 {formatDate(bm.deadlineAt)}</p>
                </Link>
                <Button variant="ghost" size="icon" onClick={() => remove(bm.id)}>
                  <Trash2 className="h-4 w-4 text-destructive" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <Card><CardContent className="p-10 text-center text-muted-foreground">북마크한 공고가 없습니다.</CardContent></Card>
      )}
    </div>
  );
}
