import type { TimestampLike } from "@/types";

export function toDate(value: TimestampLike): Date | null {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value === "string" || typeof value === "number") {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? null : date;
  }
  if ("toDate" in value) return value.toDate();
  if ("seconds" in value && typeof value.seconds === "number") {
    return new Date(value.seconds * 1000);
  }
  return null;
}

export function formatDate(value: TimestampLike, fallback = "미정") {
  const date = toDate(value);
  if (!date) return fallback;
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(date);
}

export function toDateInputValue(value: TimestampLike) {
  const date = toDate(value);
  if (!date) return "";
  return date.toISOString().slice(0, 10);
}
