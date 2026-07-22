# PromptKit Project Implementation Plan

본 문서는 하루 평균 **1시간**의 개발 시간을 할애하여 PromptKit 프로젝트의 MVP를 점진적으로 완성하기 위한 상세 일정 계획서입니다. 

각 개발 단계는 상호 의존성을 고려하여 설계되었으며, 매일 명확한 목표를 달성하고 기계적 하네스 검증(Ruff, MyPy, pytest)을 통과하는 것을 원칙으로 합니다.

---

## 📅 주차별 개발 마일스톤

```text
[1주차: Core Server 기초] ──> [2주차: SDK Core 및 어댑터] ──> [3주차: Django 연동 및 최종 QA]
```

---

## 🛠️ 1주차: 개발 환경 구축 및 Core Server 개발 (약 6시간)
**목표**: 모노레포 구조를 정의하고, Django 기반의 프롬프트 저장소 API 서버의 기본 기능을 확보합니다.

*   **Day 01 (1h): 프로젝트 초기화 및 모노레포 셋업**
    *   uv 패키지 매니저를 통한 모노레포 가상환경 정의 (`uv sync`).
    *   `apps/server` 경로에 Django 프로젝트 생성 및 PostgreSQL 데이터베이스 연결 설정.
*   **Day 02 (1h): DB 모델링 및 마이그레이션**
    *   프롬프트 명세를 위한 Django ORM 모델 설계 (`Prompt`, `Version`, `Label` 모델).
    *   각 모델간의 관계 설정(1:N) 및 마이그레이션 실행.
*   **Day 03 (1h): 기본 API 라우팅 및 인증(Auth) 구축**
    *   Django REST Framework(DRF) 기본 세팅 및 API Key 기반 인증 시스템 설계.
    *   하네스 자동 정적 분석기(Ruff, MyPy) 셋업 및 초기 코드 검사 통과.
*   **Day 04 (1h): Prompt CRUD API 개발**
    *   프롬프트 등록, 수정, 삭제, 상세 조회 API 엔드포인트 구현 및 유닛 테스트 작성.
*   **Day 05 (1h): Version API 및 변경 이력 관리**
    *   프롬프트 변경 시 자동으로 신규 버전을 생성하고 추적하는 이력 관리 API 및 롤백 기능 개발.
*   **Day 06 (1h): 1주차 주간 정렬 및 하네스 검증**
    *   작성된 API 서버 코드에 대해 Ruff 정렬, MyPy 타입 검사, DRF 유닛 테스트 구동 및 오류 제로 달성.

---

## 📦 2주차: 서버 기능 고도화 및 Python SDK Core 개발 (약 6시간)
**목표**: 서버의 메타데이터 비즈니스 로직을 정교화하고, 프롬프트 변수 검증 및 변환을 제공하는 Python SDK 핵심 라이브러리를 개발합니다.

*   **Day 07 (1h): Label API 및 Fallback 로직 구현**
    *   프롬프트 라벨 지정(dev, draft 등) 기능 API 개발.
    *   조회 시 라벨이 생략된 경우 `production` 라벨 버전을 자동으로 탐색 및 반환하는 Fallback 로직 서버 구현.
*   **Day 08 (1h): Web Playground 기초 뷰 설계**
    *   관리자가 웹 브라우저에서 프롬프트 및 변수를 입력해볼 수 있는 DRF 기반 플레이그라운드 API 뷰 구현.
*   **Day 09 (1h): Python SDK (`packages/promptkit`) 환경 셋업**
    *   독립적인 패키지 디렉토리 구조 및 `pyproject.toml` 설정.
    *   서버 API와 통신하여 프롬프트를 원격 조회하는 REST Client 모듈 개발.
*   **Day 10 (1h): SDK compile() 로컬 렌더링 엔진 개발**
    *   프롬프트 내 동적 변수를 파싱하고 렌더링하는 `compile()` 메서드 개발.
    *   주입될 변수의 유효성(Validation) 검증을 위한 Pydantic v2 스키마 연동.
*   **Day 11 (1h): Gemini Adapter 구현**
    *   컴파일된 `CompiledPrompt`를 Google Gemini GenAI SDK의 요청 인자 포맷(`generate_content` arguments)으로 치환하는 `GeminiAdapter` 개발.
*   **Day 12 (1h): LiteLLM Adapter 구현 및 SDK 테스트**
    *   LiteLLM 규격에 대응하는 어댑터 추가 구현.
    *   SDK core의 모든 Public API에 대한 100% 유닛 테스트 작성 및 `pytest` 구동 검증.

---

## ⚡ 3주차: Django Integration 및 최종 교차 검증 (약 6시간)
**목표**: Django 환경 전용 연동 패키지를 완성하고, 모노레포의 빌드 배포 방식 및 에이전트 독립 감사를 거쳐 릴리즈를 준비합니다.

*   **Day 13 (1h): Django Integration 패키지 (`packages/promptkit-django`) 셋업**
    *   Django 설정(`settings.py`) 파일과의 연동 매커니즘 구현 및 SDK 인스턴스 자동 등록.
*   **Day 14 (1h): Django Cache 기반 캐싱 메커니즘**
    *   조회 성능 향상 및 서버 부하 최소화를 위한 Django 내장 Cache API 연동 데코레이터/헬퍼 구현.
*   **Day 15 (1h): 통합 시나리오 작성 및 예제(examples) 구현**
    *   `examples/` 디렉토리에 실제 DRF 서버-SDK-Gemini API 호출에 이르는 엔드투엔드 예제 시나리오 코드 작성.
*   **Day 16 (1h): 독립 배포(Installation) 및 빌드 검증**
    *   모노레포의 개별 패키지가 Git subdirectory 옵션(`pip install "git+https://...#subdirectory=..."`)을 통해 에러 없이 설치되는지 격리 테스트.
*   **Day 17 (1h): E2E 통합 테스트 및 예외 시나리오 정밀 점검**
    *   서버 다운, 잘못된 변수 주입, 권한 오류 발생 시 SDK의 예외 처리와 로깅 구조의 복원성 검증.
*   **Day 18 (1h): 에이전트 교차 검증(Audit) 및 Sign-off**
    *   `AGENTS.md` 7항의 명세서에 의거하여 `auditor` 서브에이전트를 구동해 최종 코드 분석 및 검토 의견 수렴.
    *   발견된 결함 자가 치유 후 `[SIGN-OFF: PASSED]` 승인 획득 및 릴리즈 준비 완료.

---

## 📝 관리 및 복원 팁 (하루 1시간 성공 전략)
1.  **시작 전 기계적 체크**: 전날 마친 시점에서 코드가 꼬이지 않았는지 `uv run ruff check` 및 `uv run pytest`를 먼저 구동해 봅니다.
2.  **커밋의 최소화**: 매일 1시간의 작업이 완료되면 반드시 변경 사항을 쪼개어 Conventional Commit 메시지 규약에 맞게 로컬 커밋을 수행합니다.
3.  **진도 지연 시 대응**: 예외 디버깅 등으로 하루치 진도가 밀릴 경우, 다음 날의 목표를 무리하게 합치지 말고 일정을 하루씩 뒤로 밀어 무결성을 유지합니다. (속도보다 헌법의 '무결성'이 최우선입니다.)
