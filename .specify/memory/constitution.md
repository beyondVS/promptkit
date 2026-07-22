<!--
[SYNC IMPACT REPORT]
- Version Change: v1.0.0 -> v1.1.0
- List of Modified Principles:
  - I. Prompt Registry Focus: Refined to state SDK never calls LLMs and server stores prompts only.
  - II. SDK-First & Framework Agnostic SDK Core: Added to segregate core SDK from Django integrations.
  - III. Prompt Compilation & Adapters: Added to clarify compile() execution on SDK side and convert-only role of adapters.
  - IV. Label-Driven Resolution: Added default production label fallback rule.
  - V. Lightweight & Self-Hosted First: Restructured to define strict project scope boundaries (Out of Scope items).
- Added Sections: None
- Removed Sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md (✅ updated)
  - .specify/templates/spec-template.md (✅ updated)
  - .specify/templates/tasks-template.md (✅ updated)
- Follow-up TODOs: None
-->

# PromptKit Constitution

## Core Principles

### I. Prompt Registry Focus (프롬프트 레지스트리 역할에 집중)
Prompt Server는 LLM Gateway가 아닙니다. Prompt의 저장, 제공, 버전 관리, 검색 역할(Prompt Registry)에만 철저히 집중하며, 실제 LLM 호출, 모델 선택, 토큰 및 비용 관리 등은 Business Server 또는 사용자 코드 영역이 담당합니다. SDK는 절대로 LLM을 직접 호출하지 않습니다.

### II. SDK-First & Framework Agnostic SDK Core (SDK 우선 및 프레임워크 독립 코어)
핵심 SDK인 `packages/promptkit`은 특정 웹 프레임워크에 종속되지 않는 범용 라이브러리로 개발합니다. Django와의 연동 및 편의 기능은 완전히 독립된 어플리케이션 패키지인 `packages/promptkit-django`를 통해 확장합니다.

### III. Prompt Compilation & Adapters (프롬프트 컴파일 및 어댑터)
프롬프트의 동적 변수 렌더링 및 컴파일(`compile()`)은 서버가 아닌 SDK단에서 수행합니다. 각 LLM 공급자(Gemini, OpenAI, LiteLLM 등)에 맞춘 Adapters는 컴파일된 결과물(`CompiledPrompt`)을 해당 API 규격에 맞는 호출 인자(Arguments)로 포맷 변환하는 역할만 담당합니다.

### IV. Label-Driven Resolution (라벨 기반 버전 제공)
프롬프트 조회 시 기본 활성 라벨은 `production`이며, `draft`, `dev`, `experiment` 등을 선택적으로 지원합니다. 프롬프트 요청 시 라벨이 생략된 경우, 기본적으로 `production` 라벨을 반환하도록 설계해야 합니다.

### V. Lightweight & Self-Hosted First (경량화 및 자체 호스팅 우선)
프로젝트는 가볍고(lightweight) 자체 호스팅(self-hosted)이 용이하도록 설계합니다. 따라서 Tracing, Evaluation, Workflow Engine, Agent Framework, Analytics, Cost Dashboard 등은 범위 외(Out of Scope)로 규정하여 코어 복잡성을 최소화합니다.

## 개발 표준 및 보안 제약

### 출력 무결성 (Zero Tolerance)
모든 코드 수정 시, 지정된 변경 부분 외의 기존 문맥(전후 내용, 인접 항목 등)은 단 한 글자도 누락 없이 원본과 100% 동일하게 유지해야 합니다. 도구 호출 및 파일 기록 시 `... (중략) ...` 이나 `// 기존 동일`과 같은 임의의 생략 표현을 사용하는 것을 엄격히 금지합니다.

### 절대 보안 (No Hardcoding)
API Key, 비밀번호, 토큰 등의 민감 정보는 절대로 코드 내에 하드코딩하지 않습니다. 모든 자격 증명은 환경 변수(`.env`) 처리 혹은 시크릿 관리 도구를 기본으로 하며, 해당 설정 파일은 `.gitignore` 등으로 관리되어 레포지토리에 커밋되지 않도록 통제합니다.

### 최소 변경 원칙 (No Vanity Edits)
요청받은 비즈니스 요구사항이나 리팩토링의 직접적인 범위와 무관한 주변 코드(작동에 영향을 주지 않는 불필요한 스타일 수정, 사소한 레이아웃 변경 등)는 임의로 수정하지 않고, 최소 변경 범위만을 정밀하게 조준하여 반영합니다.

### 언어 및 자료구조 표준 (Language & Structure Standards)
- **Python 3.13+** 버전을 표준으로 작동하며, 모든 공개 인터페이스에는 **Type Hints가 필수**입니다.
- 데이터 모델 및 스키마 검증에는 **Pydantic v2**를 기본으로 활용합니다.

## 코드 품질 제어 및 거버넌스

### 기계적 린팅 및 정적 분석 위임
단순 포맷팅과 스타일 분석은 개발자나 AI의 주관에 의존하지 않고, 프로젝트에 사전 설정된 린터/포맷터인 **Ruff** 및 정적 타입 검사기인 **MyPy**의 자동화 규칙에 전적으로 위임합니다.

### 테스트 및 검증 규격
- 모든 테스트는 **pytest** 프레임워크를 기반으로 작성합니다.
- 외부에 노출되는 모든 Public API 및 코어 로직은 **100% 유닛 테스트**를 작성하여 동작을 입증해야 합니다.

### 독립적 배포 및 설치 표준
모노레포의 각 패키지(`packages/promptkit` 등)는 다음과 같이 독자적으로 Git 서브디렉토리를 지정하여 설치(`pip install "git+https://...#subdirectory=..."`) 가능하도록 패키징 표준을 유지해야 합니다.

## Governance

본 헌법(Constitution)은 프로젝트 내의 모든 개별 개발 실천법 및 에이전트 지침서(`AGENTS.md` 등)에 우선하는 최상위 규격입니다. 아키텍처 변경이나 핵심 설계 원칙의 예외 사항은 복잡성에 대한 구체적인 사유를 명시하고 거버넌스 승인을 얻어야 합니다. 본 문서의 개정은 버전 정보의 세부 규칙(SemVer)에 의거하여 이력을 갱신합니다.

**Version**: 1.1.0 | **Ratified**: 2026-07-22 | **Last Amended**: 2026-07-22
