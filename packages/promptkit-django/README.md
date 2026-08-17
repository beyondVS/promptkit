# PromptKit Django Integration 안내

`promptkit-django`는 Django application lifecycle에 하나의 read-only
`PromptKitClient`를 설정하고 등록합니다. LLM 호출, 프롬프트 생성·수정, 요청 재시도
또는 시작 단계의 registry 접속을 수행하지 않습니다. 캐시 재사용은 명시적 helper를
통해서만 제공하며 호스트 애플리케이션의 Django default cache backend를 사용합니다.

## 설치

Core SDK는 package index에 배포하지 않습니다. 저장소의 default branch에서 두
패키지를 하나의 명령으로 함께 설치합니다.

```bash
uv pip install \
  "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit" \
  "promptkit-django @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
```

`promptkit-django`만 설치하면 dependency resolver가 설정된 package index에서 현재
제공되지 않는 `promptkit`을 검색합니다. 두 Git subdirectory를 함께 전달하면 명시적으로
설치한 Core SDK가 `promptkit>=0.1,<0.2` dependency를 충족합니다. 이 URL들은 default
branch를 추적하므로 호환되는 version을 유지하려면 두 패키지를 함께 설치하거나
upgrade해야 합니다.

## Django 설정

Integration을 `INSTALLED_APPS`에 추가하고 API key는 호스트 프로젝트의 secret store
또는 환경 변수에 보관합니다.

```python
import os

INSTALLED_APPS = [
    # ...
    "promptkit_django",
]

PROMPTKIT = {
    "BASE_URL": "https://registry.example.com",
    "API_KEY": os.environ["PROMPTKIT_API_KEY"],
    "TIMEOUT": 10.0,
    "CACHE_TTL": 60.0,
}
```

`BASE_URL`과 `API_KEY`는 필수입니다. `TIMEOUT`은 선택 사항이며 기본값은 `10.0`입니다.
`CACHE_TTL`은 선택 사항이고 기본값은 `60.0`초이며 finite non-negative number여야
합니다. 양수 TTL은 해당 시간 동안 프롬프트를 fresh 상태로 유지하고, 동일한 길이의
validator revalidation 구간 동안 추가로 보존합니다. `0`은 PromptKit 캐시 읽기와 쓰기를
비활성화합니다. 이 uppercase key들만 허용합니다. 누락, 공백, 잘못된 타입, 안전하지
않은 값 또는 알 수 없는 설정이 있으면 API key 값을 노출하지 않고 설정 이름만
보고하며 application startup을 실패시킵니다.

## 등록된 client 사용

```python
from promptkit_django import get_client

prompt = get_client().fetch("support-reply")
```

`get_client()`는 Django startup 과정에서 등록한 단일 client를 반환합니다. Client를
lazy 방식으로 생성하지 않으며 integration이 없거나 initialization이 완료되지 않았으면
`PromptKitDjangoNotInitializedError`를 발생시킵니다.

## Opt-in 캐시 조회

호스트 애플리케이션의 표준 `CACHES["default"]` backend를 설정한 뒤 cache-aware
helper를 명시적으로 import합니다.

```python
from promptkit_django import clear_prompt_cache, fetch_cached

prompt = fetch_cached("support-reply", label="latest")
clear_prompt_cache("support-reply")  # 이 프롬프트의 모든 캐시 라벨을 무효화
clear_prompt_cache()  # PromptKit 소유 entry만 무효화
```

`fetch_cached()`는 uncached 조회와 동일한 `RetrievedPrompt`를 반환합니다. Freshness가
만료되면 ETag로 재검증하며 registry 오류 후에는 stale data를 제공하지 않습니다.
`get_client().fetch()`는 계속 uncached 방식으로 동작합니다. Cache key에는 API key나
authorization header가 포함되지 않으며, 캐시 장애가 발생하면 가능한 경우 registry를
조회합니다.
