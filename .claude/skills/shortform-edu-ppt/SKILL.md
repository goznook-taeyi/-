---
name: shortform-edu-ppt
description: "숏폼(9:16) 교육 PPT를 학습과학 원칙에 따라 기획하고 .pptx 파일로 생성한다. 교육용 프레젠테이션, 숏폼 강의 슬라이드, 카드뉴스형 교육 콘텐츠 제작 요청 시 사용. Use when the user asks to create educational presentations, short-form lecture slides, or teaching PPT files."
user-invocable: true
---

# 숏폼 교육 PPT 제작 오케스트레이터

숏폼 교육 콘텐츠(유튜브 숏츠/릴스용 세로형 슬라이드, 또는 일반 16:9 강의 PPT)를
**학습과학 근거 기반으로 기획 → 디자인 규격에 맞춰 .pptx 생성 → 검증**까지 수행한다.

## 워크플로우

### 1단계 — 기획 (내용 설계)
아래 활성 스킬을 순서대로 참조해 내용을 설계한다. 각 스킬은 `.claude/skills/<이름>/SKILL.md`에 있다.

1. **학습목표 확정**: 주제·대상(연령/사전지식)·완료 후 할 수 있는 것 1가지를 확정
   → `learning-target-authoring-guide`
2. **개념 청킹**: 핵심 개념을 3±1개로 쪼개고, 슬라이드당 1개념 원칙 적용. 개념이 4개를 넘으면 영상을 나눈다
   → `cognitive-load-analyser` (외재적 부하 제거 체크)
3. **훅 설계**: 첫 슬라이드는 3초 안에 시선을 잡는 질문/오개념/반전으로 연다
   → `lesson-opening-designer`, 오개념 활용 시 `erroneous-example-designer`
4. **본문 시퀀스**: 풀이예제(worked example) → 이해 점검 질문 → 요약 순서
   → `digital-worked-example-sequence`, `hinge-question-designer`
5. **마무리 인출연습**: 마지막 슬라이드에 "화면 멈추고 떠올려보기" 형태의 인출 과제 1개
   → `retrieval-practice-generator`
6. (시리즈 기획 시) 편 간 간격·복습 배치 → `spaced-practice-scheduler`, `learning-progression-builder`

심화가 필요하면 전체 라이브러리 `education-skills-library/skills/<도메인>/<스킬>/SKILL.md` (165개, 20개 도메인)를 직접 읽는다.

### 2단계 — 디자인
`references/design-reference.md`의 규격을 따른다 (사용자 레퍼런스 분석 문서). 요약:
- 바이올렛(#7C3AED) 단일 액센트 + 라벤더 틴트 + 웜그레이 캔버스(#F5F4F7)
- 큰 라운드(반경 ~10%) 카드, 상단 변에 걸치는 배지, 모서리에 걸치는 대형 이모지
- 그라데이션 면은 슬라이드당 1개(표지/퀴즈 배경), 슬라이드당 텍스트 블록 5개 이하
- 이모지는 정보(감정/상태 요약)로만, 슬라이드당 1~3개 크게

### 3단계 — 생성
1. `pip show python-pptx` 확인, 없으면 `pip install python-pptx`
2. 덱 스펙 JSON 작성 (스키마는 `scripts/build_pptx.py` docstring 참조).
   슬라이드 타입: `cover`(그라데이션 표지) / `concept`(단일 카드) / `cards`(2~3카드) /
   `quiz`(점검 질문) / `summary`(primary 밴드 결론 + 인출연습)
3. `python scripts/build_pptx.py deck.json out.pptx` 실행
   - **비율은 최종 사용처로 결정한다.** 기본은 `"16:9"`(PPT/발표 표준).
     유튜브 숏츠·릴스·틱톡처럼 **세로 화면 영상**이 최종물일 때만 `"9:16"`.
     애매하면 사용자에게 "발표 슬라이드(16:9)인가요, 세로 영상(9:16)인가요?"를 먼저 확인한다.

### 4단계 — 검증
python-pptx로 재로드해 슬라이드 수·텍스트 존재를 확인하고, 결과 파일을 사용자에게 전달한다:
```python
from pptx import Presentation
p = Presentation("out.pptx")
print(len(p.slides))
```
가능하면 LibreOffice(`soffice --convert-to png`)로 렌더링해 시각 확인한다 (미설치면 생략).

## 비율(aspect) 규칙
- **16:9 (기본)**: 발표·강의·수업 슬라이드. PowerPoint/Keynote 표준. 별도 언급 없으면 이걸로.
- **9:16 (세로)**: 최종물이 유튜브 숏츠/릴스/틱톡 **세로 영상**일 때만. 폰 화면에 꽉 참.
- 어느 쪽이든 아래 숏폼 특화 규칙(장수·큰 타이포·정지화면 독립성)은 동일하게 적용한다.

## 숏폼 특화 규칙
- 5~8장 (표지 1 + 훅/개념 3~5 + 퀴즈 1 + 결론 1)
- 시청자가 1~3초 안에 읽어야 하므로: 제목 27pt+, 본문 12pt+, 한 카드 3줄 이하
- 각 슬라이드는 정지 화면으로도 독립적으로 이해 가능해야 함 (영상 편집 시 순서가 바뀔 수 있음)
- 답을 바로 보여주지 말 것: quiz 다음 슬라이드에서 공개 (인출연습 효과)
