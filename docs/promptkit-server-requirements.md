# Prompt Server Specification & Requirements

본 문서는 PromptKit의 백엔드 하위 시스템인 **Prompt Server (`apps/server`)**의 상세 기능 사양서입니다.

---

## 1. 개요 및 개발 목적

Prompt Server는 애플리케이션 프롬프트 자산을 중앙에서 저장, 관리, 버저닝 및 서빙하는 **Prompt Registry**이다.

### 1.1 개발 목적 (Core Goals)
- **비즈니스 로직과 프롬프트의 분리**: 프롬프트를 소스 코드와 격리하여 중앙 레지스트리에서 독립적으로 관리.
- **애플리케이션 재배포 제거**: 프롬프트 수정 및 배포 시 비즈니스 애플리케이션의 재배포 없이 즉시 반영.
- **안전한 버전 및 배포 관리**: 초안 작성, 템플릿 변수 검증, 불변(Immutable) 발행 및 On-live 배포 대상의 안전한 제어.
- **LLM 공급자 독립성**: 특정 LLM Provider(OpenAI, Gemini, Claude 등)에 종속되지 않는 프롬프트 메타데이터 및 컴파일 환경 제공.

### 1.2 핵심 설계 원칙
- **LLM Gateway 배제**: 서버는 LLM을 직접 호출하거나 실행을 대행하지 않으며 오직 프롬프트 데이터와 배포 메타데이터만 관리한다.
- **분리된 접근 경계**:
  - **대시보드 (`/dashboard/`)**: 프롬프트 생성, 수정, 삭제(CUD), 버전 관리, On-live/라벨 지정 (Django Session Auth 및 CSRF 보호)
  - **SDK Read API (`/api/v1/prompts/<slug>/`)**: 외부 SDK 전용 Read-only 조회 (`X-PromptKit-Api-Key` 헤더 검증)

---

## 2. 도메인 엔티티 사양 & DB 제약조건

### 2.1 PromptCategory & Prompt
- `PromptCategory`: 프롬프트를 분류하는 독립 도메인 범주 (이름/슬러그 고유)
- `Prompt`: 프롬프트 메타데이터 (이름, 슬러그, 카테고리, 설명)
  - `name`은 동일 카테고리 내에서 고유 (`UniqueConstraint(category, name)`)
  - `slug`는 전체 서버에서 글로벌 고유 (`unique=True`)

### 2.2 Version & Section & Variable
- `Version`: 프롬프트의 변경 이력 단위
  - `status`: `draft` (초안, 편집 가능) 또는 `published` (발행 완료, 편집/삭제 불가)
  - `is_on_live`: 해당 프롬프트의 단일 활성 배포 대상 여부 (발행 버전에만 지정 가능, `on_live_must_be_published` DB 제약)
  - `revision`: 낙관적 동시성 제어(Optimistic Locking)를 위한 카운터. 수정 시마다 자동 증가하며 충돌 시 `StaleRevisionError` (409 Conflict) 발생.
  - `UniqueConstraint(prompt, version_number)`: 동일 프롬프트 내 버전 번호 중복 금지.
- `Section`: 프롬프트를 구성하는 메시지 블록
  - `role`: `system`, `user`, `assistant`
  - `UniqueConstraint(version, order)`: 동일 버전 내 섹션 순서 중복 금지.
- `VariableDefinition`: 템플릿 내 `{{ variable_name }}` 변수 정의
  - `var_type`: `string`, `number`, `boolean`, `json` 4가지 데이터 타입 지원.
  - `UniqueConstraint(version, name)`: 동일 버전 내 변수명 중복 금지.
  - **참조 데이터 무결성 (Referential Integrity)**: 템플릿 섹션 내에서 참조 중인 변수는 삭제할 수 없으며 삭제 시도 시 오류 발생.

### 2.3 Label
- 발행 버전(Published Version)에 부여할 수 있는 태그/식별자
- `latest`: 마지막 발행 버전을 자동 가리키는 시스템 예약 라벨
- `production`: 예약을 전면 금지하며 `prohibit_production_label` DB 제약조건으로 차단.

---

## 3. 대시보드 CUD & API 기능 사양

### 3.1 Prompt Management Flow
1. **프롬프트 생성**: 프롬프트 생성 시 initial `v1` 빈 초안(Draft) 자동 포함.
2. **초안 편집**: 섹션 CUD 및 변수 CUD 수행 (변수명 변경 시 섹션 템플릿 내 참조 자동 치환).
3. **버전 발행 (Publish)**: 템플릿 변수 검증 수행 후 불변(Immutable) 상태로 전환 및 `latest` 라벨 갱신.
4. **버전 복제 (Clone)**: 임의의 초안/발행 버전을 복사하여 독립적인 신규 초안 생성.
5. **On-live 지정**: 특정 발행 버전을 On-live 배포 대상으로 전환 (`is_on_live=True`).

### 3.2 대시보드 검색 및 필터링 (Dashboard Search API)
- `GET /dashboard/prompts/?category=<slug>&search=<query>`
- 대시보드 목록 보기 시 카테고리 필터링 및 프롬프트 이름/슬러그/설명 키워드 검색 지원.

### 3.3 SDK Read-Only API Boundary
- `GET /api/v1/prompts/<slug>/`
- Header: `X-PromptKit-Api-Key: <PROMPTKIT_API_KEY>`
- Query Parameter: `?label=<label_name>` (생략 시 On-live 지정 버전 반환)
- On-live 버전 미존재 시 `404 no_deployable_version` 반환.
- 상세한 JSON 응답 스키마, ETag 조건부 캐싱 및 HTTP 응답 코드 사양은 [sdk-read-api-contract.md](sdk-read-api-contract.md) 계약 문서를 참조하십시오.