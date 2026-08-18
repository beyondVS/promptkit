# PromptKit Architecture & Implementation Specification

본 문서는 PromptKit 프로젝트의 시스템 아키텍처, 컴포넌트 간 상호작용 및 데이터 컴파일 흐름을 기술합니다. 이 문서는 헌법(`constitution.md`) 및 에이전트 규칙(`AGENTS.md`)의 시스템 아키텍처 가이드라인 역할을 수행합니다.

---

## 1. Monorepo Architecture

PromptKit은 다음과 같이 분리된 역할과 책임을 가진 단일 저장소(Monorepo)로 구성됩니다. 상세 사양은 [project-spec.md](project-spec.md)를 참조하십시오.

```text
promptkit/
├── apps/
│   └── server/               # Django REST Framework 기반 관리 서버
├── packages/
│   ├── promptkit/            # Framework-agnostic Python SDK (Core)
│   └── promptkit-django/     # Django 연동 통합 라이브러리
├── docs/                     # 설계 및 아키텍처 문서
├── examples/                 # 사용 사례 예제 코드
└── tests/                    # 유닛 및 통합 테스트
```

### 1.1 apps/server (Prompt Server)
- **역할**: 프롬프트 데이터의 영속성 관리, 스태프 대시보드 CUD 및 Read-only API 서빙
- **접근 제어**:
  - **대시보드 CUD (`/dashboard/`)**: Django Session Auth 및 CSRF 보장 (스태프 전용)
  - **Playground (`/dashboard/versions/<version_id>/playground/`)**: 선택한 ORM 버전을
    SDK `RetrievedPrompt`로 변환하여 request-local `compile()`을 수행하는 스태프 전용 프리뷰
  - **SDK Read-Only API (`/api/v1/prompts/<slug>/`)**: `X-PromptKit-Api-Key` Header 인증
- **원칙**: 외부 SDK에 프롬프트 CUD API를 노출하지 않으며, Playground도 DB 쓰기나
  LLM 호출 없이 렌더링된 `CompiledPrompt` 텍스트만 표시함.

### 1.2 packages/promptkit (Python SDK Core)
- **역할**: 서버로부터 원격 프롬프트를 조회하고, 클라이언트 측에서 동적 변수를 파싱/컴파일하여 LLM 인자로 변환
- **컴포넌트**:
  - `PromptKitClient`: Read-Only REST API Client
  - `compile()` 엔진: Pydantic v2 기반 변수 유효성 검증 및 로컬 Jinja2-style 렌더링
  - `GeminiAdapter`: `CompiledPrompt`를 Google Gen AI `generate_content` 호출 인자로 변환
  - `OpenAIAdapter`: `CompiledPrompt`를 OpenAI Chat Completions 또는 Responses 호출 인자로 변환
  - `LiteLLMAdapter`: `CompiledPrompt`를 LiteLLM `completion`의 ordered `messages` 호출 인자로 변환
  - 어댑터는 순수 dictionary 변환만 담당하며 공급자 SDK를 import하거나 LLM을 호출하지 않음

### 1.3 packages/promptkit-django (Django Integration)
- **역할**: Django 웹 애플리케이션에서 PromptKit SDK를 플러그인 형태로 손쉽게 적용할 수 있도록 돕는 라이브러리
- **현재 기능**: 단일 `PROMPTKIT` Settings mapping 검증, AppConfig 시작 시 `PromptKitClient` 자동 등록, `get_client()` 접근, opt-in `fetch_cached()` 및 범위별 캐시 무효화
- **설정 계약**: `BASE_URL`, `API_KEY` 필수, `TIMEOUT` 선택(기본값 `10.0`), `CACHE_TTL` 선택(기본값 `60.0`초). 잘못되거나 알 수 없는 설정은 자격 증명을 노출하지 않고 시작 단계에서 실패
- **캐시 경계**: 호스트의 `CACHES["default"]`만 사용한다. `fetch_cached()`는 TTL 동안 fresh entry를 반환하고 다음 동일 길이 구간에서는 ETag로 재검증한다. `get_client().fetch()`는 기존처럼 항상 uncached이며 `CACHE_TTL=0`이면 모든 캐시 I/O를 우회한다.
- **정합성**: 서버는 직렬화된 응답 representation의 strong ETag를 반환한다. stale entry는 `If-None-Match` 요청의 `304`로 freshness만 연장하거나 `200` 응답으로 원자적으로 교체하며, 원격 오류에는 stale fallback을 제공하지 않는다.
- **설치 경계**: 패키지 인덱스를 사용하지 않으므로 외부 사용자는 기본 브랜치의 `packages/promptkit`과 `packages/promptkit-django` Git subdirectory를 함께 설치

