# Phase 0 Research: Prompt Version(이력 관리 및 롤백) API 개발

**Feature**: [`spec.md`](./spec.md) | **Branch**: `006-prompt-version-api` | **Date**: 2026-07-30

## Research Decisions

### 1. Version Auto-Increment & Uniqueness Strategy

- **Decision**: `Version.version_number`는 동일 `Prompt` 내에서 `(Max('version_number') or 0) + 1` 수식으로 자동 부여하며, DB 레벨 `models.UniqueConstraint(fields=["prompt", "version_number"], name="unique_prompt_version_number")` 제약조건으로 고유성을 보장합니다.
- **Rationale**: 프롬프트별 독립적인 1, 2, 3... 순차 버전 번호 체계를 안정적으로 부여하며 데이터 경합 및 중복 발행을 DB 레벨에서 완벽하게 차단합니다.
- **Alternatives Considered**:
  - UUID 사용: 버전 식별용으로는 유용하나 사용자가 직관적으로 인식하는 순차 이력(v1, v2) 요구사항을 충족하지 못함.
  - 전역 Auto-Increment ID: 개별 프롬프트의 독립 버전 번호가 아닌 전체 DB의 순번이 되어 버그 유발.

### 2. Immutability (불변성) 보장 및 REST Endpoint 설계

- **Decision**: `VersionViewSet`은 `list` 및 `retrieve` 조회 기능만 제공하며, 기존 `Version` 레코드의 직접 수정(`PUT`/`PATCH`) 및 삭제(`DELETE`) 요청은 허용하지 않고 405 Method Not Allowed를 반환합니다. 신규 버전에 대한 스냅샷 생성은 `Prompt` 수정 트랜잭션 시 자동 처리되거나 `/api/v1/prompts/{prompt_id}/rollback/` 엔드포인트를 통해서만 수행됩니다.
- **Rationale**: 생성된 템플릿 스냅샷과 변경 이력을 불변(Immutable) 상태로 100% 보존하여 감사 및 복원 기능의 신뢰성을 보장합니다.
- **Alternatives Considered**:
  - Soft Delete / Update 허용: 과거 버전의 조작 및 훼손 가능성이 생겨 버전 관리 시스템의 원칙 위배.

### 3. Structured Line Diff 계산 엔진

- **Decision**: Python 표준 라이브러리인 `difflib`의 `ndiff` 알고리즘을 활용하여 비교 대상 두 버전의 템플릿 텍스트 라인별 차이점을 파싱하고, `[{"line": 1, "op": "equal" | "add" | "delete", "text": "..."}]` 형태로 구조화된 JSON 배열을 반환합니다.
- **Rationale**: 추가 의존성 라이브러리 설치 없이 Python 3.13+ 표준 유틸리티로 1.0초 이내의 초고속 Diff 연산을 보장하며, 프론트엔드 및 SDK에서 손쉽게 차이점을 렌더링할 수 있습니다.
- **Alternatives Considered**:
  - 외부 diff 패키지(예: `git-diff` binary): 별도 의존성 및 OS 실행환경 제약 발생.

### 4. 동일 템플릿 내용 업데이트 처리 (Skip Creation)

- **Decision**: `Prompt` 업데이트 시 전달된 `template_text`가 기존 최신 `Version`의 `template_text`와 100% 동일한 경우, 신규 `Version` 레코드를 생성하지 않고 기존 최신 버전을 그대로 유지 및 반환합니다.
- **Rationale**: 의미 없는 동일 내용의 중복 스냅샷 생성 및 DB 용량 낭비를 방지합니다.

### 5. 롤백(Rollback) 이력 관리 방식 (Append-Only)

- **Decision**: 과거 버전(v{target})으로의 롤백 요청 시, 과거 이력 레코드를 수정하거나 이후 버전을 삭제하지 않고 v{target}의 `template_text`를 복사하여 `version_number = latest + 1`인 신규 스냅샷 레코드를 발행합니다. `changelog`는 전달된 커스텀 사유 또는 `Rolled back to v{target_version}` 자동 문구로 저장됩니다.
- **Rationale**: 모든 변경 작업이 이력에 남는 Append-Only 구조를 유지하여 완전한 감사 추적성(Auditability)을 수호합니다.
