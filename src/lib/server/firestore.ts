import type { QueryDocumentSnapshot } from "firebase-admin/firestore";

export function serializeFirestore<T>(value: unknown): T {
  if (!value || typeof value !== "object") return value as T;
  if (value instanceof Date) return value.toISOString() as T;
  if ("toDate" in value && typeof value.toDate === "function") {
    return value.toDate().toISOString() as T;
  }
  if (Array.isArray(value)) return value.map((item) => serializeFirestore(item)) as T;

  return Object.fromEntries(
    Object.entries(value).map(([key, item]) => [key, serializeFirestore(item)]),
  ) as T;
}

export function serializeDoc<T>(doc: QueryDocumentSnapshot) {
  return { id: doc.id, ...serializeFirestore<T>(doc.data()) } as T & { id: string };
}
