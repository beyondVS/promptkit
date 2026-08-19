# PromptKit 🚀

> **Lightweight, Self-Hosted Prompt Registry & Compilation SDK**

PromptKit은 LLM 기반 애플리케이션에서 사용되는 프롬프트(Prompt)를 코드와 분리하여 중앙에서 안전하게 관리하고 배포하기 위한 경량화 프롬프트 레지스트리(Prompt Registry) 및 Python SDK입니다.

애플리케이션 재배포 없이 프롬프트를 즉시 변경 및 동적으로 렌더링할 수 있으며, LLM 호출 오버헤드를 서버에 전가하지 않고 SDK 단에서 안전하게 처리합니다.

---

## 💡 Key Principles & Architecture

* **LLM Gateway 배제 (Prompt Registry Focus)**: Prompt Server는 LLM 호출을 대행하지 않으며, 프롬프트 저장, 대시보드 기반 버전 관리(CUD), 및 SDK 전용 Read-only 라벨 조회 역할에만 집중합니다.
* **Django Template 대시보드 CUD**: 프롬프트 생성, 수정, 삭제(CUD) 및 관리자 인증(Django Session Auth)은 백엔드 대시보드에서 전담합니다.
* **SDK Read-Only Fetch**: `promptkit`은 `X-PromptKit-Api-Key` HTTP Header 인증을 거쳐 레지스트리로부터 프롬프트를 안전하게 조회(Read-only)합니다.
* **ETag 기반 조건부 검증**: Prompt Server는 조회 결과의 canonical representation으로 strong ETag를 생성하며, Core SDK는 `If-None-Match`/`304 Not Modified`를 다루는 조건부 조회 API를 제공합니다.
* **Django Opt-in Cache**: `promptkit-django`의 `fetch_cached()`는 호스트 프로젝트의 `CACHES["default"]`와 짧은 TTL을 이용해 fresh hit와 stale revalidation을 처리합니다. 기존 `get_client().fetch()`는 캐시되지 않습니다.
* **SDK-First & Client-Side Compilation**: 동적 변수 파싱 및 컴파일(`compile()`)은 SDK에서 처리하여 서버 부하 및 API 지연(Latency)을 최소화합니다.
* **Provider-Neutral Adapters**: 컴파일 결과를 Gemini `generate_content`, OpenAI Chat Completions·Responses 및 LiteLLM `completion` 호출 인자 형태의 순수 Python dictionary로 변환하며, 공급자 SDK import나 실제 LLM 호출은 수행하지 않습니다.

* **Framework Agnostic Core SDK**: 코어 SDK (`packages/promptkit`)는 순수 Python 3.13+ 기반으로 유지되며, Django 전용 통합 기능은 독립 패키지(`packages/promptkit-django`)로 확장됩니다.
* **Label-Driven On-Live Resolution**: 라벨 생략 시 해당 프롬프트의 `on-live`로 지정된 발행 버전만 반환하며, `on-live`가 없으면 자동 fallback 없이 404(`no_deployable_version`)를 응답합니다. (`production` 라벨 사용은 금지됩니다.)
* **Subdirectory 독립 설치**: 모노레포 구조이지만 각 패키지를 외부 비즈니스 프로젝트에서 Git 서브디렉토리로 격리 설치할 수 있습니다.

---

## 🏗️ Monorepo Structure

```text
promptkit/
├── apps/
│   └── server/            # Django REST Framework 기반 Prompt Management Server
├── packages/
│   ├── promptkit/         # Framework-Agnostic Core Python SDK
│   └── promptkit-django/  # Django 설정, SDK 등록 및 opt-in 캐시 패키지
├── docs/                  # 아키텍처 및 요구사항 명세 문서
├── examples/              # E2E 사용 예제 스크립트
└── tests/                 # 하이브리드 테스트 수트 (pytest / TestCase)
```

---

## 📦 Installation

### Core Python SDK (`packages/promptkit`)

```bash
uv add "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
```

### Django Integration Package (`packages/promptkit-django`)

코어 SDK를 별도 패키지 인덱스에 배포하지 않으므로 기본 브랜치의 두 Git
subdirectory를 함께 설치합니다.

```bash
uv add \
  "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit" \
  "promptkit-django @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
```

두 패키지는 함께 설치·업그레이드해야 합니다. `promptkit-django`만 설치하면
resolver가 패키지 인덱스에서 `promptkit`을 찾으므로 현재 배포 정책에서는 실패합니다.

### 모노레포 격리 배포 검증

`promptkit`, `promptkit-django`, Prompt Server는 각각 새 wheel과 local committed Git
subdirectory 설치 경로를 격리 환경에서 검증합니다. SDK와 Django 통합은 core-first 및
integration-first 요청 순서도 확인합니다. 이 검증은 `uv`만 사용하며, local Git preflight가
실패하면 direct `pip`로 우회하지 않습니다.

외부 의존성은 artifact 판정 전에 uv로 준비하고, 실제 target artifact는 임시 wheelhouse의
`--no-index --find-links` 경로에서만 설치합니다. 따라서 repository import path나 package
index 가용성이 통과 결과를 가리지 않습니다.

```powershell
uv run pytest tests/deployment/test_isolated_installation.py
```

