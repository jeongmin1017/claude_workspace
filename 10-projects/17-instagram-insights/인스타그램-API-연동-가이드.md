# 인스타그램 API 연동 가이드

> 프로페셔널 인스타그램 계정의 **인사이트(도달·팔로워·게시물 성과)**를 API로 자동 수집하기 위한 처음-끝 가이드.
> 방식: **Instagram API with Instagram Login** (2024년 신설). **페이스북 페이지 불필요**, 본인 계정만 보면 **앱 심사 불필요**.
> 이 가이드는 이 프로젝트(`17-instagram-insights`)의 실제 스크립트 동작을 그대로 반영한다.

---

## 0. 시작 전 체크리스트

| 조건 | 내용 |
|------|------|
| 계정 유형 | 대상 인스타 계정이 **프로페셔널(비즈니스 또는 크리에이터)** 이어야 인사이트가 나온다. 개인 계정은 인사이트 API 불가. |
| Meta 개발자 계정 | https://developers.facebook.com 에서 개발자 등록(무료, 1회) |
| Python 환경 | Python 3.10+ (이 프로젝트는 `.venv` + `requests`, `python-dotenv` 사용) |
| 토큰 관리 | 토큰은 **비밀번호급**. 채팅·커밋·로그에 절대 노출 금지, `.env`로만 다룬다. |

> **개인 계정 → 프로페셔널 전환**: 인스타 앱 `설정 > 계정 유형 및 도구 > 프로페셔널 계정으로 전환`.

---

## 1. 두 가지 API 방식 (왜 Instagram Login인가)

| 방식 | 페이스북 페이지 | 앱 심사 | 조회 범위 | 이 프로젝트 |
|------|:---:|:---:|------|:---:|
| **Instagram API with Instagram Login** | ❌ 불필요 | ❌ 불필요(본인/테스터 한정) | 본인 계정 인사이트·게시물 | ✅ **채택** |
| Instagram API with Facebook Login (기존 Graph API) | ✅ 필수 | 대체로 필요 | 해시태그 검색·일부 집계 지표 추가 | 미사용 |

- **본인 계정 인사이트 수집**이 목적이면 Instagram Login으로 **충분**하다.
- 대시보드가 "인사이트는 Facebook Login으로 전환하라"고 안내해도, **본인 계정 insights는 Instagram Login으로도 가능**하다 (권한 `instagram_business_basic` + `instagram_business_manage_insights`). 해시태그 검색·`total_likes` 등 상세 집계만 Facebook Login 전용이다.

---

## 2. Meta 앱 만들기 (브라우저에서 직접 — 1회)

> Meta 로그인·권한 동의는 **본인 계정 인증**이라 사람이 직접 해야 한다. Claude가 대신 못 한다.

1. https://developers.facebook.com 로그인 → 개발자 등록
2. **내 앱 → 앱 만들기 → 유형 "비즈니스"** 선택 → 앱 이름 입력
3. (이용 사례를 묻는 경우) **"Instagram에서 메시지 및 콘텐츠 관리"** 선택
4. 비즈니스 포트폴리오: **연결 안 함**으로 진행 가능
5. 앱 대시보드 → **제품 추가 → Instagram → 설정**
   → **"Instagram API with Instagram Login"** 방식 선택
6. 왼쪽 메뉴 **Instagram → API 설정(Instagram 비즈니스 로그인)** 진입

> ⚠️ **앱 ID·URL 추측 금지**: 설정 페이지 URL에 들어가는 앱 ID 등은 **브라우저 주소창에서 직접 확인**한다. 추측으로 URL을 만들면 엉뚱한 페이지로 간다. (실제 겪은 사건)

---

## 3. 계정을 앱 테스터로 등록 (본인 계정 조회 시 필수)

개발 모드에서 본인 계정을 조회하려면 그 계정이 **앱의 Instagram 테스터**로 등록돼 있어야 한다.

1. 앱 대시보드 → **앱 역할(Roles) → Instagram 테스터**에 대상 계정(예: `@thinking.archive`) 추가
2. 인스타그램 앱에서 수락:
   **설정 → 앱 및 웹사이트 → 테스터 초대 → 수락**

> 이 단계를 건너뛰면 토큰 생성/`계정 추가` 시 **"개발자 역할 권한 부족"** 에러가 난다.

