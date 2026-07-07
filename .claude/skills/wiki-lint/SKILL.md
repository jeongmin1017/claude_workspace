---
name: wiki-lint
description: |
  00-wiki 토픽 페이지 헬스체크. 모순, 고아 페이지, 오래된 정보, 누락된 교차 참조 점검.
  "wiki-lint", "위키 점검", "위키 헬스체크", "wiki health", "토픽 점검" 등을 언급하면 자동 실행.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
  - Edit
  - AskUserQuestion
---

# Wiki Lint

`30-knowledge/00-wiki/` 토픽 페이지의 헬스체크를 수행합니다.

## 동작 방식

### Step 1: 전체 토픽 페이지 수집

```
WIKI_PATH = /Users/jeongminkim/Library/Mobile Documents/com~apple~CloudDocs/jeongmin-workspace/30-knowledge/00-wiki
```

- Glob: `$WIKI_PATH/*.md` (SCHEMA.md, README.md, index.md, log.md 제외)
- 각 파일의 제목, Related 섹션, Last enriched 날짜 수집

### Step 2: 점검 실행 (A~M)

#### A. 고아 페이지 (Orphan Pages)
- index.md에 등재되지 않은 토픽 페이지
- 다른 토픽의 Related에서 한 번도 참조되지 않는 페이지
- **조치**: index.md에 추가 제안

#### B. 죽은 링크 (Dead Links)
- Related 섹션에서 참조하는 `[[토픽]]`이 실제 파일로 존재하지 않는 경우
- **조치**: 링크 제거 또는 새 토픽 생성 제안

#### C. 오래된 페이지 (Stale Pages)
- Last enriched가 90일 이상 경과한 페이지
- **조치**: "이 토픽은 여전히 유효한가?" 플래그

#### D. 모순 탐지 (Contradictions)
- 서로 다른 토픽 페이지에서 동일 주제에 대해 상충하는 주장
- Grep으로 공통 키워드를 가진 페이지 쌍을 찾고, 내용 비교
- **조치**: `[!contradiction]` 플래그 + 어느 쪽이 최신인지 표시

#### E. 누락된 교차 참조 (Missing Cross-References)
- 내용에서 다른 토픽명이 언급되지만 Related에 링크가 없는 경우
- 모든 토픽명으로 각 페이지를 Grep → Related에 없으면 누락
- **조치**: Related에 추가 제안

#### F. 누락된 토픽 (Missing Pages)
- 여러 페이지의 Related나 본문에서 참조되지만, 전용 페이지가 없는 개념
- **조치**: 새 토픽 페이지 생성 제안

#### G. 비대한 페이지 (Oversized Pages)
- 특정 섹션이 전체 페이지의 50% 이상을 차지하거나, 하위 항목이 10개 이상인 경우
- **조치**: 해당 섹션을 독립 토픽 페이지로 분리 제안. 원래 페이지에는 요약 + `[[분리된-토픽]]` 링크 유지

#### H. 데이터 갭 (Data Gaps)
- 토픽 페이지의 핵심/근거 섹션에서 주장이 있지만 source 인용이 없는 경우
- 다른 토픽에서 반복 언급되지만 자체 근거가 부족한 개념
- **조치**: 웹 검색으로 보강할 수 있는 갭 식별 → 리서치 제안

#### I. 활동 분석 (log.md 기반)
- log.md를 읽어서 ingest 빈도 분석
- 한 번도 enriched 되지 않은 시드 페이지 (stale seed)
- 최근 30일간 ingest가 없는 카테고리
- **조치**: "이 카테고리에 새 소스를 ingest할 필요가 있는가?" 제안

#### J. Infobox 누락/훼손
- H1 바로 아래(YAML/기존 인용문구 블록 뒤)에 `> **관련**:` 줄이 없는 페이지
- 관련 링크 개수 6개 초과 (덤프)
- Infobox wikilink가 실제 파일로 존재하지 않음 (dead link — B와 중복 검사)
- **조치**: 누락 시 바닥 `## Related` 또는 본문 wikilink에서 상위 6개 추출 제안. 6개 초과 시 indegree 약한 것 제거 제안

#### K. index 한 줄 설명 품질
- 키워드 콤마 덤프 탐지: `,`가 3개 이상이거나 토큰 8개 이상이면 의심
- 70자 초과
- 문장이 아닌 명사구/파편
- **조치**: 해당 페이지 `## 핵심` 첫 문장 기반으로 한 문장 재작성 제안. 키워드는 해당 페이지 Facets로 이동

#### L. Facets 비대/중복
- Infobox Facets 줄 70자 초과
- Facets 키워드 중 현재 `## 근거` 섹션에서 더 이상 언급되지 않는 것 (obsolete keyword)
- **조치**: 오래된/약한 키워드 제거 제안

#### M. 허브 블록 표류
- index.md 상단 `> **허브 토픽**` 5개가 실제 indegree 상위 5개와 불일치
- indegree = 각 페이지 Infobox 관련 줄에 자기 토픽이 몇 번 등장하는지 집계
- **조치**: 상위 5개로 재정렬 제안

### Step 3: 헬스 리포트

```markdown
# Wiki Health Report — YYYY-MM-DD

## 요약
- 총 토픽: N개
- 건강: X개 | 주의: Y개 | 조치 필요: Z개

## 상세

### 고아 페이지 (N개)
| 페이지 | 상태 | 제안 |
|--------|------|------|

### 죽은 링크 (N개)
...

### 오래된 페이지 (N개)
...

### 모순 (N개)
...

### 누락된 교차 참조 (N개)
...

### 누락된 토픽 (N개)
...
```

### Step 4: 사용자 승인 후 수정

- AskUserQuestion으로 어떤 항목을 수정할지 확인
- 승인된 항목만 Edit (index.md 업데이트, Related 추가 등)
- 수정 내용을 log.md에 기록:
  ```
  ## [YYYY-MM-DD] lint | Wiki Health Check
  - 고아 페이지 N개 → index.md에 추가
  - 누락된 교차 참조 N개 → Related에 추가
  ```

## 핵심 원칙

- **리포트 먼저, 수정은 승인 후**: 자동으로 고치지 않음
- **모순은 플래그만**: 어느 쪽이 맞는지는 사용자가 판단
- **과잉 제안 금지**: 확실한 문제만 리포트
