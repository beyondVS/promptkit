# PromptKit Architecture & Implementation Specification

본 문서는 PromptKit 프로젝트의 아키텍처와 구현 사양을 기술합니다. 이 문서는 헌법(`constitution.md`) 및 에이전트 규칙(`AGENTS.md`)의 구체적인 구현 지침서 역할을 수행합니다.

---

## 1. Project Overview & Scope

PromptKit은 경량 자가호스팅 프롬프트 관리 서버 및 개발자 친화적인 SDK 세트입니다.

### In Scope
- 프롬프트 CRUD 및 변경 이력(Version) 관리
- 활성 라벨(Label) 관리
- SDK 수준의 동적 변수 컴파일(Compile)
- Framework-agnostic Python SDK 패키지 제공
- Django 어플리케이션용 통합 패키지 제공
- 프롬프트 테스트용 플레이그라운드(Playground)

### Out of Scope (코어 복잡성 제외 항목)
- LLM 호출 트레이싱(Tracing) 및 실시간 로깅
- 프롬프트 품질 평가(Evaluation)
- 멀티스텝 프롬프트 워크플로우 엔진(Workflow Engine)
- 에이전트 프레임워크(Agent Framework)
- 사용량 및 비용 대시보드(Analytics & Cost Dashboard)

---

## 2. Monorepo Architecture

PromptKit은 다음과 같은 구조의 단일 저장소(Monorepo)로 개발됩니다.

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

### 2.1 apps/server (Prompt Server)
- **역할**: 프롬프트 데이터의 물리적 영속성 및 원격 API 관리
- **스택**: Python 3.13+, Django, Django REST Framework, PostgreSQL
- **기능**:
  - 프롬프트 CRUD API
  - 버전(Version) 관리 API
  - 라벨(Label) 관리 API
  - 변수(Variable) 명세 및 섹션(Section) 메타데이터 관리
  - 관리자용 플레이그라운드 인터페이스 제공
  - API 호출 인증(Authentication)

### 2.2 packages/promptkit (Python SDK)
- **역할**: 프롬프트의 동적 컴파일 및 공급자별 Adapter 연동을 제공하는 핵심 코어 SDK
- **기능**:
  - REST API Client 제공 (Server와 연동하여 원격 프롬프트 조회)
  - 로컬 컴파일(`compile()`) 엔진 구현
  - 변수 검증(Validation) 및 JSON Schema 호환
  - LLM 공급자 어댑터(Gemini, OpenAI, LiteLLM) 구현
- **⚠️ 절대 원칙**: SDK는 절대로 LLM Provider의 API를 직접 호출하지 않습니다. Adapters는 컴파일된 결과물(`CompiledPrompt`)을 공급자 라이브러리 형식에 알맞은 파라미터(Arguments)로 전환하는 포맷팅 역할만 담당합니다.

### 2.3 packages/promptkit-django (Django Integration)
- **역할**: Django 환경에서 PromptKit을 플러그인 형태로 손쉽게 적용할 수 있도록 돕는 라이브러리
- **의존성**: Python SDK(`packages/promptkit`)에만 의존
- **기능**:
  - Django Settings.py 기반 자동 초기화 설정
  - 캐시(Django Cache) 기반 프롬프트 조회 최적화
  - 편의용 Helper APIs 제공

---

## 3. Prompt Compile Flow

프롬프트가 서버에 저장된 이후, 사용자의 코드 내에서 LLM API로 도달하기까지의 데이터 컴파일 흐름은 다음과 같습니다.

```text
Prompt (서버 저장 원본)
    ↓
Version (특정 버전 선택)
    ↓
Label (라벨 매핑 예: production)
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
client = PromptKitClient(base_url="http://localhost:8000", api_key="...")

# 2. 프롬프트 조회 (라벨 생략 시 'production' 기본 적용)
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

## 4. Operational Rules

### 4.1 Labels 정책
- **기본값 (Default Label)**: `production`
- **지원 선택 라벨 (Optional Labels)**: `draft`, `dev`, `experiment`
- **동작**: 사용자가 프롬프트를 요청할 때 라벨을 명시하지 않은 경우, 무조건 `production` 라벨이 지정된 최신 버전을 매칭하여 반환해야 합니다.

### 4.2 API 요구사항
서버가 외부에 노출해야 하는 핵심 API 엔드포인트 목록입니다.
- 프롬프트 CRUD
- 버전(Version) CRUD
- 라벨(Label) CRUD
- 플레이그라운드 인터페이스
- API 인증 모듈
- **⚠️ 절대 원칙**: 서버는 LLM을 호출하거나 실행을 대행하는 어떠한 API도 가지지 않습니다.

### 4.3 MVP 구성 정의
초기 가동(MVP)에 필수적으로 보장되어야 하는 범위입니다.
1. 프롬프트 CRUD 및 관리 화면
2. 버전 관리 및 롤백 기능
3. 라벨 관리 및Fallback 메커니즘
4. Python SDK 코어 및 compile() 메서드
5. Gemini 및 LiteLLM 어댑터(Adapter) 구현
6. Django Integration 패키지 (`promptkit-django`)
7. 웹 관리자 콘솔 플레이그라운드
