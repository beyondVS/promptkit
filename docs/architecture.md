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
  - **SDK Read-Only API (`/api/v1/prompts/<slug>/`)**: `X-PromptKit-Api-Key` Header 인증
- **원칙**: 외부 SDK에 프롬프트 CUD API를 노출하지 않으며, LLM을 직접 호출하지 않음.

### 1.2 packages/promptkit (Python SDK Core)
- **역할**: 서버로부터 원격 프롬프트를 조회하고, 클라이언트 측에서 동적 변수를 파싱/컴파일하여 LLM 인자로 변환
- **컴포넌트**:
  - `PromptKitClient`: Read-Only REST API Client
  - `compile()` 엔진: Pydantic v2 기반 변수 유효성 검증 및 로컬 Jinja2-style 렌더링
  - `Adapters`: 컴파일 결과를 공급자 규격(Gemini, OpenAI, LiteLLM 등)으로 전환

### 1.3 packages/promptkit-django (Django Integration)
- **역할**: Django 웹 애플리케이션에서 PromptKit SDK를 플러그인 형태로 손쉽게 적용할 수 있도록 돕는 라이브러리
- **기능**: Django Settings 연동, Django Cache 기반 프롬프트 Caching & ETag 무효화 헬퍼

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
from promptkit import PromptKitClient
from promptkit.adapters import GeminiAdapter
import google.genai as gemini

# 1. 클라이언트 초기화
client = PromptKitClient(base_url="http://localhost:8000", api_key="your-api-key")

# 2. 프롬프트 조회 (라벨 생략 시 on-live 발행 버전만 반환)
prompt = client.prompts.get("summary")

# 3. SDK 수준에서의 로컬 컴파일 실행
compiled = prompt.compile(
    params={
        "title": "LLM 아키텍처",
        "content": "중앙 집중형 프롬프트 서버의 이점은...",
    }
)

# 4. 공급자 어댑터를 통한 인자 변환 (Gemini 스펙에 맞춤)
gemini_args = GeminiAdapter().prepare(compiled)

# 5. 사용자 코드에서 LLM 직접 실행 (SDK는 이 호출에 개입하지 않음)
response = gemini.models.generate_content(
    model="gemini-2.5-pro",
    **gemini_args,
)
```

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
