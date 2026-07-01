# Crawling Rules & Daily Operations (v2)

## Goal
매일 06:00, 18:00에 국내 관공서, 지자체, 공공기관, 준공공기관, 교육청, 학교, 대학교, 도서관, 평생학습관, 청년센터, 복지관 등에서 게시하는 강사/멘토/코치/튜터/특강/교육용역 모집 공고를 수집한다.

---

## 1. Source Priority

| Priority | Source | Method | Status | Notes |
|----------|--------|--------|--------|-------|
| 1 | Worknet | OpenAPI (lod.work.go.kr) | TODO | 인증키 기반, 채용정보 API |
| 1 | 공공기관 채용정보 (Job-Alio) | 공공데이터 API (data.go.kr) | TODO | 접수기간, 직무, 첨부파일 메타 |
| 1 | 나라일터 (gojobs.go.kr) | 공식 게시판 크롤링 | ✅ DONE | 21키워드 x 3p, 기관유형 자동분류 |
| 1 | 시도교육청 (6곳) | 공식 게시판 크롤링 | ✅ DONE | 서울/경기/인천/부산/대구/제주. 대구는 사이트 점검 시 자동 건너뜀. 나머지 11곳 TODO |
| 1 | 잡알리오 (data.go.kr API) | 공공데이터 API | ✅ DONE | 진행중 공공기관 공고 전수 조회(ongoingYn=Y) 후 로컬 키워드 필터. 401 시 HTML 크롤링 폴백. DATA_GO_KR_API_KEY 필요 |
| 1 | 청소년활동진흥원 (kywa.or.kr) | HTML 크롤링 | ✅ DONE | 청소년수련관/센터 채용 집약. 3p |
| 1 | SW미래채움 (sweduhub.or.kr) | JSON API | ✅ DONE | 13개 지역센터 SW·AI 강사 공고 통합. 제목 '강사' 서버검색. robots 전체 허용 |
| 1 | 디지털배움터 (NIA) | JSON API | ✅ DONE | 전국 디지털역량교육 강사/튜터 모집 통합공고. x-nia-header/token 빈 헤더 필수 |
| 1 | 시청자미디어재단 (kcmf.or.kr) | HTML 크롤링 | ✅ DONE | 미디어교육 강사(체험·보조·일반) 모집. 매년 1~3월 집중 |
| 1 | 제주평생교육장학진흥원 (jiles.or.kr) | HTML 크롤링 | ✅ DONE | 매월 도민 강사 모집 + 평생교육 강사. 제목검색 qtype=title |
| 1 | 제주콘텐츠진흥원 (ofjeju.kr) | HTML 크롤링 | ✅ DONE | 웹툰·미디어 강사풀 (연 1~3건). 공지 게시판 qType=title |
| — | 제주테크노파크 (jejutp.or.kr) | — | ❌ 제외 | robots.txt Disallow: / (전체 금지) — robots 준수 원칙에 따라 크롤링 안 함 |
| 2 | 나라장터 | OpenAPI (data.go.kr) | TODO | 교육용역/위탁교육/멘토링 사업 |
| 2 | 네이버 웹검색 | HTML 크롤링 | ✅ DONE | 21키워드 (영상/미디어 4개 포함). 준관공서 공고 탐색 보조. API 전환 권장 |
| 3 | Saramin | HTML 크롤링 | OK | 16키워드 (영상/미디어 5개). 보조 소스 |
| 3 | JobKorea | HTML 크롤링 | OK | 15키워드 (영상/미디어 5개). 보조 소스 |
| 3 | Worknet (HTML) | HTML 크롤링 | OK | 9키워드 (영상/미디어 2개). API 전환 전 임시 |

### Principle
- 공식 API > 공식 게시판 > 검색엔진 순서
- 검색 결과는 공식 원문 URL 발견용으로만 사용
- JS 렌더링이 꼭 필요한 사이트만 Playwright 사용
- robots.txt, 이용약관, 요청 제한 준수

---

## 2. Keywords

