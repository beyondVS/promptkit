# PromptKit Django Integration (`packages/promptkit-django`) Specification & Requirements

본 문서는 Django 백엔드 애플리케이션을 위한 통합 라이브러리인 **`packages/promptkit-django`**의 상세 기능 사양서입니다.

---

## 1. 개요 및 설계 원칙

`packages/promptkit-django`는 Django 웹 애플리케이션에서 코어 SDK(`packages/promptkit`)를 표준 설정 및 AppConfig lifecycle에 연결하고, 호스트 프로젝트의 Django Cache를 이용한 opt-in 조회 최적화를 제공하는 **공식 통합 라이브러리**이다.

### 핵심 설계 원칙
- **Standard Django Extension**: Django Settings 및 AppConfig 규격을 온전히 준수.
- **Pure SDK Extension**: `packages/promptkit` 패키지에만 단방향 의존하며 서버(`apps/server`) 내부 코드나 데이터베이스 모델에 직접 의존하지 않음.
- **Lifecycle-scoped Registration**: AppConfig 시작 단계에서 설정을 검증하고 하나의 `PromptKitClient`를 등록하며 lazy construction을 허용하지 않음.
- **Credential Safety**: 설정 오류에는 영향받은 key 이름만 포함하고 API key 값은 노출하지 않음.

---

## 2. 핵심 사양 및 요구사항

### 2.1 Django AppConfig & Settings 연동 (Configuration)
`PromptKitDjangoConfig` 앱이 구동될 때 `settings.py`의 단일 `PROMPTKIT` mapping을 검증하고 `PromptKitClient`를 자동 등록한다:

```python
PROMPTKIT = {
    "BASE_URL": "https://registry.example.com",
    "API_KEY": os.environ["PROMPTKIT_API_KEY"],
    "TIMEOUT": 10.0,
    "CACHE_TTL": 60.0,
}
```

- `BASE_URL`, `API_KEY`: 필수 non-blank 문자열
- `TIMEOUT`: 선택 positive finite number, 기본값 `10.0`
- `CACHE_TTL`: 선택 non-negative finite number(초), 기본값 `60.0`; `0`이면 캐시 읽기·쓰기·무효화를 모두 우회
- 알 수 없는 key, 누락·공백·잘못된 타입·안전하지 않은 URL은 애플리케이션 시작을 즉시 실패시킴
- `get_client()`는 시작 단계에서 등록된 동일 인스턴스를 반환하며 미설치·미초기화 상태에서는 integration-specific 오류를 발생시킴

### 2.2 Django Cache Layer & ETag 핸드셰이크 규격
- **Opt-in Entry Point**: `fetch_cached(slug, *, label=None)`만 캐시 계층을 사용한다. `get_client().fetch()`의 uncached 동작과 오류 계약은 변경하지 않는다.
- **Host Cache Backend**: 별도 backend를 만들지 않고 Django 프로젝트의 `CACHES["default"]`를 사용한다. backend 장애는 cache miss로 처리하되 원격 registry의 결과나 오류를 바꾸지 않는다.
- **Cache Identity**: 정규화한 비밀값 없는 registry base URL, 전역 유일 prompt slug, label의 생략 여부와 값을 canonicalize한 뒤 SHA-256 digest로 키를 만든다. API key와 인증 header는 키나 값에 포함하지 않는다.
- **Two-window TTL**: 저장 후 `CACHE_TTL` 동안은 네트워크 없이 fresh entry를 반환한다. backend에는 `2 × CACHE_TTL` 동안 보존하여 두 번째 동일 길이 구간에서만 조건부 재검증에 사용한다.
- **ETag Validation**: 서버는 직렬화된 조회 응답의 canonical JSON을 SHA-256으로 digest한 quoted strong ETag를 반환한다. stale entry는 이 값을 `If-None-Match`로 전송하며, `304 Not Modified`이면 freshness를 연장하고 `200 OK`이면 prompt와 ETag를 하나의 record로 교체한다.
- **Failure Semantics**: malformed cache entry는 miss이다. 재검증 중 registry 오류가 발생하면 해당 entry를 제거하고 오류를 그대로 전파하며 stale prompt로 fallback하지 않는다.
- **Invalidation**: `clear_prompt_cache(slug=None)`는 generation token을 사용해 전체 또는 특정 slug의 모든 label variant를 논리적으로 무효화한다. 다른 애플리케이션 캐시는 지우지 않으며 `cache.clear()`나 backend-specific pattern delete에 의존하지 않는다.

### 2.3 Django Helpers, Mixins & Template Tags (향후 확장 후보)
- **Class-Based View Mixin**: `PromptMixin`을 통한 CBV 내 프롬프트 자동 주입.
- **Template Tags**: Django 템플릿 내 직관적 조회 헬퍼:
  - `{% get_prompt "welcome-email" label="staging" as prompt %}`
  - `{% render_prompt "welcome-email" customer_name=user.username %}`

---

## 3. 독립 배포 및 설치 규격

코어 SDK를 패키지 인덱스에 배포하지 않는 현재 개발 정책에서는 기본 브랜치의 두 Git subdirectory를 함께 설치한다:

```bash
uv add \
  "promptkit @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit" \
  "promptkit-django @ git+https://github.com/beyondVS/promptkit.git#subdirectory=packages/promptkit-django"
```

두 패키지는 함께 설치·업그레이드한다. `promptkit-django`의 표준 metadata에는
`promptkit>=0.1,<0.2`가 유지되지만, 통합 패키지만 설치하면 resolver가 configured
package index에서 코어 SDK를 찾으므로 현재 정책에서는 실패한다.

배포 검증은 새 Core SDK wheel을 임시 wheelhouse에 제공하고 Django integration의 wheel과
local committed Git subdirectory 경로를 각각 새 uv 환경에 설치한다. 설치 후 repository
source path 없이 최소 Django `settings.configure()`·`django.setup()`과 단일 `get_client()`
등록을 확인한다. 또한 core-first와 integration-first의 두 요청 설치 순서가 동일한
`RetrievedPrompt.compile()` 결과와 호환 metadata를 제공해야 한다.
