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
- `fetch()`는 기존의 uncached 전체 조회 계약을 유지하며, `fetch_conditional(..., etag=...)`은 선택적으로 `If-None-Match`를 보내 `200 OK`와 `304 Not Modified`를 구분한 `ConditionalFetchResult`를 반환한다.
- 조건부 조회의 `200` 결과는 `prompt`와 유효한 quoted ETag를 포함하고, `304` 결과는 `prompt=None`과 ETag를 포함한다. 성공 응답의 ETag가 누락되거나 malformed이면 `InvalidResponseError`를 발생시킨다.
- 코어 SDK는 조건부 요청 primitive만 제공하며 응답 저장, TTL, 무효화 및 stale fallback 정책은 구현하지 않는다.
- 기본 Timeout은 10초이며, 호출자가 양수 값으로 재정의할 수 있습니다.
- **SDK 예외 계층 구조**:
  - `PromptKitError` (기저 예외 클래스)
  - `InvalidConfigurationError` (빈 API key, 안전하지 않거나 잘못된 client 설정)
  - `InvalidRequestError` / `InvalidLabelError` (요청 전 입력 또는 금지 라벨 검증 실패)
  - `AuthenticationError` (401 API 키 미인증)
  - `PromptNotFoundError` (404 존재하지 않는 슬러그)
  - `NoDeployableVersionError` (404 On-live 지정 버전 미존재)
  - `LabelNotFoundError` (404 명시 라벨 미존재)
  - `RateLimitError` (429 요청 제한)
  - `RedirectError` (redirect 응답 거부)
  - `CommunicationError` (connection, timeout, TLS 또는 응답 전 연결 종료)
  - `InvalidResponseError` (지원하지 않는 상태 또는 잘못된 registry 응답)
  - `MissingVariableError` (필수 변수 누락)
  - `InvalidVariableTypeError` (Pydantic 변수 타입 검증 실패)
  - `UnexpectedVariableError` (선언되지 않은 변수 입력)
  - `TemplateValidationError` (잘못된 템플릿 문법 또는 선언 불일치)
  - `AdapterConversionError` (지원하지 않는 역할 또는 중복된 섹션 순서)

### 2.2 `compile()` 엔진 및 변수 검증
- `RetrievedPrompt.compile(params=...)`은 `{{ variable_name }}` 형식만 파싱하며, 표현식·필터·속성 접근·제어문은 허용하지 않습니다.
- Pydantic v2 기반 변수 타입 검증:
  - `string`: 엄격한 문자열
  - `number`: boolean을 제외한 엄격한 정수/실수
  - `boolean`: 엄격한 참/거짓
  - `json`: JSON 객체/배열 구조
- 호출자 값은 선언된 이름만 허용하며, 누락한 값은 유효한 `default_value`로 보완합니다. 호출자 값은 기본값보다 우선합니다.
- 템플릿·섹션 전체를 검증한 뒤 한 번만 렌더링하므로, 주입 값 안의 `{{ ... }}`는 추가로 해석되지 않습니다.
- 실패 시 부분 결과를 반환하지 않으며, 오류 메시지와 예외 traceback에는 호출자 입력값을 포함하지 않습니다.
- 성공한 `CompiledPrompt`는 렌더링된 aggregate content 및 ordered sections와 함께 원본 `slug`, `version`, `label`을 보존합니다.

### 2.3 LLM Provider Adapters 상세 규격
컴파일 완료된 `CompiledPrompt` 객체를 각 공급자 SDK 형식으로 매핑하는 어댑터 인터페이스:
- **`GeminiAdapter`**: Google GenAI SDK 규격
  - `to_generate_content_args()`: `user`는 `user`, `assistant`는 `model` 역할의 `contents`로 매핑
  - system 섹션은 `\n\n`으로 결합하여 `config.system_instruction`에 매핑