### Include
```
강사, 강사모집, 강사채용, 외부강사, 시간강사, 특강, 교육강사, 위촉강사,
멘토, 멘토링, 코치, 코칭, 튜터, 지도사, 교관, 연수강사,
방과후강사, 늘봄강사, 디지털튜터, 기초학력 튜터, 학습지원 튜터,
계약제교원, 기간제교원, 자유학기, 예술강사, 스포츠강사,
창업강사, 기업가정신, 창업멘토, 진로강사, 취업특강,
리더십, 동기부여, 멘탈코칭,
영상강사, 미디어강사, 콘텐츠강사, 유튜브강사, 크리에이터강사
```

### Exclude
```
정규직, 일반직, 행정직, 시설관리, 조리실무사, 미화, 경비, 운전,
공무원 전입, 임원 후보자, 원장 후보자, 교장, 교감, 전임교원,
채용 최종합격자, 서류전형 합격자, 면접결과, 합격자 발표
```

---

## 3. Data Fields

```json
{
  "id": "string",
  "title": "string",
  "organization": "string",
  "orgType": "government | quasi_gov | school | university | public_institution | corporate | procurement",
  "orgSubType": "string",
  "region": "string",
  "regionDetail": "string",
  "sourceName": "string",
  "sourceUrl": "string",
  "originalUrl": "string",
  "postedAt": "timestamp",
  "deadlineAt": "timestamp | null",
  "deadlineText": "string",
  "deadlineStatus": "known | unknown | rolling | closed",
  "category": "string",
  "applyMethod": "string",
  "contact": "string",
  "attachments": [{"fileName": "", "fileUrl": "", "fileType": ""}],
  "description": "string",
  "status": "active | closing_soon | closed | unknown",
  "firstSeenAt": "timestamp",
  "lastSeenAt": "timestamp",
  "contentHash": "string",
  "dedupeKey": "string"
}
```

---

## 4. Deadline Handling

**deadlineText가 없다는 이유만으로 삭제하지 않는다.**

```
1차: 목록 페이지에서 마감일 추출
2차: 상세 본문에서 접수기간/마감일 추출
3차: 첨부파일(HWP/PDF)에서 접수기간 추출
4차: 추출 실패 시 deadlineStatus = "unknown"으로 저장
5차: postedAt 기준 14~30일이 지난 unknown 공고만 inactive 처리
```

### Status Rules
- `deadlineAt >= today` → active
- `deadlineAt < today + 3days` → closing_soon
- `deadlineAt < today` → closed
- 원문에서 "모집종료/마감/채용완료/삭제" 확인 → closed
- deadline 없고 postedAt > 30일 전 → closed

---

## 5. Category Classification

| Category | Keywords |
|----------|----------|
| IT/Programming | IT, AI, coding, SW, data, cloud, digital |
| Language | English, TOEIC, Japanese, Chinese |
| Business/Marketing | marketing, branding, sales, trade |
| Startup/Career | startup, entrepreneurship, resume, career |
| Self-Development | leadership, mental, motivation, mindset |
| Finance/Accounting | accounting, tax, investment |
| Law/Admin | labor law, HR, contract, policy |
| Education/Teaching | pedagogy, facilitation, coaching, mentoring |
| Culture/Art | art, music, design, craft |
| Health/Welfare | exercise, yoga, sports, psychology |
| Environment/ESG | ESG, carbon, energy, climate |
| Other | (no match) |

---

## 6. Org Type Classification

| Type | Examples |
|------|----------|
| government | 시청, 구청, 교육청, 교육부, 도청 |
| quasi_gov | 센터, 재단, 진흥원, 도서관, 복지관 |
| school | 초등학교, 중학교, 고등학교, 교육지원청 |
| university | 대학교, 대학 |
| public_institution | 공단, 공사, 연구원 |
| procurement | 나라장터 용역 |
| corporate | (default) |

---

## 7. Dedup Strategy

1. canonical `sourceUrl` 기준
2. `originalUrl` 기준
3. `title + organization + deadlineAt` 기준
4. `title + organization + postedAt` 기준

