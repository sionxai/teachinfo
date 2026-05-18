"use client";

import { deleteDoc, doc, getDoc, serverTimestamp, setDoc } from "firebase/firestore";
import { Heart } from "lucide-react";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { Button } from "@/components/ui/button";
import { db } from "@/lib/firebase/client";
import type { TimestampLike } from "@/types";

type BookmarkButtonProps = {
  jobId: string;
  jobTitle: string;
  organization: string;
  deadlineAt?: TimestampLike;
};

export function BookmarkButton({ jobId, jobTitle, organization, deadlineAt }: BookmarkButtonProps) {
  const { firebaseUser } = useAuth();
  const [bookmarked, setBookmarked] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!db || !firebaseUser) {
      setBookmarked(false);
      return;
    }

    getDoc(doc(db, "users", firebaseUser.uid, "bookmarks", jobId)).then((snapshot) => {
      setBookmarked(snapshot.exists());
    });
  }, [firebaseUser, jobId]);

  async function toggleBookmark() {
    if (!db || !firebaseUser) {
      alert("로그인이 필요합니다.");
      return;
    }

    setBusy(true);
    const ref = doc(db, "users", firebaseUser.uid, "bookmarks", jobId);
    if (bookmarked) {
      await deleteDoc(ref);
      setBookmarked(false);
    } else {
      await setDoc(ref, {
        jobTitle,
        organization,
        deadlineAt: deadlineAt ?? null,
        createdAt: serverTimestamp(),
      });
      setBookmarked(true);
    }
    setBusy(false);
  }

  return (
    <Button
      type="button"
      variant={bookmarked ? "default" : "outline"}
      size="sm"
      onClick={toggleBookmark}
      disabled={busy}
    >
      <Heart className={bookmarked ? "h-4 w-4 fill-current" : "h-4 w-4"} />
      {bookmarked ? "저장됨" : "북마크"}
    </Button>
  );
}
