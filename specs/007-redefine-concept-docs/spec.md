# Feature Specification: promptkit 프로젝트 컨셉 재정의 및 문서화

**Feature Branch**: `007-redefine-concept-docs`

**Created**: 2026-07-31

**Status**: Draft

**Input**: User description: "# [Feature Spec] promptkit 프로젝트 컨셉 재정의 및 문서화..."

## Clarifications

### Session 2026-07-31

- Q: 대시보드 관리자 인증/인가 방식 → A: Django 내장 Auth (Session / Standard User Model / Django Form & LoginView)
- Q: SDK 프롬프트 조회 API 인증 전달 방식 → A: Custom HTTP Header (`X-PromptKit-Api-Key: <key>`) 방식

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 프롬프트 관리자의 Django 대시보드를 통한 프롬프트 CUD 및 독립 인증 (Priority: P1)

프롬프트 관리자는 SDK API Key와 분리된 Django 내장 Session Auth 전용 인증/인가 체계를 통해 Django Template 대시보드에 로그인하여 프롬프트를 생성, 수정, 삭제(CUD)하고 버전을 관리할 수 있어야 한다.

**Why this priority**: 프롬프트 생성/수정/삭제 기능이 SDK에서 제외되므로 대시보드가 중앙 관리의 유일한 창구가 된다. 또한 관리자 접근 통제는 서비스 보안의 핵심이다.

**Independent Test**: 대시보드 로그인 후 프롬프트를 신규 등록하고 수정/삭제할 수 있으며, SDK 접속용 `PROMPTKIT_API_KEY`로는 대시보드에 로그인하거나 접근할 수 없음을 독립 검증할 수 있다.

**Acceptance Scenarios**:

1. **Given** 등록된 대시보드 관리자 계정이 있을 때, **When** 대시보드 로그인 페이지에서 Django Session Auth 자격증명으로 로그인하면, **Then** 프롬프트 목록 및 CUD 대시보드 화면에 성공적으로 접근한다.
2. **Given** Valid한 SDK 전용 `PROMPTKIT_API_KEY`가 있을 때, **When** 해당 키로 대시보드 로그인/관리 페이지 진입을 시도하면, **Then** 접근이 거부된다.
3. **Given** 로그인된 관리자가 대시보드에 있을 때, **When** 신규 프롬프트를 작성하여 저장하면, **Then** 해당 프롬프트가 버전과 함께 중앙 레지스트리에 저장된다.

---

### User Story 2 - Application Developer의 SDK를 통한 Read-only 프롬프트 조회 (Priority: P2)

애플리케이션 개발자는 `promptkit-sdk`를 통해 `X-PromptKit-Api-Key` HTTP 헤더 인증을 거쳐 `promptkit-server`로부터 필요한 프롬프트를 조회(Read-only)하고 컴파일할 수 있으며, SDK 내에 CUD 관련 기능은 노출되지 않는다.

**Why this priority**: 외부 애플리케이션과의 연동 인터페이스를 안정화하고, 잘못된 프롬프트 변조 시도를 차단하기 위해 SDK 역할을 Read-only로 한정한다.

**Independent Test**: SDK 파이썬 패키지를 사용하여 API Key 인증 헤더를 통해 프롬프트를 조회(Fetch)할 수 있고, 생성/수정/삭제 등의 CUD 메서드가 제공되지 않음을 검증한다.

**Acceptance Scenarios**:

1. **Given** `X-PromptKit-Api-Key` 헤더가 설정된 SDK 클라이언트가 있을 때, **When** 등록된 프롬프트 조회를 요청하면, **Then** 서버로부터 최신 프롬프트 내용 및 라벨 정보를 성공적으로 반환받는다.
2. **Given** SDK 사용자가 프롬프트 생성/수정을 시도하고자 할 때, **When** SDK 인터페이스를 확인하면, **Then** CUD 관련 API 호출 메서드가 존재하지 않는다.

---

### User Story 3 - 프로젝트 핵심 문서 및 일정 로드맵 최신화 (Priority: P3)

개발자와 에이전트가 재정의된 아키텍처와 경계 규칙을 명확히 이해하고 따를 수 있도록 constitution, AGENTS.md, README.md, docs 디렉토리 내 문서 및 project_plan.md 일정을 갱신한다.

**Why this priority**: 프로젝트 거버넌스 및 온보딩/에이전트 가이드라인의 정합성을 유지하여 향후 커뮤니케이션 오류를 방지한다.

