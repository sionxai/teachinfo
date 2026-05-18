import type { FieldValue, Timestamp } from "firebase/firestore";

export type TimestampLike = Date | string | number | Timestamp | FieldValue | null | undefined;

export type OrgType = "government" | "quasi_gov" | "university" | "corporate" | "other";
export type DeadlineType = "fixed" | "until_filled" | "until_budget" | "unknown";
export type JobStatus = "active" | "expired" | "closed" | "hidden";
export type UserRole = "user" | "admin";
export type CalendarEventType = "deadline" | "interview" | "lecture" | "custom";
export type PostCategory = "free" | "info" | "review" | "qna";
export type CrawlRunStatus = "success" | "partial" | "failed";

export interface BaseDocument {
  id?: string;
  createdAt?: TimestampLike;
  updatedAt?: TimestampLike;
}

export interface JobAttachment {
  name: string;
  url: string;
  storagePath?: string;
  type?: string;
}

export interface Job extends BaseDocument {
  title: string;
  organization: string;
  orgType: OrgType;
  orgSubType?: string;
  category: string;
  region: string;
  regionDetail?: string;
  description: string;
  requirements?: string;
  pay?: string;
  deadlineAt?: TimestampLike;
  deadlineText?: string;
  deadlineType: DeadlineType;
  applyUrl?: string;
  applyMethod?: string;
  contactInfo?: string;
  sourceUrl?: string;
  canonicalUrl?: string;
  sourceId?: string;
  sourceName?: string;
  externalPostId?: string;
  contentHash?: string;
  dedupeKey?: string;
  extractionConfidence?: number;
  rawStoragePath?: string;
  attachments: JobAttachment[];
  status: JobStatus;
  publishedAt?: TimestampLike;
  lastSeenAt?: TimestampLike;
  viewCount: number;
  bookmarkCount: number;
  crawledAt?: TimestampLike;
}

export interface Source extends BaseDocument {
  name: string;
  url: string;
  type: string;
  subType?: string;
  region?: string;
  parserType: string;
  crawlerModule?: string;
  enabled: boolean;
  rateLimit: number;
  timeout: number;
  maxRetries: number;
  robotsPolicy: "respect" | "ignore" | "manual";
  lastSuccessAt?: TimestampLike;
  lastFailureAt?: TimestampLike;
  failureCount: number;
  totalCrawled: number;
}

export interface CrawlRun {
  id?: string;
  sourceId: string;
  sourceName: string;
  startedAt: TimestampLike;
  finishedAt?: TimestampLike;
  status: CrawlRunStatus;
  newCount: number;
  updatedCount: number;
  skippedCount: number;
  errorCount: number;
  errors: string[];
  duration: number;
}

export interface NotificationSettings {
  email: boolean;
  push: boolean;
  keywords: string[];
  regions: string[];
  orgTypes: OrgType[];
  categories?: string[];
  deadlineReminderDays?: number[];
}

export interface User extends BaseDocument {
  email: string;
  displayName: string;
  profileImage?: string;
  bio?: string;
  specialties: string[];
  regions: string[];
  role: UserRole;
  notificationSettings: NotificationSettings;
}

export interface Bookmark {
  id?: string;
  jobTitle: string;
  organization: string;
  deadlineAt?: TimestampLike;
  createdAt?: TimestampLike;
}

export interface CalendarEvent extends BaseDocument {
  jobId?: string;
  title: string;
  date: TimestampLike;
  type: CalendarEventType;
  memo?: string;
  reminder: boolean;
}

export interface Post extends BaseDocument {
  authorId: string;
  authorName: string;
  category: PostCategory;
  title: string;
  content: string;
  viewCount: number;
  commentCount: number;
  likeCount: number;
}

export interface Comment extends BaseDocument {
  authorId: string;
  authorName: string;
  content: string;
}
