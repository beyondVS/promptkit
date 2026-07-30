# Phase 0 Research: PromptCategory 독립 모델링 및 관리 API 개발

**Feature**: [`spec.md`](./spec.md) | **Branch**: `005-prompt-category-api` | **Date**: 2026-07-30

## Technical Decisions & Analysis

### 1. PromptCategory ORM 모델 정의 및 관계 매핑 (ORM Model & Relationships)

- **Decision**: `apps/server/prompts/models.py`에 `PromptCategory` 독립 ORM 모델을 추가하고, `Prompt` 모델과의 관계를 1:N 외래키(`category = models.ForeignKey(PromptCategory, on_delete=models.RESTRICT, related_name='prompts')`)로 매핑합니다.
- **Rationale**:
  - 기존의 단일 문자열 `task` 필드는 범주 데이터의 정규화가 이루어지지 않아 카테고리 이름 변경, 카테고리별 개수 통계 집계, 카테고리 메타데이터(슬러그, 설명 등) 관리에 한계가 존재했습니다.
  - 명세 수용 기준에 따라 `ON DELETE Restrict`를 적용해 연결된 프롬프트가 존재할 경우 카테고리 삭제를 데이터베이스 레벨에서 차단(409 Conflict 반환)함으로써 프롬프트 데이터 무결성을 보호합니다.
  - `Prompt` 모델에서 `category` 지정은 필수(Mandatory, `null=False`, `blank=False`) 항목으로 연동합니다.
- **Alternatives Considered**:
  - `on_delete=models.SET_NULL`: 카테고리 삭제 시 프롬프트를 미분류 상태로 보존하는 방법. (기획 요구사항상 프롬프트는 필수적으로 카테고리에 속해야 하고 Restrict 제약을 준수해야 하므로 기각)
  - `on_delete=models.CASCADE`: 카테고리 삭제 시 소속 프롬프트 전체 연쇄 삭제. (치명적 프롬프트 자산 손실 위험이 있으므로 기각)

---

### 2. 하위 호환성 및 기존 문자열 `task` 파라미터 매핑 (Backward Compatibility Strategy)

- **Decision**: `PromptFilterSet` 필터 클래스에서 `category` (ID) 및 `category_slug` (영문 슬러그) 전용 필터 파라미터를 새로 추가하는 동시에, 레거시 API 파라미터인 `task` 검색어가 인수로 들어올 경우 `category__name__icontains` 또는 `category__slug`와 자동 매핑하여 처리합니다.
- **Rationale**:
  - 기존 SDK 또는 외부 비즈니스 서비스 API 호출부의 전면 수정 없이도 레거시 `task` 필터링 요청을 새로운 `PromptCategory` 관계 필터로 유연하게 변환 처리할 수 있습니다.
  - 데이터 마이그레이션 단계에서는 기존 `task` 문자열 값을 기반으로 초기 `PromptCategory` 엔티티를 자동 세이빙/연결하는 Data Migration을 수행합니다.
- **Alternatives Considered**:
  - 레거시 `task` 파라미터 즉시 폐기(Deprecated & Hard Remove): 기존 연동 애플리케이션에 대한 하위 호환성 파괴 위험으로 인해 기각.

---

### 3. 카테고리별 프롬프트 수 집계 성능 최적화 (Prompt Count Aggregation)

- **Decision**: `PromptCategoryViewSet` 목록 조회(`list`) 뷰에서 Django ORM의 `annotate(prompt_count=Count('prompts'))` 식을 적용하여 API 응답 시 `prompt_count` 필드를 함께 반환합니다.
- **Rationale**:
  - N+1 쿼리 오버헤드를 유발하는 Python 객체 루프 순회 대신, 단일 DB SQL Query 레벨에서 `LEFT OUTER JOIN`과 `COUNT()` 집계를 실행함으로써 응답 지연 시간 목표(SC-004: 1초 이내)를 완벽히 충족합니다.
  - `django.test.TestCase` 기반 하이브리드 ORM 검증을 통해 응답 메타데이터 정합성을 검증합니다.
- **Alternatives Considered**:
  - `PromptCategory` 모델에 `prompt_count` 정적 컬럼을 두고 프롬프트 생성/삭제 마다 시그널(Signal)로 업데이트: 동구현 복잡도 증가 및 트랜잭션 경쟁 조건 위험이 있어 DB ORM `annotate` 방식으로 채택.