**Independent Test**: 최신화된 문서를 검토하여 변경된 컨셉(대시보드 CUD, SDK Read-only, 인증 분리)이 일관되게 반영되어 있는지 확인한다.

**Acceptance Scenarios**:

1. **Given** 재정의된 컨셉이 확정되었을 때, **When** 핵심 문서(`constitution.md`, `AGENTS.md`, `README.md`, `docs/*.md`)를 확인하면, **Then** 대시보드 CUD 및 SDK Read-only 가이드라인이 명시되어 있다.
2. **Given** `docs/project_plan.md` 파일이 있을 때, **When** 마일스톤 및 미완료 일정을 조회하면, **Then** 변경된 역할 분담에 맞는 최신 작업 항목이 반영되어 있다.

---

### Edge Cases

- 대시보드 관리용 내부 API로 SDK가 접근을 시도하는 경우 권한 없음(401/403) 오류가 발생해야 함.
- SDK 조회가 실패(서버 장애, 잘못된 API Key)했을 경우 SDK 내부의 적절한 예외 처리 및 폴백 메커니즘 동작 확인.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `promptkit-server`는 Django Template 기반의 웹 대시보드 화면을 제공해야 한다.
- **FR-002**: 대시보드는 프롬프트 등록, 수정, 삭제(CUD) 및 버전/라벨 관리 기능을 제공해야 한다.
- **FR-003**: 대시보드 관리자 인증/인가 체계는 Django 내장 Session Auth(User Model, Form)를 기반으로 구축하며, SDK 프롬프트 조회용 API Key 인증과 물리적/논리적으로 엄격히 분리되어야 한다.
- **FR-004**: `promptkit-server`가 외부에 공개하는 REST API는 `promptkit-sdk`의 프롬프트 조회(Read-only) 전용 엔드포인트로 제한되며, `X-PromptKit-Api-Key` Custom HTTP Header를 통해 인증을 수행한다.
- **FR-005**: `promptkit-sdk`는 프롬프트를 가져오는(Fetch/Read) 기능만 포함하며, 프롬프트 생성·수정·삭제 메서드를 일절 포함하지 않아야 한다.
- **FR-006**: 재정의된 아키텍처 및 역할(대시보드 CUD, SDK Read-only, 인증 분리)에 맞게 `constitution.md`, `AGENTS.md`, `README.md`, `docs/*.md` 문서의 내용이 업데이트되어야 한다.
- **FR-007**: `docs/project_plan.md` 내 미완료 일정 및 로드맵이 새로운 컨셉에 맞추어 업데이트되어야 한다.

### Key Entities

- **Prompt**: 관리자가 대시보드에서 등록/수정/삭제하고, SDK가 조회하는 대상 프롬프트 (이름, 내용, 버전, 라벨 등 포함).
- **Dashboard Admin User**: 대시보드에 로그인하여 프롬프트를 관리할 수 있는 권한을 가진 Django User 계정.
- **SDK API Key (`PROMPTKIT_API_KEY`)**: SDK 클라이언트가 `X-PromptKit-Api-Key` 헤더로 프롬프트 조회 API 요청 시 제시하는 인증 토큰.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 대시보드를 통한 프롬프트 CUD 작업 시 처리 성공률 100% 달성.
- **SC-002**: `promptkit-sdk` 사용 시 프롬프트 조회 이외의 CUD API 호출 시도가 불가능하도록 인터페이스 100% 격리.
- **SC-003**: SDK API Key를 사용한 대시보드 접근 시도가 100% 차단됨 (0% 무단 접근 성공률).
- **SC-004**: 핵심 문서 4종(`constitution.md`, `AGENTS.md`, `README.md`, `docs/*.md`) 및 `project_plan.md`가 새 아키텍처 사양과 100% 일치하도록 갱신 완료.

## Assumptions

- 대시보드 인증 체계는 Django 기본 Session Auth 및 User 모델을 활용하여 구현된다.
- SDK와 서버 간 프롬프트 조회 API 인증은 `X-PromptKit-Api-Key` 커스텀 HTTP 헤더를 통해 이루어진다.
- 외부 애플리케이션은 LLM 직접 호출을 위해 `promptkit-sdk`를 통해 프롬프트를 조회한 후 자체적으로 LLM API를 호출한다 (Prompt Registry 원칙 유지).
- 기존 데이터 모델의 스키마는 대시보드 CUD와 SDK 조회를 모두 지원하는 방향으로 유지 및 호환된다.
