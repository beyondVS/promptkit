# PromptKit 🚀

> **Lightweight, Self-Hosted Prompt Registry & Compilation SDK**

PromptKit은 LLM 기반 애플리케이션에서 사용되는 프롬프트(Prompt)를 코드와 분리하여 중앙에서 안전하게 관리하고 배포하기 위한 경량화 프롬프트 레지스트리(Prompt Registry) 및 Python SDK입니다.

애플리케이션 재배포 없이 프롬프트를 즉시 변경 및 동적으로 렌더링할 수 있으며, LLM 호출 오버헤드를 서버에 전가하지 않고 SDK 단에서 안전하게 처리합니다.

---

## 💡 Key Principles & Architecture

* **LLM Gateway 배제 (Prompt Registry Focus)**: Prompt Server는 LLM 호출을 대행하지 않으며, 프롬프트 저장, 버전 관리, 라벨 조회 역할에만 집중합니다.
* **SDK-First & Client-Side Compilation**: 동적 변수 파싱 및 컴파일(`compile()`)은 SDK에서 처리하여 서버 부하 및 API 지연(Latency)을 최소화합니다.
* **Framework Agnostic Core SDK**: 코어 SDK (`packages/promptkit`)는 순수 Python 3.13+ 기반으로 유지되며, Django 전용 통합 기능은 독립 패키지(`packages/promptkit-django`)로 확장됩니다.
* **Label-Driven Fallback**: 라벨 생략 시 기본적으로 `production` 라벨 버전을 자동 반환하며, `draft`, `dev`, `experiment` 라벨 조회를 지원합니다.
* **Subdirectory 독립 설치**: 모노레포 구조이지만 각 패키지를 외부 비즈니스 프로젝트에서 Git 서브디렉토리로 격리 설치할 수 있습니다.

---

## 🏗️ Monorepo Structure

```text
promptkit/
├── apps/
│   └── server/            # Django REST Framework 기반 Prompt Management Server
├── packages/
│   ├── promptkit/         # Framework-Agnostic Core Python SDK
│   └── promptkit-django/  # Django 설정 및 Cache API 연동 패키지
├── docs/                  # 아키텍처 및 요구사항 명세 문서
├── examples/              # E2E 사용 예제 스크립트
└── tests/                 # 하이브리드 테스트 수트 (pytest / TestCase)
```

---

## 📦 Installation

### Core Python SDK (`packages/promptkit`)

* **uv (추천)**
  ```bash
  uv add "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
  ```
* **pip**
  ```bash
  pip install "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
  ```

### Django Integration Package (`packages/promptkit-django`)

* **uv (추천)**
  ```bash
  uv add "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
  ```
* **pip**
  ```bash
  pip install "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
  ```

---

## ⚡ Quick Start

```python
from promptkit import PromptKitClient
from promptkit.adapters import GeminiAdapter
import google.genai as gemini

# 1. REST Client 초기화
client = PromptKitClient(base_url="http://localhost:8000", api_key="your-api-key")

# 2. 원격 프롬프트 조회 (기본 production 라벨 탐색)
prompt = client.prompts.get("customer_summary")

# 3. SDK 로컬 컴파일 (Pydantic v2 기반 변수 유효성 검증)
compiled = prompt.compile(
    params={
        "customer_name": "홍길동",
        "product_name": "PromptKit Enterprise",
        "language": "ko",
    }
)

# 4. LLM 어댑터를 사용해 공급자별 호출 인자 규격으로 변환
prepared = GeminiAdapter().prepare(compiled)

# 5. 애플리케이션 코드에서 실제 LLM 호출
response = gemini.models.generate_content(
    model="gemini-2.5-pro",
    **prepared,
)

print(response.text)
```

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

---

## 📄 Documentation

* 📌 [Prompt Server Requirements](docs/prompt-server-requirements.md)
* 📐 [Project Specification](docs/project-spec.md)
* 🗺️ [Architecture Diagram](docs/architecture.md)
* 📅 [Implementation Plan (18-Day MVP)](docs/project_plan.md)
* 📜 [Project Constitution](.specify/memory/constitution.md)

---

## 📝 License

Distributed under the [MIT License](LICENSE).