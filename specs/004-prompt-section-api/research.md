# Research: Prompt & Section CRUD 및 다차원 검색 API

## Technical Decisions & Tradeoffs

### Decision 1: 다차원 검색 (Multidimensional Search) ORM 구현 방식

- **Chosen Approach**: Django ORM `Q` 객체 조합 및 `django-filter` / DRF `filterset_class` 기반 동적 쿼리 빌더
- **Rationale**:
  - 이름(Name) 키워드는 `icontains` (대소문자 구분 없는 부분 일치) 적용.
  - 업무(Task)는 exact match 적용.
  - 복수 태그(Tags)는 요청된 모든 태그를 포함해야 하는 AND 매칭 적용.
- **Alternatives Considered**:
  - *Full-Text Search (PostgreSQL `SearchVector`)*: 단순 태그/이름/업무 조건 키워드 필터링에는 오버헤드가 크고 태그 엄격 매칭(AND)에 불필요한 복잡성 유발.
  - *Raw SQL Query*: ORM 데이터 보안 및 유지보수성을 낮춤.

---

### Decision 2: 태그(Tags) 데이터 구조 및 AND 필터링 기법

- **Chosen Approach**: `JSONField` (또는 `ArrayField`) 기반 태그 리스트 저장 및 ORM `.filter()` 체이닝 / `Q` 객체 AND 조합
- **Rationale**:
  - 태그 목록을 JSON 배열(`['summary', 'v1']`)로 유지하고, 요청된 복수 태그 `t1, t2`에 대해 `.filter(tags__contains=t1).filter(tags__contains=t2)` 형태로 체이닝하면 Django ORM 레벨에서 완벽한 AND 조건 필터링 수행 가능.
  - 데이터베이스 종속성을 최소화하여 SQLite/PostgreSQL 모두 호환 가능.
- **Alternatives Considered**:
  - *M2M Tag Model (별도 Tag 테이블)*: 단순 프롬프트 태그 관리에 조인 오버헤드가 발생하고 가벼운 SDK 레지스트리 원칙(Constitution 원칙 V)에 비해 복잡함.

---

### Decision 3: Prompt 및 Section CRUD API 엔드포인트 설계

- **Chosen Approach**: Django REST Framework (DRF) `ModelViewSet` 및 `Nested/Sub-resource Routing`
- **Rationale**:
  - `/api/v1/prompts/` : 프롬프트 목록 조회(검색), 생성, 상세 조회, 수정, 삭제
  - `/api/v1/prompts/{prompt_id}/sections/` 또는 `/api/v1/sections/` : 섹션 목록 및 CRUD
  - 프롬프트 상세 조회 시 포함된 섹션 목록을 직렬화(Serializer)하여 한 번에 반환하는 중첩 직렬화 지원.
- **Alternatives Considered**:
  - *단일 거대 JSON 필드로 섹션 저장*: 섹션별 독립 수정 및 순서(Order) 제어가 어려움.

---

### Decision 4: 프롬프트 이름 고유성(Uniqueness) 및 검증 오류 처리

- **Chosen Approach**: `Prompt` 모델 `name` 필드에 `unique=True` 또는 `UniqueConstraint` 부여, DRF Serializer 레벨 validation 및 HTTP `400 Bad Request` / `409 Conflict` 예외 응답 처리.
- **Rationale**:
  - 데이터베이스 수준의 무결성을 수호하며 유효하지 않은 이름 중복 요청을 사전에 차단.
