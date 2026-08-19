# PromptKit Project Specification

본 문서는 PromptKit 프로젝트의 종합 기술 사양서이자 핵심 가이드라인(Single Source of Truth)입니다.

---

## 1. Project Overview & Scope

PromptKit은 LLM 애플리케이션용 자가호스팅 프롬프트 레지스트리(Prompt Registry) 및 클라이언트 측 컴파일 SDK입니다.

### In Scope
- 프롬프트 CRUD 및 대시보드 기반 이력/버전 관리
- On-live 및 발행 라벨 기반 배포 관리
- SDK 측 로컬 동적 변수 컴파일 및 validation
- Framework-agnostic Python Core SDK (`packages/promptkit`)
- Django 애플리케이션용 통합 패키지 (`packages/promptkit-django`)
- 웹 대시보드 내 템플릿 테스트용 Playground

### Out of Scope (코어 복잡성 제외)
- LLM 호출 트레이싱(Tracing) 및 실시간 로깅
- 프롬프트 품질 평가(Evaluation)
- 멀티스텝 워크플로우 엔진(Workflow Engine)
- 에이전트 프레임워크(Agent Framework)
- 비용/사용량 통계 대시보드(Analytics & Cost Dashboard)

---

## 2. Technical Stack & Development Rules

### Technology Stack
- **Language / Runtime**: Python 3.13+
- **Package Manager**: `uv` (선언적 의존성 통제)
- **Server Framework**: Django 5.x, Django REST Framework, PostgreSQL (Production) / SQLite (Local Development)
- **Static Analysis & Linting**: Ruff, MyPy (`strict` / type hints mandatory)
- **Test Framework**: `pytest` (Django ORM 테스트는 `TestCase` 활용)
- **Schema Validation**: Pydantic v2

### Core Rules
- **No Secrets**: API Key, DB 비밀번호 등 민감 정보 하드코딩 금지 (`.env` 전용).
- **SDK Boundaries**: SDK는 절대로 LLM API를 직접 호출하지 않음 (Adapters는 렌더링된 인자 포맷팅만 전담).
- **Git Subdirectory Installation**: 모노레포의 패키지는 Git subdirectory로 설치하며, 별도 패키지 인덱스를 사용하지 않는 현재 정책상 Django 통합 사용자는 코어 SDK와 통합 패키지를 함께 지정해야 함:
  ```bash
  uv add \
    "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit" \
    "promptkit-django @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
  ```
- **Isolated Artifact Validation**: `promptkit`, `promptkit-django`, Prompt Server는 각각 새 wheel과 local committed Git subdirectory 경로에서 uv-only로 검증한다. target artifact 설치는 임시 wheelhouse와 `--no-index --find-links`를 사용하며 repository source path와 package index를 판정 경계에서 제외한다.
- **Artifact Metadata Contract**: 모든 wheel은 `Name`, `Version`, `Requires-Python`, `Requires-Dist` 및 공개 import 모듈을 보존한다. Prompt Server wheel은 `apps.server.*` namespace, templates, migrations와 `promptkit>=0.1,<0.2` 의존성을 포함한다.
- **Release Decision Matrix**: 6개 독립 설치 경로와 2개 SDK/Django 설치 순서를 실제 소비자 환경에서 검증하고, 실패를 scenario/stage에 귀속하며 동일 matrix를 연속 두 번 실행한다.

---

## 3. Package Specification

| 패키지 | 주요 역할 및 책임 | 주요 의존성 |
| :--- | :--- | :--- |
| `apps/server` | 프롬프트 저장소, 대시보드 CUD, Read-Only API Serving, 독립 wheel/Git subdirectory 배포 | Django, DRF, `promptkit>=0.1,<0.2`, PostgreSQL |
| `packages/promptkit` | 원격 프롬프트 fetch와 ETag 조건부 조회, 로컬 `compile()`, Pydantic 변수 검증, LLM Adapters | Pydantic v2, httpx |
| `packages/promptkit-django` | `PROMPTKIT` Settings 검증, SDK 자동 등록, opt-in Django Cache/ETag 재검증 및 무효화 | `promptkit`, Django, Pydantic v2 |

---

## 4. MVP Definition

1. **Prompt Server**: 대시보드 CUD (`/dashboard/`), Read-Only API (`GET /api/v1/prompts/<slug>/`)
2. **Version & Deployment**: 초안/발행/복제(Clone) 라이프사이클, On-live 지정 (자동 Fallback 금지, `production` 라벨 금지)
3. **Core SDK & Adapters**: `PromptKitClient`, `compile()`, Gemini `generate_content`, OpenAI Chat Completions / Responses 및 LiteLLM `completion` Adapters
4. **Django Integration**: `promptkit-django` 설정 검증, SDK 인스턴스 자동 등록 및 호스트의 default Django Cache를 이용한 opt-in ETag/TTL 정합성 계층
5. **Playground**: 대시보드 내 템플릿 컴파일 프리뷰 인터페이스
