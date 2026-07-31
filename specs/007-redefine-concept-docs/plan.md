# Implementation Plan: promptkit 프로젝트 컨셉 재정의 및 문서화

**Branch**: `007-redefine-concept-docs` | **Date**: 2026-07-31 | **Spec**: [spec.md](file:///D:/Projects/Private/promptkit/specs/007-redefine-concept-docs/spec.md)

**Input**: Feature specification from `/specs/007-redefine-concept-docs/spec.md`

## Summary

`promptkit-server`와 `promptkit-sdk`의 역할 및 인증 경계를 명확히 재정의합니다.
서버는 Django Template 기반 대시보드를 통해 프롬프트/카테고리 관리(CUD) 및 Django Session Auth를 제공하고, SDK 전용 Read-only REST API(`X-PromptKit-Api-Key` 환경 변수 기반 인증)만을 외부에 노출합니다. SDK는 CUD 메서드를 완전히 제거하여 Read-only 조회에만 집중시킵니다. 이와 함께 `constitution.md`, `AGENTS.md`, `README.md`, `docs/*.md` 및 `docs/project_plan.md`를 신규 컨셉에 맞춰 최신화합니다.

## Technical Context

**Language/Version**: Python 3.13+

**Primary Dependencies**: Django, Django REST Framework, Pydantic v2

**Storage**: PostgreSQL / Django ORM (`PromptCategory`, `Prompt`, `Version`, `Label`, `VariableDefinition`, `Section` models)

**Testing**: pytest, pytest-django, unittest

**Target Platform**: Linux Server / Self-hosted Python

**Project Type**: Monorepo Python Web Application (`apps/server`) + Pure Python SDK (`packages/promptkit`) + Django Integration (`packages/promptkit-django`)

**Performance Goals**: <100ms API response for prompt fetch

**Constraints**: Prompt Registry Focus (No LLM calls inside SDK/Server), Framework Agnostic Core SDK (`packages/promptkit`), Django Integration Package (`packages/promptkit-django`), Subdirectory Installation Support, Environment Variable API Key Auth (`.env` `PROMPTKIT_API_KEY`)

**Scale/Scope**: Monorepo Architecture + Core Documentation Alignment (`constitution.md`, `AGENTS.md`, `README.md`, `docs/*.md`, `docs/project_plan.md`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Prompt Registry Focus**: Passed. Prompt Server는 프롬프트 레지스트리로만 작동하며 SDK 및 서버 내 LLM 호출 로직 없음.
- [x] **II. SDK-First & Framework Agnostic SDK Core**: Passed. `packages/promptkit`은 순수 파이썬 프레임워크 독립 라이브러리로 유지.
- [x] **III. Prompt Compilation & Adapters**: Passed. SDK단에서 `compile()` 처리.
- [x] **IV. Label-Driven Resolution**: Passed. `production` 기본 라벨 제공.
- [x] **V. Lightweight & Self-Hosted First**: Passed. DB ApiKey 모델 대신 `.env` 시크릿 방식을 적용하여 가볍고 자체 호스팅이 용이함.

## Project Structure

### Documentation (this feature)

```text
specs/007-redefine-concept-docs/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   └── sdk-server-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
apps/server/              # Django REST Framework Prompt Server
├── config/              # Django 루트 설정 및 URL 라우팅
├── core/                # 공통 유틸리티
└── prompts/             # 프롬프트 레지스트리 Django App
    ├── models.py        # PromptCategory, Prompt, Version, Label 등
    ├── views/           # 대시보드 CUD View(Django Template) 및 SDK Read-only API View
    ├── templates/       # 대시보드 Django HTML Templates
    ├── urls.py          # 대시보드 및 SDK Read-only API 라우팅
    └── serializers.py   # SDK Read-only Serializer

packages/promptkit/       # Pure Python SDK (Read-only Fetch Only)
├── src/promptkit/

packages/promptkit-django/ # Django Integration Package

docs/                     # Architecture & Planning Documentation
├── project_plan.md
```

**Structure Decision**: Monorepo structure preserving isolation between `apps/server`, `packages/promptkit`, and `packages/promptkit-django`.

## Complexity Tracking

*No constitution violations. Architecture adheres to all core principles.*