---

## 8. Rate Limiting

| Source | Strategy |
|--------|----------|
| Public APIs | rate limit per API spec |
| Naver Search API | 25,000 calls/day limit |
| Saramin/JobKorea | No delay needed |
| Worknet HTML | 1s delay between pages |
| Gov bulletin boards | 2s delay between requests |

---

## 9. Status Update (Daily Re-check)

이미 저장된 공고는 매일 재확인한다.
- 원문에서 "모집종료/마감/채용완료/삭제" → `status = closed`
- 마감일 3일 이내 → `closing_soon`
- 마감일 경과 → `closed`

---

## 10. Operations

- Cloud Scheduler 또는 cron: 매일 06:00, 18:00
- source별 성공/실패/수집건수/신규건수/중복건수 로그 저장
- 실패 source: 3회 재시도 후 crawl_runs에 에러 기록
- API rate limit 준수
- 게시판 크롤링: source별 delay + backoff

---

## 11. Implementation Status

### Phase 1 (Current MVP)
- [x] Saramin HTML crawler (16 keywords, 영상/미디어 5개 포함)
- [x] JobKorea HTML crawler (15 keywords, 영상/미디어 5개 포함)
- [x] Worknet HTML crawler (9 keywords x 2 pages, 영상/미디어 2개 포함)
- [x] Naver web search (21 keywords, 영상/미디어 4개 포함, 2s delay)
- [x] Quality filter (old year removal + deadline required)
- [x] Auto category classification (12 categories, school subjects included)
- [x] Org type reclassification (school/government/quasi_gov 분리)
- [x] JSON export to src/data + public/data
- [x] 크롤링 스킬 문서화 (crawl-instructor-jobs skill)
- [x] 리포트 스크립트 (crawl_report.py)

### Phase 2 (API Migration)
- [ ] Worknet OpenAPI integration
- [x] 공공기관 채용정보 API (data.go.kr) — 전수조회+로컬필터, 401 시 HTML 폴백
- [ ] 나라장터 입찰공고 API (data.go.kr)
- [ ] Naver Search API migration
- [x] 나라일터 게시판 크롤러 (18 keywords x 3 pages)
- [ ] Deadline extraction from detail pages
- [ ] HWP/PDF attachment parsing

### Phase 3 (Education/School)
- [x] 5개 시도교육청 게시판 크롤러 (서울SEN/경기GOE/인천ICE/부산PEN/대구DGE)
- [ ] 나머지 12개 교육청 (광주/대전/세종/울산/강원/충북/충남/전북/전남/경북/경남/제주)
- [x] 학교 키워드 확대 (방과후, 기간제교원, 예술강사, 늘봄, 스포츠강사, 진로, 튜터, 교관, 코치 등)
- [x] Exclude keyword filter (합격자, 교장, 시설관리 등)

### Phase 4 (Quasi-Gov Direct)
- [x] AI·디지털 교육 특화 소스 (sources/ai_edu.py): SW미래채움·디지털배움터·시청자미디어재단·제주평생교육장학진흥원·제주콘텐츠진흥원
- [ ] 주요 청년센터 게시판 크롤러
- [ ] 평생학습관/도서관 게시판 크롤러
- [ ] 복지관/문화센터 게시판 크롤러

---

## 12. Manual Commands

```bash
# Full export (all sources -> JSON)
python3 crawlers/export_json.py

# Test individual source
python3 crawlers/sources/saramin.py
python3 crawlers/sources/jobkorea.py
python3 crawlers/sources/worknet.py
python3 crawlers/sources/public_gov.py

# Dev server (port 3003)
npm run dev
```

---

## 13. API Keys Needed

| API | Where to get | Key env var |
|-----|-------------|-------------|
| Worknet OpenAPI | lod.work.go.kr | WORKNET_API_KEY |
| 공공데이터포털 | data.go.kr | DATA_GO_KR_API_KEY |
| Naver Search API | developers.naver.com | NAVER_CLIENT_ID, NAVER_CLIENT_SECRET |