---

## 4. 액세스 토큰 발급 (60일 장기 토큰)

1. **Instagram → API 설정** 화면에서 **토큰 생성** 클릭
2. 대상 계정으로 로그인 → **권한 동의**
   - 필요 권한: **`instagram_business_basic`**, **`instagram_business_manage_insights`**
3. 표시된 **60일 액세스 토큰** 문자열을 복사

이때 함께 확인 가능한 식별값 (화면에서 직접 확인, 추측 금지):
- **Instagram 앱 ID**
- **IG User ID** (인사이트 대상 계정의 숫자 ID)
- **60일 장기 토큰**

---

## 5. 환경 설정 (.env)

```bash
cd "10-projects/17-instagram-insights"

# 가상환경이 없다면 1회만
python3 -m venv .venv
.venv/bin/pip install requests python-dotenv

# 환경변수 템플릿 복사
cp .env.example .env
```

`.env` 를 열어 토큰을 붙여넣는다:

```bash
# 본인 계정 (기본)
IG_ACCESS_TOKEN=발급받은_60일_토큰

# (선택) 멀티계정 — 7항 참고
# IG_ACCESS_TOKEN_HAEUN=상대방이_공유한_토큰

# (선택) 앱 대시보드 > 앱 설정 > 기본 설정 에서 확인
IG_APP_ID=
IG_APP_SECRET=

# Graph API 버전 (기본값 권장)
IG_API_VERSION=v23.0
```

> ⚠️ `.env` 는 `.gitignore` 처리되어 있다. 토큰은 커밋·채팅에 노출하지 않는다.

---

## 6. 조회 실행

```bash
# 계정 인사이트 + 최근 게시물 10개 (기본)
.venv/bin/python fetch_insights.py

# 최근 게시물 25개
.venv/bin/python fetch_insights.py --media 25

# 다른 사람 계정 (멀티계정, 7항 참고)
.venv/bin/python fetch_insights.py --account haeun --media 25
```

결과는 계정별로 `output/<라벨>/` 에 분리 저장된다 (본인 = `default`, 지인 = 소문자 이름):

| 파일 | 내용 |
|------|------|
| `YYYYMMDD-HHMM-요약.md` | 사람이 읽는 요약 (계정 지표 + 게시물 표 + 참여율·저장률 + 🏆 베스트 콘텐츠 순위) |
| `YYYYMMDD-HHMM-media.csv` | 게시물별 성과 (엑셀/시트용, `engagement_rate`·`save_rate` 포함) |
| `YYYYMMDD-HHMM-insights-raw.json` | API 원본 응답 |

### 성과 분석 리포트

```bash
.venv/bin/python analyze.py                          # 가장 최근 조회 결과 분석
.venv/bin/python analyze.py --keywords "투자,여행,일상"  # 키워드별 평균 성과까지
.venv/bin/python analyze.py --account haeun           # 지인 계정 분석
```

해당 계정의 최신 raw JSON을 읽어 **포맷별·월별 평균 성과 + 참여율 Top/Bottom 5 + (선택)키워드별 평균**을 `output/<라벨>/YYYYMMDD-HHMM-분석리포트.md` 로 저장한다. (먼저 `fetch_insights.py`를 그 계정으로 실행해야 함)

---

## 7. 다른 사람 계정 조회 (멀티계정)

본인 앱을 새로 만들 필요 없이, **상대방이 발급해 공유한 60일 토큰 문자열 하나**만 있으면 된다. 스크립트가 `me` 엔드포인트로 **토큰 소유자를 자동 조회**하므로 계정을 하드코딩하지 않는다.

### 세팅
1. 상대방이 **자기 Meta 앱에서 자기 계정 토큰을 생성**해 문자열만 공유
   - 권한: `instagram_business_basic`, `instagram_business_manage_insights` (4항과 동일)
   - 상대 계정은 **프로페셔널(비즈니스/크리에이터)** 이어야 인사이트가 나옴
2. 받은 토큰을 `.env` 에 **`IG_ACCESS_TOKEN_<이름>`** 형식으로 추가
   ```bash
   IG_ACCESS_TOKEN=본인토큰
   IG_ACCESS_TOKEN_HAEUN=하은님이_공유한_토큰
   ```