- **`OpenAIAdapter`**: OpenAI SDK 규격
  - `to_chat_completions_args()`: 각 섹션을 ordered `messages`로 매핑
  - `to_responses_args()`: system 섹션은 `instructions`, user/assistant 섹션은 ordered `input`으로 매핑
- **`LiteLLMAdapter`**: LiteLLM `completion` 규격
  - `to_completion_args()`: 각 섹션을 역할과 본문이 보존된 ordered `messages`로 매핑
- **공통 변환 정책**:
  - 섹션 순서를 오름차순으로 정렬하며 반복 역할은 병합하지 않음
  - 섹션이 없으면 aggregate content를 단일 user 항목으로 사용
  - system-only 입력은 공급자별 system-only 인자를 반환하고 민감한 본문 없이 `WARNING` 로그를 한 번 기록
  - 공급자 SDK, 모델, 자격 증명, 생성 설정 및 실제 호출은 어댑터 범위 밖이며 입력 `CompiledPrompt`를 변경하지 않음
  - LiteLLM은 설치하거나 import하지 않으며, 호출자는 `messages` 외에 필요한 `model` 등의 인자와 실제 `litellm.completion` 호출을 관리함

### 2.4 Public API 통합 하네스
- `promptkit.__all__` inventory와 명시적 검증 맵의 일치를 검증하여 public export 누락 또는 stale entry를 식별합니다.
- 정상 fetch → compile → Gemini·OpenAI·LiteLLM 변환 여정과 공개 예외 계층의 실패 경계를 `pytest` 통합 테스트로 검증합니다.

### 2.5 실제 HTTP 실패 복원성 및 로깅 경계
- pytest-django가 관리하는 loopback HTTP Prompt Server의 health readiness를 먼저 확인하고, 실제 SDK client로 on-live 성공 조회와 non-empty key의 401 인증 실패를 검증합니다.
- test-owned socket으로 connection refused와 연결 수락 후 응답 전 종료를 각각 재현하며, 두 경로는 자동 재시도·fallback 없이 `CommunicationError`를 반환해야 합니다.
- 빈 또는 whitespace API key는 HTTP client 생성 전에 `InvalidConfigurationError`로 거부해야 합니다.
- 실제 HTTP로 조회한 prompt의 누락·미선언·잘못된 타입 변수는 각각 공개 compile 예외를 반환하고 부분 결과나 provider adapter 호출을 만들지 않아야 합니다.
- 예외 문자열, traceback 및 호출 애플리케이션이 생성한 diagnostic record에는 API key, authorization header, 변수 값, 전체 template 또는 compiled content가 포함되지 않아야 합니다.
- registry 조회 및 local compile의 scoped 실패 경로에서 SDK는 log record를 emit하거나 handler·level·propagation·출력 대상을 변경하지 않습니다. 호출 애플리케이션이 안전한 예외 타입과 메시지를 자체 정책으로 기록합니다. 이는 system-only adapter 변환의 기존 safe `WARNING` 계약을 변경하지 않습니다.

Focused 검증 명령:

```powershell
uv run pytest tests/promptkit/integration/test_sdk_failure_e2e.py -q
```

---

## 3. 독립 배포 및 설치 규격

모노레포 내에서 완전히 격리되어 Git Subdirectory 방식으로 독립 설치 가능해야 함:

```bash
uv add "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
```

새 wheel과 local committed Git subdirectory 설치는 각각 별도의 uv 가상환경에서 검증한다.
검증 환경은 repository root와 `PYTHONPATH`를 노출하지 않으며 설치된 distribution 위치가
해당 환경 내부인지 확인한다. wheel metadata의 `Name`, `Version`, `Requires-Python` 및
`Requires-Dist`(`httpx>=0.27,<1`, `pydantic>=2,<3`)를 공개 import·compile smoke와 함께
검증한다. Pydantic 의존성을 제거한 실제 변조 wheel은 설치 후
`promptkit-missing-dependency:smoke`로 식별되어야 한다.
