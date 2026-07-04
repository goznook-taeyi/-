# CLAUDE.md

## 프로젝트 구성

이 저장소에는 두 가지가 있다.

1. **YouTube Shorts Downloader** (`extension/`, `server/`) — 크롬 확장 + yt-dlp 로컬 서버. 자세한 사용법은 README.md 참조.
2. **교육 콘텐츠 제작 환경** — 숏폼 교육 PPT 제작에 최적화된 스킬 세트.

## 교육 PPT 제작

숏폼 교육 PPT(9:16) 또는 강의 슬라이드(16:9) 제작 요청을 받으면 **`shortform-edu-ppt` 스킬을 사용한다**
(`.claude/skills/shortform-edu-ppt/SKILL.md`). 이 스킬이 기획(학습과학) → 디자인(레퍼런스 규격) → .pptx 생성 → 검증의 전체 워크플로우를 정의한다.

- 디자인 규격: `.claude/skills/shortform-edu-ppt/references/design-reference.md` (사용자 레퍼런스 분석 — 바이올렛 액센트, 라운드 카드, 걸침 이모지, 라벤더 그라데이션)
- PPT 빌더: `.claude/skills/shortform-edu-ppt/scripts/build_pptx.py` (python-pptx 필요)

### 교육학 스킬
- `.claude/skills/`에 활성화된 17개 스킬: 인지부하 분석, 이중부호화, 인출연습, 훅 오프닝, 풀이예제, 점검질문 설계 등 — 내용 기획 시 참조
- 전체 라이브러리(165개, 20개 도메인): `education-skills-library/skills/<도메인>/<스킬>/SKILL.md` — 활성 스킬로 부족할 때 직접 읽기 (출처·라이선스는 `education-skills-library/NOTICE.md`)