3. 실행 시 `--account <이름>` 으로 선택 (이름은 키의 `IG_ACCESS_TOKEN_` 뒤 부분, 대소문자 무관)

> **대안**: 정민님 앱에 상대를 **Instagram 테스터로 등록** → 상대가 인스타에서 초대 수락 → `계정 추가`로 토큰 발급. 이 경우 상대의 인스타 로그인·동의가 필요하다.

### ✅ 왜 사업체·앱 심사 없이 되나

7항은 **각 계정 주인이 "자기 앱에서 자기 계정 토큰"을 발급**하는 구조다. 모든 계정이 각자에게 **"소유/관리하는 계정"** 이라 **Standard Access**가 적용된다 → 비즈니스 인증·App Review·Live 모드 전부 불필요. 상대가 **본인 의사로 발급해 건넨 자기 데이터**이므로 ToS 문제도 없다.

- ✅ **7항으로 충분한 경우**: 소수의 지인·스터디, 비상업적, **상대가 직접 토큰을 발급해 줄 수 있는** 관계.
- ⚠️ **8항(Advanced Access)이 필요해지는 순간**: 클라이언트가 **"연결" 버튼 하나로** 온보딩되길 원할 때 / 상대가 **직접 앱 세팅을 못 하는** 비개발자일 때 / **상업적 대행 서비스**로 다수 계정을 자동 수집할 때.

> 전제(마찰 지점): "앱 새로 만들 필요 없다"는 **정민님 기준**이다. **토큰 주는 사람은** 자기 Meta 개발자 앱이 필요(또는 정민님 앱에 테스터 등록). 계정마다 수작업 발급 → 소수엔 OK, 수십 개엔 부적합.

### 🔒 공유 토큰의 조회 범위 (개인정보)

토큰 권한이 **2개뿐**(`basic` + `manage_insights`)이라 **볼 수 있는 것이 권한으로 원천 제한**된다. 코드가 막는 게 아니라 **Instagram API 자체가 막는다(scope 방어)**.

| 볼 수 있는 것 | 절대 못 보는 것 |
|------|------|
| 상대가 올린 **본인 게시물** 목록·캡션 (원래 공개) | ❌ **DM / 메시지** (별도 권한 `manage_messages` 필요) |
| 게시물 인사이트 (도달·좋아요·저장·공유 등) | ❌ 로그인 정보·비밀번호 |
| 프로필 기본정보 (팔로워 **수**, 게시물 수, 소개글) | ❌ **팔로워 개개인 명단·연락처** |
| 계정 단위 인사이트 (도달·프로필 조회 등) | ❌ 좋아요 목록·저장한 남의 게시물·열람 기록 |
| | ❌ 게시물 작성·삭제·수정 (또 다른 별도 권한 필요) |

**상대방 안전장치**: ① 토큰 생성 시 동의 화면에서 부여 권한 직접 확인 · ② `설정 > 앱 및 웹사이트`에서 언제든 연결 해제(즉시 무효) · ③ 60일 자동 만료. 필요가 끝나면 **재발급(=기존 토큰 폐기)** 권장.

---

## 8. 대행사·제3자 계정 수집 (Advanced Access)

> 앞의 1~7항은 **본인/테스터 계정**(각자 자기 토큰 발급) 기준이다. **내가 소유하지 않은 클라이언트 계정**을, 상대가 직접 토큰을 못 주는 상황에서 **내 앱이 대신 서비스**하려면 접근 등급이 달라진다.

### 핵심 분기: Standard vs Advanced Access

| 구분 | 대상 | 앱 심사 |
|------|------|:---:|
| **Standard Access** | 내가 **소유/관리**하고 앱에 **테스터로 추가한** 계정만 (= 7항까지) | ❌ 불필요 |
| **Advanced Access** | 내가 소유하지 않은 **제3자(클라이언트) 프로페셔널 계정** | ✅ **필수** |

> Meta 공식 기준: *"Advanced Access is required if your app serves Instagram professional accounts you **don't own or manage**."* 대행사는 무조건 여기에 해당한다.

### 대행사가 밟아야 할 4단계

1. **Meta 비즈니스 인증 (Business Verification) — 선행 필수**
   - Business Manager에서 사업자 실체 인증(사업자등록증 등).
   - ⚠️ **App Review보다 먼저** 통과해야 함. 순서를 바꾸는 게 가장 흔한 실수.

