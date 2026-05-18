import Link from "next/link";
import { BriefcaseBusiness, Mail, MessageSquare, Rss } from "lucide-react";

const footerGroups = [
  {
    title: "서비스",
    links: [
      { href: "/jobs", label: "구인정보" },
      { href: "/calendar", label: "캘린더" },
      { href: "/community", label: "커뮤니티" },
    ],
  },
  {
    title: "계정",
    links: [
      { href: "/login", label: "로그인" },
      { href: "/register", label: "회원가입" },
      { href: "/mypage", label: "마이페이지" },
    ],
  },
  {
    title: "운영",
    links: [
      { href: "/admin", label: "관리자" },
      { href: "/community/write", label: "글쓰기" },
    ],
  },
];

export function Footer() {
  return (
    <footer className="border-t bg-zinc-50/70">
      <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 md:grid-cols-[1.1fr_1.4fr]">
        <div className="space-y-4">
          <Link href="/" className="flex items-center gap-2 text-base font-semibold text-zinc-900">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <BriefcaseBusiness className="h-5 w-5" />
            </span>
            강사구인
          </Link>
          <p className="max-w-sm text-sm leading-6 text-muted-foreground">
            강사 구인 정보를 수집하고, 북마크와 일정 관리까지 이어지는 교육 일자리 탐색 서비스입니다.
          </p>
          <div className="flex gap-2">
            <Link
              href="/community"
              className="flex h-9 w-9 items-center justify-center rounded-md border bg-white text-muted-foreground transition-colors hover:text-blue-600"
              aria-label="커뮤니티"
            >
              <MessageSquare className="h-4 w-4" />
            </Link>
            <a
              href="mailto:contact@example.com"
              className="flex h-9 w-9 items-center justify-center rounded-md border bg-white text-muted-foreground transition-colors hover:text-blue-600"
              aria-label="이메일 문의"
            >
              <Mail className="h-4 w-4" />
            </a>
            <Link
              href="/jobs"
              className="flex h-9 w-9 items-center justify-center rounded-md border bg-white text-muted-foreground transition-colors hover:text-blue-600"
              aria-label="최신 공고"
            >
              <Rss className="h-4 w-4" />
            </Link>
          </div>
        </div>

        <div className="grid gap-6 sm:grid-cols-3">
          {footerGroups.map((group) => (
            <div key={group.title} className="space-y-3 text-sm">
              <h2 className="font-semibold text-zinc-900">{group.title}</h2>
              <div className="grid gap-2">
                {group.links.map((link) => (
                  <Link key={link.href} href={link.href} className="text-muted-foreground transition-colors hover:text-foreground">
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t bg-white/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-5 text-xs text-muted-foreground md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} 강사구인. All rights reserved.</p>
          <p>Firebase + Next.js 기반 정보 수집 MVP</p>
        </div>
      </div>
    </footer>
  );
}
