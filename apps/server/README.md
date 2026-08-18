# Prompt Server (Django) 안내

Django REST Framework 기반 Prompt Registry 서버로, 운영자 대시보드와 SDK 전용 Read-only 조회 API를 제공합니다.

## 기능 및 정책

- **SDK Read-only 조회 API**:
  - `GET /api/v1/prompts/<slug>/` 요청을 `X-PromptKit-Api-Key` 헤더로 인증합니다.
  - **라벨 생략**: on-live로 지정된 발행 버전을 조회합니다. on-live 버전이 없으면 `404 no_deployable_version`을 반환합니다.
  - **명시적 라벨** (`?label=latest` 또는 사용자 정의 라벨): 해당 라벨이 가리키는 발행 버전을 조회합니다.
  - **`production` 라벨**: 사용을 금지하며 `400 invalid_label`로 거부합니다.
- **운영자 세션 대시보드**:
  - `/dashboard/`: CSRF로 보호되며 운영자 세션 인증이 필요한 대시보드입니다.
  - 카테고리, 프롬프트, 초안 버전 섹션 및 초안 버전 변수의 전체 CUD를 지원합니다.
  - 발행, 초안 복제, on-live 대상 선택 및 사용자 정의 라벨 작업을 원자적 트랜잭션으로 처리합니다.
  - `/dashboard/versions/<version_id>/playground/`: 선택한 버전의 변수 값을 받아 SDK
    `compile()`로 aggregate content와 ordered sections를 로컬 렌더링합니다. 결과는
    autoescape와 공백 보존이 적용된 텍스트 프리뷰이며, DB 쓰기나 LLM 호출은 없습니다.

## 빠른 시작

```bash
# 환경 동기화 및 마이그레이션 실행
uv sync
uv run python manage.py migrate

# 대시보드 접근용 슈퍼유저 생성
uv run python manage.py createsuperuser

# 서버 실행
uv run python manage.py runserver
```

로그인 후 프롬프트 상세 화면에서 대상 버전의 Playground 링크를 선택합니다. 문자열,
유한 number, 명시적 true/false boolean, JSON object/array 입력을 지원하며 검증 또는
컴파일 실패 시 같은 화면에 오류가 표시됩니다.

Playground 회귀 테스트는 저장소 루트에서 별도로 실행합니다.

```bash
uv run pytest apps/server/prompts/tests/test_dashboard_playground.py
```
