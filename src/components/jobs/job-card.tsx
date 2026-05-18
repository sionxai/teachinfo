import Link from "next/link";
import { Briefcase, Building2, CalendarDays, GraduationCap, Landmark, MapPin, type LucideIcon } from "lucide-react";

import { BookmarkButton } from "@/components/jobs/bookmark-button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate, toDate } from "@/lib/date";
import { cn } from "@/lib/utils";
import type { Job, OrgType } from "@/types";

const orgTypeLabels: Record<OrgType, string> = {
  government: "관공서",
  quasi_gov: "준관공서",
  university: "대학교",
  corporate: "기업",
  other: "기타",
};

const orgTypeIcons: Record<OrgType, LucideIcon> = {
  government: Building2,
  quasi_gov: Landmark,
  university: GraduationCap,
  corporate: Briefcase,
  other: Building2,
};

export function JobCard({ job }: { job: Job }) {
  const jobId = job.id ?? "";
  const OrgIcon = orgTypeIcons[job.orgType] ?? Building2;
  const orgTypeLabel = orgTypeLabels[job.orgType] ?? "기관";
  const isUrgent = isDeadlineSoon(job);

  return (
    <Card className="group relative h-full overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
      <div className={cn("absolute inset-y-0 left-0 w-1.5", getCategoryStripe(job.category))} />
      <CardHeader className="gap-3">
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary" className="bg-zinc-100 text-zinc-700">
            {job.category || "분야 미정"}
          </Badge>
          <Badge variant="outline" className="gap-1.5 bg-white">
            <OrgIcon className="h-3.5 w-3.5" />
            {orgTypeLabel}
          </Badge>
          {isUrgent && <Badge variant="destructive">마감임박</Badge>}
        </div>
        <CardTitle className="line-clamp-2 text-base leading-6">
          <Link href={`/jobs/${jobId}`} className="transition-colors group-hover:text-blue-600">
            {job.title}
          </Link>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm text-muted-foreground">
        <p className="flex items-center gap-2">
          <OrgIcon className="h-4 w-4 shrink-0 text-zinc-500" />
          <span className="line-clamp-1">{job.organization}</span>
        </p>
        <p className="flex items-center gap-2">
          <MapPin className="h-4 w-4 shrink-0 text-blue-500" />
          <span>{[job.region, job.regionDetail].filter(Boolean).join(" ") || "지역 미정"}</span>
        </p>
        <p className="flex items-center gap-2">
          <CalendarDays className={cn("h-4 w-4 shrink-0", isUrgent ? "text-red-500" : "text-zinc-500")} />
          <span className={cn(isUrgent && "font-medium text-red-600")}>
            마감 {job.deadlineText || formatDate(job.deadlineAt)}
          </span>
        </p>
        <p className="line-clamp-3 text-foreground/80">{job.description || "상세 설명 없음"}</p>
      </CardContent>
      <CardFooter className="justify-between gap-2">
        <BookmarkButton
          jobId={jobId}
          jobTitle={job.title}
          organization={job.organization}
          deadlineAt={job.deadlineAt}
        />
        <Link href={`/jobs/${jobId}`} className="text-sm font-medium text-primary hover:underline">
          자세히
        </Link>
      </CardFooter>
    </Card>
  );
}

function isDeadlineSoon(job: Job) {
  const deadline = toDate(job.deadlineAt) ?? parseDeadlineText(job.deadlineText);
  if (!deadline) return false;

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const deadlineDate = new Date(deadline.getFullYear(), deadline.getMonth(), deadline.getDate());
  const daysUntilDeadline = (deadlineDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24);

  return daysUntilDeadline >= 0 && daysUntilDeadline <= 7;
}

function parseDeadlineText(text?: string) {
  if (!text || text.includes("상시") || text.includes("채용시")) return null;

  const now = new Date();
  if (text.includes("오늘") || /\d{1,2}시마감/.test(text)) {
    return now;
  }

  const match = text.match(/(\d{1,2})\/(\d{1,2})/);
  if (!match) return null;

  const month = Number(match[1]);
  const day = Number(match[2]);
  if (!month || !day) return null;

  const candidate = new Date(now.getFullYear(), month - 1, day);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  if (candidate.getTime() < today.getTime() - 30 * 24 * 60 * 60 * 1000) {
    candidate.setFullYear(now.getFullYear() + 1);
  }

  return candidate;
}

function getCategoryStripe(category = "") {
  if (category.includes("어학")) return "bg-blue-500";
  if (category.includes("교육")) return "bg-zinc-900";
  if (category.includes("IT") || category.includes("디지털")) return "bg-cyan-500";
  if (category.includes("예술") || category.includes("문화")) return "bg-violet-500";
  if (category.includes("취업") || category.includes("진로")) return "bg-emerald-500";
  return "bg-zinc-300";
}
