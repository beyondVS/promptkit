# Recommended External Agent Skills (추천 외부 에이전트 스킬 카탈로그)

> [!NOTE]
> 본 카탈로그는 검증된 3rd-party 외부 스킬의 모범 사례를 큐레이션한 카탈로그입니다. 외부 레포지토리의 업데이트로 스킬명이나 설치 옵션이 변경되었을 경우, 각 섹션 하단의 원본 README 링크를 단일 진실 출처(SSOT)로 참조하십시오.

---

## 💡 표준 CLI 설치 가이드 (`npx skills add`)

```bash
# 1) 레포지토리 전체 스킬 일괄 설치 예시
npx skills add <repository-url>

# 2) 특정 단독 스킬 선택 설치 예시
npx skills add <repository-url> --skill "<skill-name>"
```

---

## 🎨 1. 프론트엔드 & UI 디자인 스킬

### [taste-skill](https://github.com/Leonxlnx/taste-skill)
- **개요**: AI 프론트엔드 코드(AI Slop) 방지, 모던 타이포그래피, 동적 뷰포트 레이아웃, micro-interaction 디자인 및 비주얼 파이프라인 지침 모음
- **전체 일괄 설치**: `npx skills add https://github.com/Leonxlnx/taste-skill`

| 하위 스킬명 (Skill Name) | 주요 역할 및 제공 지침 | 단독 선택 설치 명령어 |
| :--- | :--- | :--- |
| **design-taste-frontend** | Anti-Slop 디자인 규격, CSS Grid, 뷰포트 및 모던 스타일 기본 지침 | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"` |
| **minimalist-ui** | Notion/Linear 스타일의 미니멀리즘 인터페이스 & 절제된 색상 지침 | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "minimalist-ui"` |
| **image-to-code** | 시안/참고 이미지를 분석하여 모던 프론트엔드 코드로 구현하는 비주얼 파이프라인 | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "image-to-code"` |
| **brand-kit** | 브랜딩 색상 고정(Color Lock) 및 디자인 시스템 구성 지침 | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "brand-kit"` |
| **reference-board** | Web/Mobile reference 보드 뷰포트 구도 및 UX 구성 가이드 | `npx skills add https://github.com/Leonxlnx/taste-skill --skill "reference-board"` |

> 💡 *추가 하위 스킬 및 세부 옵션은 [Leonxlnx/taste-skill README](https://github.com/Leonxlnx/taste-skill)를 참조하십시오.*

---

## 🛠️ 2. 백엔드 & 프레임워크 스킬

### [django-ai-plugins](https://github.com/vintasoftware/django-ai-plugins)
- **개요**: Django 백엔드 아키텍처 모범 사례(ORM, DRF, Celery 비동기, DB 마이그레이션 안전 수칙 및 코드 리뷰어) 지침 모음
- **전체 일괄 설치**: `npx skills add https://github.com/vintasoftware/django-ai-plugins`

| 하위 스킬명 (Skill Name) | 주요 역할 및 제공 지침 | 단독 선택 설치 명령어 |
| :--- | :--- | :--- |
| **django-expert** | Django ORM 쿼리 최적화, DRF API 설계 및 유닛 테스트 지침 | `npx skills add https://github.com/vintasoftware/django-ai-plugins --skill "django-expert"` |
| **django-celery-expert** | Celery 백그라운드 Task, Redis 비동기 큐 처리 전문 지침 | `npx skills add https://github.com/vintasoftware/django-ai-plugins --skill "django-celery-expert"` |
| **django-safe-migration** | DB 마이그레이션 시 테이블 락 방지 및 데이터 무결성 안전 수칙 | `npx skills add https://github.com/vintasoftware/django-ai-plugins --skill "django-safe-migration"` |
| **django-reviewer** | Django 코드 품질 및 헌법 부합성 비판적 검수 스킬 | `npx skills add https://github.com/vintasoftware/django-ai-plugins --skill "django-reviewer"` |

> 💡 *추가 하위 스킬 및 세부 옵션은 [vintasoftware/django-ai-plugins README](https://github.com/vintasoftware/django-ai-plugins)를 참조하십시오.*

---

## 📐 3. 신규 추천 스킬 등록 템플릿 (Skill Registration Template)

향후 신규 외부 3rd-party 에이전트 스킬 및 AI 플러그인을 본 카탈로그에 추가할 때는 아래 표준 양식을 준수하여 작성하십시오:

```markdown
### [<repository-name>](https://github.com/owner/repository-name)
- **개요**: <스킬의 주요 목적 및 에이전트에 주입하는 핵심 지침 1줄 요약>
- **전체 일괄 설치**: `npx skills add https://github.com/owner/repository-name`

| 하위 스킬명 (Skill Name) | 주요 역할 및 제공 지침 | 단독 선택 설치 명령어 |
| :--- | :--- | :--- |
| **<skill-name-1>** | <주요 기능 1줄 요약> | `npx skills add https://github.com/owner/repository-name --skill "<skill-name-1>"` |
| **<skill-name-2>** | <주요 기능 1줄 요약> | `npx skills add https://github.com/owner/repository-name --skill "<skill-name-2>"` |

> 💡 *추가 하위 스킬 및 세부 옵션은 [<owner/repository-name> README](https://github.com/owner/repository-name)를 참조하십시오.*
```
