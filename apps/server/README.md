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
