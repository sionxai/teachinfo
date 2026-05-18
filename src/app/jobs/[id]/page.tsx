import { notFound } from "next/navigation";
import { CalendarDays, ExternalLink, MapPin, Phone } from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { getJobById } from "@/lib/data";

export default async function JobDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const job = getJobById(id);
  if (!job) notFound();

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Button variant="ghost" size="sm" asChild className="mb-4">
        <Link href="/jobs">← 목록으로</Link>
      </Button>

      <Card>
        <CardHeader className="gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge>{job.category || "분야 미정"}</Badge>
            <Badge variant="secondary">{job.orgType === "corporate" ? "기업" : job.orgType === "government" ? "관공서" : job.orgType === "quasi_gov" ? "준관공서" : job.orgType}</Badge>
            {job.sourceName && <Badge variant="outline">{job.sourceName}</Badge>}
            {job.region && <Badge variant="outline">{job.region}</Badge>}
          </div>
          <div className="space-y-2">
            <CardTitle className="text-2xl leading-9 md:text-3xl">{job.title}</CardTitle>
            <p className="text-lg text-muted-foreground">{job.organization}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {(job.applyUrl || job.sourceUrl) && (
              <Button asChild>
                <a href={job.applyUrl || job.sourceUrl || "#"} target="_blank" rel="noreferrer">
                  지원하기 / 원문 보기
                  <ExternalLink className="h-4 w-4" />
                </a>
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid gap-3 rounded-lg bg-muted p-4 text-sm md:grid-cols-2">
            <Info icon={<MapPin className="h-4 w-4" />} label="지역" value={[job.region, job.regionDetail].filter(Boolean).join(" ") || "미정"} />
            <Info icon={<CalendarDays className="h-4 w-4" />} label="마감" value={job.deadlineText || "미정"} />
            <Info label="급여" value={job.pay || "공고 확인"} />
            <Info label="지원방법" value={job.applyMethod || "공고 확인"} />
            <Info icon={<Phone className="h-4 w-4" />} label="연락처" value={job.contactInfo || "공고 확인"} />
            <Info label="출처" value={job.sourceName || "미정"} />
          </div>

          {job.description && (
            <section className="space-y-3">
              <h2 className="text-lg font-semibold">공고 내용</h2>
              <p className="whitespace-pre-wrap leading-7">{job.description}</p>
            </section>
          )}

          {job.requirements && (
            <>
              <Separator />
              <section className="space-y-3">
                <h2 className="text-lg font-semibold">자격 요건</h2>
                <p className="whitespace-pre-wrap leading-7">{job.requirements}</p>
              </section>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Info({ icon, label, value }: { icon?: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-start gap-2">
      {icon}
      <div>
        <p className="text-muted-foreground">{label}</p>
        <p className="font-medium text-foreground">{value}</p>
      </div>
    </div>
  );
}