2. **앱 Live 모드 + 정책 페이지**
   - Development → **Live 모드** 전환.
   - **개인정보처리방침 URL** + **데이터 삭제 경로(data deletion)** 필수.

3. **App Review — 권한별 심사**
   - 인사이트 필요 권한: `instagram_business_basic` + `instagram_business_manage_insights` (최소 권한 원칙 — 불필요한 게시/DM 권한 붙이지 말 것).
   - 권한마다 **데모 영상** 제출: **실제 비즈니스/크리에이터 계정**(테스트 유저 불가)으로 OAuth 동의 전 과정 + 그 데이터가 **내 앱 화면에 렌더링**되는 것까지, 심사자가 **재현 가능**하게.
   - 기간: 인사이트류 대체로 1~7영업일. **첫 제출 반려 흔함**(수 회 반복 각오).

4. **클라이언트별 동의/자산접근 확보**
   - Advanced Access를 받아도 **계정 주인의 동의**는 여전히 필요.

### 두 연동 방식 비교 (대행사 관점)

| 항목 | A. Instagram Login | B. Facebook Login + 파트너 자산접근 |
|------|------|------|
| 페이스북 페이지 | ❌ 불필요 | ✅ 클라이언트 IG가 페이지 연결 필수 |
| 온보딩 | 클라이언트가 앱 OAuth 1회 로그인·동의 | 클라이언트가 Business Manager에서 파트너로 추가 → 자산(IG·페이지) 배정 |
| 다수 계정 관리 | 계정마다 토큰 관리 | **System User 토큰**으로 서버 간 중앙 관리 용이 |
| 해시태그·일부 집계 지표 | 불가 | 가능 |
| Business Verification + App Review | ✅ 필요 | ✅ 필요 |

> 클라이언트 수가 많고 서버에서 자동 수집하는 **전형적 대행사 시나리오**면 대체로 **B(파트너 자산접근 + System User)** 가 운영이 깔끔하다. 페이지 연결 없이 가볍게 가려면 A.