---

## 2. Prompt Compile Flow

프롬프트가 서버에 저장된 이후, 사용자의 코드 내에서 LLM API로 도달하기까지의 데이터 컴파일 흐름은 다음과 같습니다.

```text
Prompt (서버 저장 원본)
    ↓
Version (특정 버전 선택)
    ↓
Deployment Selector (On-live 또는 명시한 발행 라벨)
    ↓
Variables (동적 주입 변수 매핑)
    ↓
Compile (SDK 로컬 렌더링 엔진)
    ↓
CompiledPrompt (렌더링 완료된 텍스트 및 메타데이터)
    ↓
Adapter (공급자별 전처리 및 포맷 변환)
    ↓
LLM SDK (사용자 코드에서의 API 호출 인수)
```

### SDK 사용 가이드라인 예시

```python
from promptkit import GeminiAdapter, LiteLLMAdapter, OpenAIAdapter, PromptKitClient

# 1. 클라이언트 초기화
client = PromptKitClient(base_url="http://localhost:8000", api_key="your-api-key")

# 2. 프롬프트 조회 (라벨 생략 시 on-live 발행 버전만 반환)
prompt = client.fetch("summary")

# 3. SDK 수준에서의 로컬 컴파일 실행
compiled = prompt.compile(
    params={
        "title": "LLM 아키텍처",
        "content": "중앙 집중형 프롬프트 서버의 이점은...",
    }
)

# 4. 공급자별 호출 인자 생성
gemini_args = GeminiAdapter.to_generate_content_args(compiled)
chat_args = OpenAIAdapter.to_chat_completions_args(compiled)
responses_args = OpenAIAdapter.to_responses_args(compiled)
litellm_args = LiteLLMAdapter.to_completion_args(compiled)

# 5. 완성된 텍스트와 원본 버전 정보 사용
print(compiled.content)
print(compiled.version)
```

Day 13의 SDK는 조회·검증·로컬 렌더링에 더해 Gemini, OpenAI 및 LiteLLM용 호출 인자
변환을 제공합니다. 모델, 자격 증명, 생성 설정과 실제 LLM 호출은 호출자가 관리하며
SDK는 어떤 경우에도 공급자 SDK를 import하거나 LLM 호출을 대행하지 않습니다.

### Playground 및 실행 예제 경계

대시보드 Playground는 서버에 저장된 특정 버전과 사용자가 제출한 변수만 사용해 SDK
컴파일을 한 번 수행합니다. 이 경로는 원격 Read-only API를 다시 호출하지 않고,
aggregate content와 ordered sections를 autoescaped 텍스트로 표시하며 영속 상태를
변경하지 않습니다.

`examples/gemini-e2e`는 반대로 외부 애플리케이션의 책임 경계를 보여주는 격리 예제입니다.
실제 Read-only API 조회와 로컬 컴파일·Gemini 변환을 수행하되, 기본 모드는 공급자 SDK를
생성하지 않습니다. 사용자가 `--live`를 명시한 경우에만 예제 애플리케이션이 Gemini를
정확히 한 번 호출합니다. 따라서 `google-genai`와 `.env` 로딩 의존성은 코어 SDK나
Prompt Server가 아니라 예제 프로젝트에만 존재합니다.

---

## 3. Deployment & Operational Rules

### 3.1 On-Live & Label 배포 정책
- 라벨이 생략되면 해당 프롬프트의 **`on-live`로 지정된 발행 버전**만 반환한다.
- `on-live` 버전이 지정되어 있지 않으면 `latest`, 사용자 정의 라벨, 초안으로 대체하지 않고 `404 no_deployable_version` 오류를 반환한다.
- `latest`는 마지막 발행 버전을 가리키는 유일한 시스템 예약 라벨이며, 사용자 정의 라벨은 발행 버전만 가리킬 수 있다.
- `production` 라벨은 사용할 수 없다.

### 3.2 버전 라이프사이클 및 동시성
- **초안 (Draft)**: 자유로운 편집, 변수/섹션 CUD 가능. 삭제 가능.
- **발행 (Published)**: 변경 불가능한(Immutable) 릴리즈 버전. 편집/삭제 불가. 복제(Clone)를 통해 새 초안으로 파생 가능.
- **낙관적 동시성 (Optimistic Locking)**: `Version.revision` 카운터를 통해 대시보드 동시 수정 충돌을 방지한다 (`StaleRevisionError`).
