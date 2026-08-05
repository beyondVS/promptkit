# PromptKit Documentation Index

PromptKit 프로젝트의 아키텍처, 서버/SDK/Django 통합 패키지 요구사항, API 계약 및 개발 마일스톤 문서 모음입니다.

---

## 📚 문서 지지도 (Document Map)

| 문서명 | 역할 및 내용 | 비고 |
| :--- | :--- | :--- |
| [architecture.md](architecture.md) | 전체 모노레포 구조, 백엔드/SDK/Django패키지 역할, 컴파일 흐름 및 운용 규칙 | **핵심 아키텍처** |
| [project-spec.md](project-spec.md) | 프로젝트 전체 기술 사양, 어댑터 명세, 코딩 및 MVP 규격 | **전체 스펙 정의서** |
| [promptkit-server-requirements.md](promptkit-server-requirements.md) | Prompt Server 전용 백엔드 요구사항 및 도메인 범위 | **서버 요구사항** |
| [promptkit-sdk-requirements.md](promptkit-sdk-requirements.md) | Pure Python Core SDK (`packages/promptkit`) 전용 요구사항 | **SDK 요구사항** |
| [promptkit-django-requirements.md](promptkit-django-requirements.md) | Django 연동 패키지 (`packages/promptkit-django`) 전용 요구사항 | **Django패키지 요구사항** |
| [sdk-read-api-contract.md](sdk-read-api-contract.md) | SDK Read-Only API 규격, 인증, On-live/라벨 조회 규약 | **API 계약 문서** |
| [project-plan.md](project-plan.md) | MVP 완성을 위한 일자별 마일스톤 및 기술 리스크 대응 | **일정 관리 계획서** |
| [roadmap.md](roadmap.md) | MVP 이후 확장 예정인 장기 기능 구상 및 기술 고도화 아이템 | **로드맵 문서** |

---

## 📖 추천 읽기 순서 (Reading Order)

1. **프로젝트 전체 개요 파악**: [architecture.md](architecture.md) & [project-spec.md](project-spec.md)
2. **Prompt Server 개발자**: [promptkit-server-requirements.md](promptkit-server-requirements.md) & [sdk-read-api-contract.md](sdk-read-api-contract.md)
3. **SDK 및 Django 통합 개발자**: [promptkit-sdk-requirements.md](promptkit-sdk-requirements.md) & [promptkit-django-requirements.md](promptkit-django-requirements.md)
4. **일정 및 마일스톤 확인**: [project-plan.md](project-plan.md) & [roadmap.md](roadmap.md)