### 주의
- **메뉴 위치·최신 서류 요건은 정책 변경이 잦다.** 신청 직전 공식 문서로 재확인:
  - [Instagram API with Instagram Login (공식)](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/)
  - [Insights — Instagram Platform (공식)](https://developers.facebook.com/docs/instagram-platform/insights/)
- 지표명은 수시 변경(`impressions` 폐지 등) → 코드는 지표별 개별 시도 + 실패 스킵 구조 유지.

> **요약**: 본인 계정 = 테스터 등록 + 토큰 발급으로 끝. **대행사(클라이언트 계정) = 비즈니스 인증 → Live 모드+정책 → 권한별 App Review(Advanced Access) → 클라이언트별 동의/자산접근** 4단계 전부 필요.

---

## 9. 토큰 갱신 (60일마다)

장기 토큰은 발급 후 60일이면 만료된다. 만료 전에 갱신하면 새 60일 토큰으로 자동 교체된다.

```bash
.venv/bin/python refresh_token.py                 # 본인(IG_ACCESS_TOKEN)
.venv/bin/python refresh_token.py --account haeun  # 지인(IG_ACCESS_TOKEN_HAEUN)
```

- `.env` 의 해당 키 라인만 새 토큰으로 교체한다.
- **발급 후 24시간이 지나야** 갱신 가능하다.
- **완전 만료 시**엔 갱신 불가 → 4항으로 재발급해야 한다.

---

## 10. 조회 가능한 지표

| 구분 | 지표 |
|------|------|
| **계정 단위** | `reach`(도달), `profile_views`(프로필 조회), `accounts_engaged`(참여 계정), `total_interactions`(총 상호작용), `website_clicks`(웹사이트 클릭), `follower_count`, `online_followers` |
| **게시물 단위** | `reach`, `likes`, `comments`, `saved`, `shares`, `views`, `total_interactions` |

> ⚠️ **`likes`/`comments`/`saved`/`shares` 는 게시물 레벨 전용**이다. 계정 레벨로 호출하면 에러가 나므로 계정 지표에서 제외돼 있다.

### 파생 지표 (팔로워 수와 무관한 콘텐츠 품질 지표)
- **참여율** = 총 상호작용 ÷ 도달 × 100
- **저장률** = 저장 ÷ 도달 × 100

> ⚠️ **Meta가 지표명을 수시로 바꾼다** (예: `impressions`는 2025년 폐지). 스크립트는 지표별로 안전하게 시도하고, 실패한 지표는 비고에 사유를 남긴 채 건너뛴다. "값 없음/에러"가 뜨는 지표가 있으면 현재 API 버전에 맞게 조정이 필요하다.

---

## 11. 스크립트 내부 동작 (참고)

| 요소 | 값/동작 |
|------|------|
| Graph 도메인 | `https://graph.instagram.com/{API_VERSION}` (기본 `v23.0`) |
| 프로필 조회 | `GET /me?fields=user_id,username,account_type,media_count,followers_count,...` |
| 계정 인사이트 | `GET /{ig_id}/insights?metric=...&period=day&metric_type=total_value` |
| 게시물 목록 | `GET /me/media?fields=id,caption,media_type,timestamp,permalink,like_count,comments_count` |
| 게시물 인사이트 | `GET /{media_id}/insights?metric=reach,likes,comments,saved,shares,total_interactions,views` (일괄 실패 시 지표별 개별 재시도) |
| 토큰 갱신 | `GET /refresh_access_token?grant_type=ig_refresh_token&access_token=...` |
| 토큰 선택 | `--account` 없으면 `IG_ACCESS_TOKEN`, 있으면 `IG_ACCESS_TOKEN_<대문자>` |

---

## 12. 자주 겪는 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| "개발자 역할 권한 부족" | 계정이 앱 테스터로 미등록 | 3항 — 테스터 등록 + 인스타에서 초대 수락 |
| 대시보드가 Facebook Login 전환 안내 | 해시태그·상세 집계는 FB Login 전용 | 본인 인사이트는 Instagram Login으로 충분 → 무시하고 진행 |
| 계정 지표에서 saved/likes 에러 | 이들은 게시물 레벨 전용 지표 | 계정 지표에서 제외됨(정상). 게시물 인사이트에서 조회 |
| 프로필 조회 실패 | 토큰 만료·권한 부족 | `.env`의 토큰 확인 → 9항 갱신 또는 4항 재발급 |
| 특정 지표 "값 없음" | Meta 지표명 변경 | 현재 API 버전에 맞게 지표명 조정 필요 |
| 갱신 실패(24시간 미경과) | 발급 직후 갱신 시도 | 24시간 후 재시도. 완전 만료면 재발급 |

---

## 13. 파일 구성

```
17-instagram-insights/
├── 인스타그램-API-연동-가이드.md   ← 이 파일
├── README.md            ← 요약 사용법
├── CLAUDE.md            ← 프로젝트 맥락(핵심 확정값)
├── PROGRESS.md          ← 작업 로그
├── .env.example         ← 환경변수 템플릿 (멀티계정 예시 포함)
├── .env                 ← (직접 생성) 실제 토큰들 — git 제외
├── fetch_insights.py    ← 인사이트 조회 메인 (--account 지원)
├── analyze.py           ← 콘텐츠 성과 분석 리포트 (--account 지원)
├── refresh_token.py     ← 60일 토큰 갱신 (--account 지원)
├── .venv/               ← 파이썬 가상환경
└── output/              ← 조회 결과 (계정별 하위 폴더)
    ├── default/         ← 본인
    └── haeun/           ← 지인 (예)
```

---

## 14. 보안 수칙 (반드시)

- 토큰은 **비밀번호급**. 채팅·커밋·로그에 노출 금지, `.env`로만 다룬다.
- `.env` 는 `.gitignore` 처리 확인.
- 지인의 공유 토큰은 **상대의 개인정보 자산**이다. 필요가 끝나면 상대가 재발급(=폐기)하도록 안내한다.
- 지표명·식별값(앱 ID, IG User ID, 티커류)은 **추측 금지**. API 응답 또는 공식 문서·화면에서 직접 확인한다.

---

*작성 기준: 이 프로젝트의 실제 스크립트(`fetch_insights.py`·`refresh_token.py`·`analyze.py`) 및 `README.md`·`CLAUDE.md`·`PROGRESS.md` 검증 반영. 8항(대행사)은 Meta 공식 문서 + 2026 기준 App Review 실무자료 교차 확인.*
