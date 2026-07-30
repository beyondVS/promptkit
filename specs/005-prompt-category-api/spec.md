# Feature Specification: PromptCategory(도메인 범주) 독립 모델링 및 관리 API 개발

**Feature Branch**: `005-prompt-category-api`

**Created**: 2026-07-30

**Status**: Draft

**
## Clarifications

### Session 2026-07-30

- Q: 프롬프트가 연결된 카테고리의 삭제 시 ON DELETE 처리 방식 → A: Restrict/Protect (연결된 프롬프트가 1개 이상 존재하는 경우 카테고리 삭제를 거부하고 409 Conflict 오류를 반환하여 데이터 무결성을 보호함).
- Q: 프롬프트 작성 시 카테고리 지정 필수 여부 (Nullability) → A: Mandatory (프롬프트 생성 및 수정 시 반드시 유효한 PromptCategory가 지정되어야 하며 미지정 시 400 Bad Request 유효성 에러를 반환함).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PromptCategory(도메인 카테고리) 엔티티 CRUD 관리 (Priority: P1)

관리자 및 사용자 시스템은 기존의 무정규화된 단일 문자열 `task` 필드 대신, 프롬프트의 도메인 범주(예: 고객지원, 코드 생성, 요약, 번역 등)를 체계적으로 관리할 수 있는 독립 엔티티인 `PromptCategory`를 생성, 조회, 수정, 삭제(CRUD)할 수 있어야 한다.

**Why this priority**: 도메인 범주(Category) 데이터를 정규화된 엔티티로 관리할 수 있어야 프롬프트와의 관계 매핑 및 일관성 있는 범주 관리가 가능하므로 최우선 순위(P1)를 지닌다.

**Independent Test**: API를 통해 신규 도메인 카테고리(이름, 슬러그, 설명 등)를 등록하고 상세 조회, 전체 목록 조회, 수정, 삭제 후 정상 반영되는지 독립적으로 검증할 수 있다.

**Acceptance Scenarios**:

1. **Given** 카테고리 이름(Name), 영문 슬러그(Slug), 설명(Description) 데이터가 주어졌을 때, **When** 카테고리 생성 요청을 보내면, **Then** 고유 식별자(ID)가 부여된 신규 PromptCategory 정보가 반환된다.
2. **Given** 기존에 등록된 카테고리가 존재할 때, **When** 카테고리 목록 조회를 요청하면, **Then** 전체 도메인 카테고리 목록이 표시 순서 및 생성일시 기준 정렬되어 반환된다.
3. **Given** 기존 카테고리의 정보(이름 또는 설명)를 변경하려 할 때, **When** 카테고리 수정 요청을 전송하면, **Then** 업데이트된 카테고리 메타데이터가 응답으로 반환된다.
4. **Given** 프롬프트에 연결되지 않은 카테고리가 존재할 때, **When** 해당 카테고리 삭제를 요청하면, **Then** 성공적으로 삭제 처리되어 이후 조회되지 않는다.

---

### User Story 2 - Prompt와 PromptCategory 간 매핑 관계 구축 및 검색 API 개선 (Priority: P2)

기존 `Prompt` 모델의 단순 문자열 `task` 필드를 독립된 `PromptCategory`와의 외래키(ForeignKey) 관계 매핑으로 전환하고, 프롬프트 검색 및 등록 API에서 카테고리 식별자/슬러그 기반의 정밀 검색을 지원해야 한다.

**Why this priority**: 정규화된 카테고리 모델을 기반으로 프롬프트를 분류하고 필터링함으로써 다차원 검색의 정합성과 데이터 무결성을 보장할 수 있다.

**Independent Test**: 특정 카테고리에 속한 프롬프트를 등록하고, 해당 카테고리 ID 또는 슬러그를 검색 조건으로 지정하여 검색 API를 호출했을 때 정확히 대상 프롬프트들만 필터링되는지 독립 검증이 가능하다.

**Acceptance Scenarios**:

1. **Given** 등록된 PromptCategory가 존재할 때, **When** 해당 카테고리 ID를 연결하여 신규 Prompt를 생성하면, **Then** 프롬프트 상세 조회 시 정규화된 카테고리 객체 정보가 올바르게 매핑되어 반환된다.
2. **Given** 특정 카테고리(예: '고객지원')에 연결된 프롬프트들이 존재할 때, **When** 카테고리 식별자 또는 슬러그 조건으로 프롬프트 검색을 요청하면, **Then** 해당 카테고리에 속한 프롬프트 목록만 필터링되어 반환된다.
3. **Given** 기존에 단순 문자열 `task` 필드로 검색하던 외부 요청이 입력되었을 때, **When** 기존 문자열 검색 파라미터를 전송하더라도, **Then** 해당 task 문자열에 상응하는 PromptCategory를 매핑 검색하거나 하위 호환성을 유지하여 결과를 반환한다.

---

### User Story 3 - 카테고리별 연결 프롬프트 통계 및 유닛 테스트 검증 (Priority: P3)

카테고리 관리 효율성을 높이기 위해 카테고리 목록 조회 시 각 카테고리에 연결된 프롬프트 수(Prompt Count) 정보를 제공하고, 전체 CRUD 및 관계 매핑/검색 개선에 대한 유닛 테스트 세트를 구동하여 무결성을 보장해야 한다.

**Why this priority**: 카테고리별 사용 현황 파악을 돕고, 기존 시스템 코드베이스와의 호환성을 포함한 100% 자동화 테스트로 시스템 안정성을 유지하기 위함이다.

