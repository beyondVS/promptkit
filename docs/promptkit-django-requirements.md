# PromptKit Django Integration (`packages/promptkit-django`) Specification & Requirements

본 문서는 Django 백엔드 애플리케이션을 위한 통합 라이브러리인 **`packages/promptkit-django`**의 상세 기능 사양서입니다.

---

## 1. 개요 및 설계 원칙

`packages/promptkit-django`는 Django 웹 애플리케이션에서 코어 SDK(`packages/promptkit`)를 표준 설정 및 AppConfig lifecycle에 연결하는 **공식 통합 라이브러리**이다. 현재 범위는 설정 검증과 SDK 인스턴스 자동 등록이며, Cache/ETag 기능은 Day 15 후속 범위이다.

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
}
```

- `BASE_URL`, `API_KEY`: 필수 non-blank 문자열
- `TIMEOUT`: 선택 positive finite number, 기본값 `10.0`
- 알 수 없는 key, 누락·공백·잘못된 타입·안전하지 않은 URL은 애플리케이션 시작을 즉시 실패시킴
- `get_client()`는 시작 단계에서 등록된 동일 인스턴스를 반환하며 미설치·미초기화 상태에서는 integration-specific 오류를 발생시킴

### 2.2 Django Cache Layer & ETag 핸드셰이크 규격 (Day 15 예정)
- **Cache Key Naming**: `promptkit:prompt:<slug>:<label>` 형식의 캐시 키 포맷.
- **Cache Lookup Flow**: 프롬프트 조회 요청 시 먼저 Django Cache 백엔드 조회.
- **ETag Validation**: `If-None-Match: "W/<slug>-v<ver>-r<rev>"` 헤더를 전송하여 서버 변경 여부를 검증하고, `304 Not Modified` 수신 시 캐시된 프롬프트 즉시 반환.
- **Automatic & Manual Invalidation**: TTL 만료 시 자동 갱신 및 `clear_prompt_cache(slug=None)` 헬퍼를 통한 수동 캐시 초기화 지원.

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
