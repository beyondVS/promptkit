# PromptKit Python SDK 안내

`promptkit`은 PromptKit registry에서 발행된 프롬프트를 조회하는 framework-agnostic
동기식 Python 클라이언트입니다. Read-only 방식으로 동작하며 LLM provider 호출,
프롬프트 생성·변경, 응답 캐싱, 요청 재시도 또는 redirect 추적을 수행하지 않습니다.
Django 및 Django REST Framework에 의존하지 않습니다.

## 설치

저장소의 subdirectory에서 패키지를 설치합니다.

```bash
pip install "git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit"
```

## 프롬프트 조회

Registry URL과 API key를 명시적으로 전달합니다. API key는 secret store 또는 환경
변수에 보관하고 소스 코드에 포함하지 않습니다.

```python
import os

from promptkit import PromptKitClient

client = PromptKitClient(
    base_url="https://registry.example.com",
    api_key=os.environ["PROMPTKIT_API_KEY"],
)
prompt = client.fetch("support-reply", label="latest")

print(prompt.template_text)
```

`label`을 생략하면 현재 on-live인 프롬프트 버전을 조회합니다. SDK는 `production`
라벨을 거부하고 redirect를 추적하지 않으며, registry URL은 HTTPS만 허용합니다.
단, 로컬 개발을 위한 loopback HTTP는 허용합니다.

## 캐시된 representation 검증

Core SDK는 응답을 캐시하지 않지만 framework integration에서 사용하는 HTTP validator
primitive를 제공합니다. 이전에 받은 entity tag를 `fetch_conditional()`에 전달합니다.
`200 OK` 결과에는 `prompt`와 `etag`가 모두 포함되고, `304 Not Modified` 결과에는
일치한 `etag`가 포함되며 `prompt`는 `None`입니다.

```python
result = client.fetch_conditional(
    "support-reply",
    label="latest",
    etag='"previous-representation-etag"',
)

if result.not_modified:
    use_cached_prompt()
else:
    prompt = result.prompt
    store_prompt_and_etag(prompt, result.etag)
```

정상 registry 응답에서 ETag가 누락되거나 malformed이면 유효하지 않은 응답으로
거부합니다. 캐시 저장, TTL 정책 및 stale fallback 결정은 호출자의 책임이며,
`promptkit-django`는 opt-in Django Cache 구현을 제공합니다.

## 로컬에서 프롬프트 컴파일

`RetrievedPrompt.compile()`은 애플리케이션 process 안에서 선언된
`{{ variable_name }}` placeholder를 검증하고 렌더링합니다. 전달된 값을 registry로
보내거나 LLM provider를 호출하지 않으며, 값을 다른 template으로 평가하지 않습니다.

```python
from promptkit import (
    InvalidVariableTypeError,
    MissingVariableError,
    TemplateValidationError,
    UnexpectedVariableError,
)

try:
    compiled = prompt.compile({"customer_name": "Ada"})
except MissingVariableError:
    # 참조된 필수 값에 호출자 입력과 유효한 기본값이 모두 없습니다.
    raise
except InvalidVariableTypeError:
    # 입력값 또는 registry 기본값이 선언된 타입과 일치하지 않습니다.
    raise
except UnexpectedVariableError:
    # 호출자가 프롬프트에 선언되지 않은 이름을 전달했습니다.
    raise
except TemplateValidationError:
    # 조회한 template이 잘못되었거나 선언과 일치하지 않습니다.
    raise

print(compiled.content)
print(compiled.version)
```

지원하는 선언 타입은 `string`, `number`, `boolean`, JSON object 또는 array입니다.
성공한 `CompiledPrompt`는 이후 provider별 formatting을 위해 원본 프롬프트의 slug,
version, label 및 렌더링된 ordered section을 보존합니다.

## 컴파일된 프롬프트를 LLM provider 형식으로 변환

PromptKit adapter는 immutable `CompiledPrompt`를 일반 Python dictionary로 변환하기만
합니다. Provider SDK import, model 선택, credential 조회, 생성 설정 적용 또는 LLM
요청을 수행하지 않습니다. Provider client를 호출할 때 호출자 소유 인자를 별도로
전달해야 합니다.

```python
from promptkit import GeminiAdapter, LiteLLMAdapter, OpenAIAdapter

gemini_args = GeminiAdapter.to_generate_content_args(compiled)
chat_args = OpenAIAdapter.to_chat_completions_args(compiled)
responses_args = OpenAIAdapter.to_responses_args(compiled)
litellm_args = LiteLLMAdapter.to_completion_args(compiled)
```

Gemini 인자는 `user` 또는 `model` role을 사용하는 ordered `contents` 항목과 컴파일된
대화 section별 text `part` 하나를 포함합니다. Ordered system section은 `\n\n`으로
결합되어 `config.system_instruction`에 들어가며, system section이 없으면 `config`를
생략합니다.

Chat Completions 인자는 컴파일된 section마다 `system`, `user` 또는 `assistant` role을
가진 ordered `messages` 항목 하나를 포함합니다. Responses 인자는 결합된 system text를
`instructions`에, ordered user/assistant 항목을 `input`에 배치합니다. 반복되는 role은
모든 형식에서 개별 항목으로 유지합니다.

모든 변환은 중복 section order와 정확한 `system`, `user`, `assistant` 이외의 role을
`AdapterConversionError`로 거부합니다. Section이 없는 컴파일 프롬프트는 aggregate
content를 user 항목 하나로 사용합니다. 빈 문자열, whitespace, multiline, Unicode 및
placeholder 형태의 text는 변경하지 않습니다.

프롬프트에 system section만 있으면 각 method는 대상 형식의 system-only 인자를
반환하고 원본 slug, version, label만 포함한 `WARNING`을 정확히 한 번 기록합니다.
대화 content 추가 또는 provider 호출 여부는 호출자가 결정합니다. 컴파일된 프롬프트
text는 이 log에 기록하지 않습니다.

LiteLLM 인자는 컴파일된 section마다 ordered
`{"role": "system"|"user"|"assistant", "content": "..."}` 항목 하나를 `messages`
아래에 포함합니다. PromptKit은 LiteLLM 설치·import, 필수 `model` 선택, credential
제공, 생성 option 설정 또는 `litellm.completion` 호출을 수행하지 않습니다.
애플리케이션이 요청할 때 이러한 호출자 소유 값을 직접 제공합니다.
