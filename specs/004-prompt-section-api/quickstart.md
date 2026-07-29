# Quickstart Validation Guide: Prompt & Section CRUD 및 다차원 검색 API

본 가이드는 `004-prompt-section-api` 기능 개발 완료 후 시스템의 주요 시나리오를 기계적으로 검증하기 위한 가이드입니다.

---

## 1. 사전 준비 및 환경 구성

의존성 패키지를 동기화하고 데이터베이스 마이그레이션을 적용합니다.

```bash
# 의존성 동기화
uv sync

# Django 데이터베이스 마이그레이션 적용
uv run python apps/server/manage.py migrate
```

---

## 2. 하네스 자동화 검증 (Linting & Testing)

헌법 원칙에 명시된 하네스 명령어를 순서대로 실행하여 코드 스타일, 타입, 유닛 테스트 통과 여부를 검증합니다.

```bash
# 린트 및 포맷팅, 타입 검사
uv run ruff check ; uv run ruff format ; uv run mypy .

# Prompt & Section CRUD 및 다차원 검색 유닛 테스트 구동
uv run pytest apps/server/prompts/
```

---

## 3. 검증 시나리오 (Verification Scenarios)

### Scenario A: 프롬프트 & 섹션 생성 및 상세 조회 (CRUD)

1. **프롬프트 생성**:
   - `POST /api/v1/prompts/`
   - Body: `{"slug": "support-agent", "name": "고객 상담 AI 프롬프트", "task": "customer-support", "tags": ["v1", "support"]}`
   - **기대 결과**: HTTP 201 Created, 생성된 프롬프트 ID 반환.

2. **프롬프트 이름 중복 생성 시도**:
   - `POST /api/v1/prompts/`
   - Body: `{"slug": "another-slug", "name": "고객 상담 AI 프롬프트"}`
   - **기대 결과**: HTTP 400 Bad Request 또는 409 Conflict 오류 반환 (이름 고유성 제약 검증).

3. **섹션 추가**:
   - `POST /api/v1/prompts/{prompt_id}/sections/`
   - Body: `{"role": "system", "order": 1, "content": "당신은 친절한 고객 상담원입니다."}`
   - **기대 결과**: HTTP 201 Created, 섹션 생성 완료.

4. **상세 조회**:
   - `GET /api/v1/prompts/{prompt_id}/`
   - **기대 결과**: HTTP 200 OK, 섹션 목록이 포함된 프롬프트 반환.

---

### Scenario B: 이름, 태그, 업무 기반 다차원 검색 (Multidimensional Search)

1. **이름 부분 검색**:
   - `GET /api/v1/prompts/?name=고객`
   - **기대 결과**: 이름에 '고객'이 포함된 프롬프트 목록 반환.

2. **업무 분류 검색**:
   - `GET /api/v1/prompts/?task=customer-support`
   - **기대 결과**: `customer-support` 업무 프롬프트만 반환.

3. **복수 태그 AND 검색**:
   - `GET /api/v1/prompts/?tags=v1&tags=support`
   - **기대 결과**: `v1`과 `support` 두 태그를 **모두** 지닌 프롬프트만 정확히 반환.

4. **다차원 조합 검색 (Name + Task + Tags)**:
   - `GET /api/v1/prompts/?name=고객&task=customer-support&tags=v1`
   - **기대 결과**: 모든 필터링 조건(AND)을 만족하는 프롬프트 집합 반환.
