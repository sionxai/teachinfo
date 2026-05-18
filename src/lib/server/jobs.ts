import { getAdminDb } from "@/lib/firebase/admin";
import { serializeDoc, serializeFirestore } from "@/lib/server/firestore";
import type { Job } from "@/types";

export async function getLatestJobs(limitCount = 6) {
  const db = getAdminDb();
  if (!db) return [];

  try {
    const snap = await db
      .collection("jobs")
      .where("status", "==", "active")
      .orderBy("publishedAt", "desc")
      .limit(limitCount)
      .get();

    return snap.docs.map((doc) => serializeDoc<Job>(doc));
  } catch {
    return [];
  }
}

export async function getJobById(id: string) {
  const db = getAdminDb();
  if (!db) return null;

  try {
    const doc = await db.collection("jobs").doc(id).get();
    if (!doc.exists) return null;
    const job = { id: doc.id, ...serializeFirestore<Job>(doc.data()) };
    return job.status === "active" ? job : null;
  } catch {
    return null;
  }
}

export async function getHomeStats() {
  const db = getAdminDb();
  if (!db) return { jobs: 0, sources: 0, posts: 0 };

  try {
    const [jobs, sources, posts] = await Promise.all([
      db.collection("jobs").where("status", "==", "active").limit(1000).get(),
      db.collection("sources").where("enabled", "==", true).limit(1000).get(),
      db.collection("posts").limit(1000).get(),
    ]);

    return { jobs: jobs.size, sources: sources.size, posts: posts.size };
  } catch {
    return { jobs: 0, sources: 0, posts: 0 };
  }
}
