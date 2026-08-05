# PromptKit Django Integration (`packages/promptkit-django`) Specification & Requirements

본 문서는 Django 백엔드 애플리케이션을 위한 통합 라이브러리인 **`packages/promptkit-django`**의 상세 기능 사양서입니다.

---

## 1. 개요 및 설계 원칙

`packages/promptkit-django`는 Django 웹 애플리케이션에서 코어 SDK(`packages/promptkit`)를 한 줄의 설정으로 손쉽게 연동하고, Django Cache 백엔드를 통해 프롬프트 원격 조회 성능을 극대화해 주는 **공식 통합 라이브러리**이다.

### 핵심 설계 원칙
- **Standard Django Extension**: Django Settings, Cache Framework 및 AppConfig 규격을 온전히 준수.
- **Pure SDK Extension**: `packages/promptkit` 패키지에만 단방향 의존하며 서버(`apps/server`) 내부 코드나 데이터베이스 모델에 직접 의존하지 않음.
- **High-Performance Caching**: Django Cache(LocMem, Redis, Memcached) 연동 및 ETag 기반 `304 Not Modified` 검증을 통한 네트워크 부하 최소화.

---

## 2. 핵심 사양 및 요구사항

### 2.1 Django AppConfig & Settings 연동 (Configuration)
`PromptKitDjangoConfig` 앱이 구동될 때 `settings.py` 내의 환경변수 및 설정을 검증하고 `PromptKitClient` 싱글톤 자동 생성:

```python
PROMPTKIT_SERVER_URL = "http://localhost:8000"
PROMPTKIT_API_KEY = os.getenv("PROMPTKIT_API_KEY")
PROMPTKIT_CACHE_TTL = 300  # 캐시 유지 시간 (초, 기본값: 300)
```

### 2.2 Django Cache Layer & ETag 핸드셰이크 규격
- **Cache Key Naming**: `promptkit:prompt:<slug>:<label>` 형식의 캐시 키 포맷.
- **Cache Lookup Flow**: 프롬프트 조회 요청 시 먼저 Django Cache 백엔드 조회.
- **ETag Validation**: `If-None-Match: "W/<slug>-v<ver>-r<rev>"` 헤더를 전송하여 서버 변경 여부를 검증하고, `304 Not Modified` 수신 시 캐시된 프롬프트 즉시 반환.
- **Automatic & Manual Invalidation**: TTL 만료 시 자동 갱신 및 `clear_prompt_cache(slug=None)` 헬퍼를 통한 수동 캐시 초기화 지원.

### 2.3 Django Helpers, Mixins & Template Tags
- **Class-Based View Mixin**: `PromptMixin`을 통한 CBV 내 프롬프트 자동 주입.
- **Template Tags**: Django 템플릿 내 직관적 조회 헬퍼:
  - `{% get_prompt "welcome-email" label="staging" as prompt %}`
  - `{% render_prompt "welcome-email" customer_name=user.username %}`

---

## 3. 독립 배포 및 설치 규격

모노레포 내에서 완전히 격리되어 Git Subdirectory 방식으로 독립 설치 가능해야 함:

```bash
pip install "git+https://github.com/<org>/promptkit.git#subdirectory=packages/promptkit-django"
```