**Independent Test**: 유닛 테스트 도구를 구동하여 Category CRUD, Prompt-Category 관계 매핑, 카테고리별 프롬프트 필터링 검색 테스트가 100% 통과하는지 검증한다.

**Acceptance Scenarios**:

1. **Given** 각 카테고리에 속한 프롬프트들이 등록되어 있을 때, **When** 카테고리 목록 조회를 요청하면, **Then** 각 카테고리 항목별 소속 프롬프트 수(Count) 메타데이터가 포함되어 응답된다.
2. **Given** Category CRUD 및 Prompt-Category 매핑/검색 API 유닛 테스트 세트가 준비되었을 때, **When** 유닛 테스트 구동 시, **Then** 모든 케이스가 오류 없이 정상 통과한다.

---

### Edge Cases

- 이미 존재하는 카테고리 이름(Name) 또는 식별 슬러그(Slug)로 신규 카테고리를 생성하거나 수정 시 중복 등록 오류(400 Bad Request 또는 409 Conflict)를 반환한다.
- 프롬프트 등록/수정 시 존재하지 않는 Category ID를 참조 전달할 경우 리소스 부재 유효성 에러(400 Bad Request / 404 Not Found)를 반환한다.
- 프롬프트가 1개 이상 연결되어 있는 카테고리를 삭제 요청 시, 무단 참조 삭제 방지를 위해 삭제 불가 오류(400 Bad Request / 409 Conflict)를 반환한다.
- 프롬프트 등록/수정 시 카테고리를 지정하지 않거나(Null/Empty) 유효하지 않은 카테고리를 입력할 경우 400 Bad Request 유효성 오류를 반환한다.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 시스템은 독립적인 도메인 범주 모델인 `PromptCategory` 엔티티를 제공해야 한다.
- **FR-002**: 시스템은 `PromptCategory`의 신규 등록, 상세 조회, 목록 조회, 수정, 삭제(CRUD)를 위한 API 엔드포인트를 제공해야 한다.
- **FR-003**: `PromptCategory` 엔티티는 이름(Name) 및 고유 영문 슬러그(Slug)의 고유성(Uniqueness)을 검증 및 보장해야 한다.
- **FR-004**: 시스템은 `Prompt` 모델과 `PromptCategory` 모델 간의 정규화된 외래키(ForeignKey) 관계 매핑(1:N)을 구축해야 한다.
- **FR-005**: 시스템은 프롬프트 생성 및 수정 시 유효한 `PromptCategory` 지정을 필수(Mandatory)로 연동해야 하며 미지정 시 유효성 에러를 반환해야 한다.
- **FR-006**: 시스템은 `PromptCategory` 식별자(ID) 또는 슬러그(Slug) 기반의 프롬프트 목록 필터링 검색 API를 제공해야 한다.
- **FR-007**: 시스템은 기존 단순 문자열 `task` 필드 요청에 대한 마이그레이션 방안 및 검색 하위 호환성 매핑을 제공해야 한다.
- **FR-008**: 시스템은 카테고리 목록 조회 시 각 카테고리에 매핑된 프롬프트 개수(Prompt Count) 정보를 함께 응답할 수 있어야 한다.
- **FR-009**: 모든 카테고리 CRUD API 및 카테고리 기반 프롬프트 검색/매핑 기능은 자동화된 유닛 테스트 케이스를 통해 100% 검증되어야 한다.

### Key Entities

- **PromptCategory (도메인 카테고리)**:
  - 프롬프트가 속한 업무 도메인 및 범주를 표현하는 정규화된 독립 엔티티.
  - 주요 속성: 고유 식별자(ID), 카테고리 이름(Name), 식별용 영문 슬러그(Slug), 상세 설명(Description), 표시 순서(Display Order), 활성화 여부(Is Active), 생성일시, 수정일시.
  - 관계: 여러 Prompt에 참조될 수 있음 (1:N 관계).

- **Prompt (프롬프트 - 개정)**:
  - 기존 단순 문자열 `task` 필드가 `PromptCategory` 외래키 참조(category)로 정규화 교체/확장됨.
  - 주요 속성: 고유 식별자, 이름(Name), 설명(Description), 카테고리 참조(Category FK, Mandatory), 태그 목록(Tags), 생성일시, 수정일시.
  - 관계: 필수적으로 하나의 PromptCategory에 속함 (1:N 관계의 필수 참조).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PromptCategory 엔티티의 CRUD 기능이 명세대로 작동하여 100% 정상 API 응답을 보장한다.
- **SC-002**: 프롬프트-카테고리 간 외래키 매핑 및 카테고리 ID/슬러그 기반 필터링 검색 결과의 정합성이 100% 일치한다.
- **SC-003**: 작성된 유닛 테스트 세트 실행 시 모든 카테고리 관리 및 관계 매핑/검색 테스트 케이스가 100% 통과한다.
- **SC-004**: 카테고리별 프롬프트 수 집계 및 목록 조회가 지연 없이(1초 이내) 즉각 처리된다.

## Assumptions

- 기존 `task` 문자열 필드는 데이터베이스 마이그레이션을 통해 상응하는 `PromptCategory` 레코드로 자동 전환되거나, `category` 외래키 필드로 맵핑 정규화된다.
- 한 프롬프트는 기본적으로 1개의 `PromptCategory`에 속하는 1:N 단일 카테고리 구조를 타겟으로 설정한다.
- 카테고리 관리 API 엔드포인트의 접근 통제는 기존 프롬프트 서버의 권한 및 인증 모듈 정책을 공유한다.
