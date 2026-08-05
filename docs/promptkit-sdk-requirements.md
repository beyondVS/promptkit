# PromptKit SDK (`packages/promptkit`) Specification & Requirements

본 문서는 Framework-Agnostic Pure Python 코어 SDK 패키지인 **`packages/promptkit`**의 상세 기능 사양서입니다.

---

## 1. 개요 및 설계 원칙

`packages/promptkit`은 Prompt Server로부터 원격 프롬프트를 조회하고, 클라이언트 애플리케이션 환경에서 동적 변수를 컴파일(컴파일/파싱/검증)하여 LLM API 호출에 적합한 데이터 형태로 전환해 주는 **경량 Python 라이브러리**이다.

### 핵심 설계 원칙
- **Zero Framework Dependency**: Django, Fast-API 등 특정 웹 프레임워크에 종속되지 않음 (`pydantic` v2, `httpx` 전용).
- **Client-Side Compilation**: 서버에 연산 오버헤드를 전가하지 않고 클라이언트 측에서 동적 변수를 파싱하고 렌더링.
- **LLM Calling Non-Involvement**: SDK는 절대로 LLM API를 직접 호출하거나 대신 실행하지 않음 (Adapters는 렌더링된 인자 포맷팅만 담당).
- **Read-Only Operation**: 프롬프트 CUD 메서드를 일절 포함하지 않으며 오직 안전한 조회(Fetch) 및 로컬 컴파일만 수행.
- **No Silent Fallback**: 서버에서 404 반환 또는 원격 프롬프트 미존재 시 자의적으로 로컬 템플릿이나 `latest` 버전으로 자의적 Fallback하지 않고 명확한 예외 발생.

---

## 2. 핵심 사양 및 요구사항

### 2.1 PromptKitClient (REST Client) & 예외 체계
- `GET /api/v1/prompts/<slug>/` 호출 및 `X-PromptKit-Api-Key` 헤더 전송.
- Query Parameter: `?label=<label_name>` (생략 시 On-live 지정 버전만 조회).
- Strict Timeout 제약: Connect Timeout 1.0초, Read Timeout 2.0초 설정으로 호스트 서비스 블로킹 방지.
- **SDK 예외 계층 구조**:
  - `PromptKitError` (기저 예외 클래스)
  - `AuthenticationError` (401 API 키 미인증)
  - `PromptNotFoundError` (404 존재하지 않는 슬러그)
  - `NoDeployableVersionError` (404 On-live 지정 버전 미존재)
  - `MissingVariableError` (필수 변수 누락)
  - `InvalidVariableTypeError` (Pydantic 변수 타입 검증 실패)

### 2.2 `compile()` 엔진 및 변수 검증
- `{{ variable_name }}` 형식의 Jinja2-style 템플릿 변수 파싱.
- Pydantic v2 기반 변수 타입 검증:
  - `string`: 문자열 검증 및 파싱
  - `number`: 정수/실수 검증
  - `boolean`: 참/거짓(True/False) 검증
  - `json`: JSON 객체/배열 구조 검증
- 필수 변수(`required=True`) 누락 시 `MissingVariableError` 발생 및 기본값(`default_value`) 존재 시 자동 주입.

### 2.3 LLM Provider Adapters 상세 규격
컴파일 완료된 `CompiledPrompt` 객체를 각 공급자 SDK 형식으로 매핑하는 어댑터 인터페이스:
- **`GeminiAdapter`**: Google GenAI SDK 규격
  - `contents`: 역할별 메세지 블록 매핑
  - `system_instruction`: 시스템 프롬프트 독립 매핑
- **`OpenAIAdapter`**: OpenAI SDK 규격
  - `messages`: `[{"role": "system"|"user"|"assistant", "content": "..."}]` 포맷팅
- **`LiteLLMAdapter`**: LiteLLM 호환 멀티-프로바이더 규격 변환

---

## 3. 독립 배포 및 설치 규격

모노레포 내에서 완전히 격리되어 Git Subdirectory 방식으로 독립 설치 가능해야 함:

```bash
pip install "git+https://github.com/<org>/promptkit.git#subdirectory=packages/promptkit"
```
