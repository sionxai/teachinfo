"""강사 구인 공고 데이터 모델"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import hashlib
import json


# 강사 분야 분류
CATEGORIES = {
    "IT·프로그래밍": ["IT", "프로그래밍", "코딩", "소프트웨어", "AI", "인공지능", "빅데이터", "데이터", "웹", "앱", "디지털", "컴퓨터", "정보", "SW", "ICT", "블록체인", "클라우드", "보안", "네트워크"],
    "어학": ["영어", "일본어", "중국어", "한국어", "외국어", "TOEIC", "IELTS", "토익", "회화", "통번역", "언어"],
    "경영·마케팅": ["경영", "마케팅", "브랜딩", "SNS", "홍보", "광고", "기획", "전략", "세일즈", "영업", "무역", "유통", "물류"],
    "창업·취업": ["창업", "스타트업", "취업", "면접", "이력서", "자소서", "진로", "직업", "커리어", "비즈니스모델", "사업계획", "기업가정신", "기업가", "앙트러프러너", "예비창업", "창업교육"],
    "자기계발": ["자기계발", "리더십", "소통", "커뮤니케이션", "발표", "스피치", "프레젠테이션", "시간관리", "동기부여", "멘탈", "마인드", "멘탈코칭", "셀프리더십", "회복탄력성", "마인드셋", "성장마인드"],
    "재무·회계": ["재무", "회계", "세무", "세금", "재테크", "투자", "금융", "보험", "부동산", "자산"],
    "법률·행정": ["법률", "행정", "노동법", "근로", "인사", "총무", "계약", "규정", "정책"],
    "교육·강의기법": ["교수법", "강의기법", "교육", "학습", "퍼실리테이션", "코칭", "멘토링", "상담", "방과후", "기간제교원", "계약제교원", "늘봄", "시간강사", "튜터", "교관", "코치", "멘토", "수학", "과학", "국어"],
    "문화·예술": ["문화", "예술", "미술", "음악", "사진", "영상", "디자인", "공예", "서예", "도예", "예술강사"],
    "건강·복지": ["건강", "운동", "요가", "필라테스", "체육", "스포츠", "심리", "복지", "간호", "의료", "식품", "영양", "안전", "스포츠강사"],
    "환경·ESG": ["환경", "ESG", "탄소", "에너지", "친환경", "지속가능", "기후"],
    "기타": [],
}


def classify_category(title: str, description: str = "") -> str:
    """제목과 내용에서 강의 분야를 자동 분류"""
    text = f"{title} {description}".lower()
    scores: dict[str, int] = {}
    for cat, keywords in CATEGORIES.items():
        if cat == "기타":
            continue
        score = sum(1 for kw in keywords if kw.lower() in text)
        if score > 0:
            scores[cat] = score
    if scores:
        return max(scores, key=scores.get)  # type: ignore
    return "기타"


@dataclass
class JobPosting:
    title: str
    organization: str
    org_type: str  # government, quasi_gov, university, corporate, other
    org_sub_type: str = ""  # 청년센터, 창업지원센터 등
    category: str = ""  # 자동 분류됨
    region: str = ""
    region_detail: str = ""
    description: str = ""
    requirements: str = ""
    pay: str = ""
    deadline_text: str = ""
    deadline_type: str = "unknown"  # fixed, until_filled, until_budget, unknown
    apply_url: str = ""
    apply_method: str = ""
    contact_info: str = ""
    source_url: str = ""
    source_name: str = ""
    external_post_id: str = ""
    published_at: Optional[str] = None
    attachments: list = field(default_factory=list)

    def __post_init__(self):
        if not self.category:
            self.category = classify_category(self.title, self.description)

    @property
    def content_hash(self) -> str:
        content = f"{self.title}|{self.organization}|{self.description}"
        return hashlib.md5(content.encode()).hexdigest()

    @property
    def dedupe_key(self) -> str:
        return f"{self.title}|{self.organization}|{self.deadline_text}"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "organization": self.organization,
            "orgType": self.org_type,
            "orgSubType": self.org_sub_type,
            "category": self.category,
            "region": self.region,
            "regionDetail": self.region_detail,
            "description": self.description,
            "requirements": self.requirements,
            "pay": self.pay,
            "deadlineText": self.deadline_text,
            "deadlineType": self.deadline_type,
            "applyUrl": self.apply_url,
            "applyMethod": self.apply_method,
            "contactInfo": self.contact_info,
            "sourceUrl": self.source_url,
            "sourceName": self.source_name,
            "externalPostId": self.external_post_id,
            "contentHash": self.content_hash,
            "dedupeKey": self.dedupe_key,
            "publishedAt": self.published_at,
            "attachments": self.attachments,
            "status": "active",
            "viewCount": 0,
            "bookmarkCount": 0,
        }

    def summary(self) -> str:
        return f"[{self.category}] {self.title} | {self.organization} | {self.region} | 마감: {self.deadline_text or '미정'}"
