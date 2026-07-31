# Research & Technical Decisions: promptkit 프로젝트 컨셉 재정의 및 문서화

## Overview
본 연구 문서에서는 `promptkit-server`와 `promptkit-sdk` 간의 아키텍처 경계 재정의, Django Template 대시보드 구축, SDK Read-only 조회 API 엔드포인트 수립 및 문서 최신화 전략을 다룹니다.

---

## Technical Decisions

### 1. Django Template 대시보드 및 Session Auth 구조
- **Decision**: `apps/server` 내에 Django Template 기반의 프롬프트 CUD 대시보드를 구축하고, Django 내장 Session Auth(`django.contrib.auth`)를 활용합니다.
- **Rationale**:
  - Django의 기본 인증/인가 시스템(Form, Session, Permission)을 활용하여 불필요한 커텀 인증 미들웨어 작성 오버헤드를 방지합니다.
  - 대시보드는 백엔드 관리자 전용 웹 화면이므로 폼 로그인 및 세션 기반 접근 제어가 가장 안전하고 표준적입니다.
- **Alternatives Considered**:
  - *DRF + SPA(React/Vue) 대시보드*: 과도한 아키텍처 복잡성 및 빌드 파이프라인 추가 부담으로 배제 (Lightweight & Self-Hosted First 원칙 위배).
  - *Custom Token Header 인증*: 세션 쿠키와 호환되지 않으며 브라우저 XSS/CSRF 관리가 복잡해지므로 배제.

---

### 2. SDK Read-only 조회 API 및 API Key 인증 규격
- **Decision**: `promptkit-server`는 SDK를 위한 Read-only API(`GET /api/v1/prompts/{name}/`)만을 외부에 노출하며, 인증은 Custom HTTP Header `X-PromptKit-Api-Key`를 사용합니다.
- **Rationale**:
  - SDK는 프롬프트를 레지스트리로부터 조회(Fetch)하는 용도로만 제한하며, CUD 메서드를 완벽히 제거하여 프롬프트 임의 변조 위험을 차단합니다.
  - 대시보드의 세션 쿠키 인증과 SDK의 API Key 헤더 인증을 명확히 구분하여 인증 경로 간 보안 간섭을 방지합니다.
- **Alternatives Considered**:
  - *Bearer Token (`Authorization: Bearer ...`)*: OAuth/JWT 토큰 방식과 오인될 수 있어 Custom Header로 직관적 분리.
  - *Query Parameter (`?api_key=...`)*: 웹 서버 액세스 로그 등에 API Key가 노출될 위험이 있어 배제.

---

### 3. 프로젝트 핵심 문서 및 project_plan.md 업데이트 전략
- **Decision**: 헌법(Constitution), 에이전트 마스터 가이드(`AGENTS.md`), 메인 `README.md`, `docs/*.md` 및 `docs/project_plan.md`를 단일 작업 흐름으로 동기화 갱신합니다.
- **Rationale**:
  - 코드 아키텍처 변경과 거버넌스 문서 간 시차가 발생하면 개발자 및 AI 에이전트 간의 환각(Hallucination) 및 지침 충돌이 발생할 수 있습니다.
  - `docs/project_plan.md`의 미완료 로드맵을 신규 컨셉(대시보드 CUD, SDK Read-only)에 맞춰 태스크 단위로 재편합니다.