출력은 scenario별 deployment unit, 설치 방식, 실패 단계 및 verdict를 요약해 릴리스
담당자가 빠르게 판정할 수 있게 합니다.

---

## ⚡ Quick Start

```python
from promptkit import GeminiAdapter, LiteLLMAdapter, OpenAIAdapter, PromptKitClient

# 1. REST Client 초기화
client = PromptKitClient(base_url="http://localhost:8000", api_key="your-api-key")

# 2. 원격 프롬프트 조회 (라벨 생략 시 on-live 발행 버전 반환)
prompt = client.fetch("customer_summary")

# 3. SDK 로컬 컴파일 (Pydantic v2 기반 변수 유효성 검증)
compiled = prompt.compile(
    params={
        "customer_name": "홍길동",
        "product_name": "PromptKit Enterprise",
        "language": "ko",
    }
)

# 4. 공급자 SDK에 전달할 호출 인자 변환
gemini_args = GeminiAdapter.to_generate_content_args(compiled)
chat_args = OpenAIAdapter.to_chat_completions_args(compiled)
responses_args = OpenAIAdapter.to_responses_args(compiled)
litellm_args = LiteLLMAdapter.to_completion_args(compiled)

# 5. 렌더링 결과와 원본 버전 메타데이터 사용
print(compiled.content)
print(compiled.version)
```

`compile()`과 어댑터는 입력값을 서버나 LLM 공급자에게 전송하지 않습니다. LiteLLM
어댑터는 순서가 보존된 `messages`를 반환하며, 모델, 자격 증명, 생성 설정 및 실제
`litellm.completion` 호출을 포함한 API 호출은 호출자 애플리케이션의 책임입니다.

Django 애플리케이션에서는 `PROMPTKIT`에 `CACHE_TTL`(기본 `60.0`초)을 설정하고
`promptkit_django.fetch_cached()`를 명시적으로 호출할 수 있습니다. `CACHE_TTL=0`은
캐시 읽기와 쓰기를 모두 비활성화합니다. 자세한 계약은
[Django Integration Requirements](docs/promptkit-django-requirements.md)를 참고하십시오.

### Playground 로컬 프리뷰

스태프 사용자는 대시보드의 버전 상세 화면에서 Playground를 열어 선언된 변수 값을
입력하고, SDK의 공개 `RetrievedPrompt.compile()` 엔진으로 렌더링된 aggregate content와
ordered sections를 확인할 수 있습니다. 이 POST 화면은 Django Session Auth와 CSRF로
보호되며 데이터베이스를 변경하거나 LLM 공급자를 호출하지 않습니다. 실행 방법은
[Prompt Server 안내](apps/server/README.md)를 참고하십시오.

### Prompt Server → SDK → Gemini E2E 예제

격리된 소비자 예제는 실제 Prompt Server에서 on-live 버전을 조회하고 로컬 컴파일과
Gemini 인자 변환까지 수행합니다. 기본 실행은 Gemini를 호출하지 않으며, `--live`를
명시한 경우에만 재시도 없이 Gemini 요청을 정확히 한 번 전송합니다.

```powershell
Copy-Item examples/gemini-e2e/.env.example examples/gemini-e2e/.env
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py
# 외부 전송과 quota/비용 가능성을 확인한 뒤에만 실행
uv run --project examples/gemini-e2e python examples/gemini-e2e/gemini_e2e.py --live
```

예제는 자체 디렉토리의 `.env`를 현재 작업 디렉토리와 무관하게 자동으로 읽으며,
이미 설정된 shell 환경 변수를 우선합니다. 설정 항목과 안전한 실패 계약은
[Gemini E2E Example](examples/gemini-e2e/README.md)을 참고하십시오.

---

## 🛠️ Local Development & Mechanical Harness

본 프로젝트는 **uv** 패키지 매니저와 자동화된 기계적 하네스 검증을 표준으로 준수합니다.

### 1. 환경 생성 및 의존성 동기화
```bash
uv sync
```

### 2. 정적 분석 및 포맷팅 검사 (Ruff & MyPy)
```bash
uv run ruff check ; uv run ruff format ; uv run mypy .
```

### 3. 유닛 및 통합 테스트 구동
```bash
uv run pytest
```

루트 `pytest` 설정은 `tests/`를 대상으로 하므로 서버 앱 내부의 Playground 테스트는
다음 명령으로 별도 실행합니다.

```bash
uv run pytest apps/server/prompts/tests/test_dashboard_playground.py
uv run pytest tests/examples/test_gemini_e2e.py
```

---

## 📄 Documentation

* 📌 [Prompt Server Requirements](docs/promptkit-server-requirements.md)
* 📦 [Core SDK Requirements](docs/promptkit-sdk-requirements.md)
* 🔌 [Django Integration Requirements](docs/promptkit-django-requirements.md)
* 📐 [Project Specification](docs/project-spec.md)
* 🗺️ [Architecture Diagram](docs/architecture.md)
* 📅 [Implementation Plan (19-Day MVP)](docs/project-plan.md)
* 📜 [Project Constitution](.specify/memory/constitution.md)

---

## 📝 License

Distributed under the [MIT License](LICENSE).
