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

* [ ] **Day 01 (1h): 프로젝트 초기화 및 모노레포 셋업**
    *   uv 패키지 매니저를 통한 모노레포 가상환경 정의 (`uv sync`).
    *   `apps/server` 경로에 Django 프로젝트 생성 및 PostgreSQL 데이터베이스 연결 설정.
* [ ] **Day 02 (1h): DB 모델링 및 마이그레이션**
    *   프롬프트 명세를 위한 Django ORM 모델 설계 (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section` 모델).
    *   각 모델간의 관계 설정(1:N) 및 마이그레이션 실행.
* [ ] **Day 03 (1h): 기본 API 라우팅 및 인증(Auth) 구축**
    *   Django REST Framework(DRF) 기본 세팅 및 API Key 기반 인증 시스템 설계.
    *   하네스 자동 정적 분석기(Ruff, MyPy) 셋업 및 초기 코드 검사 통과.
* [ ] **Day 04 (1h): Prompt & Section CRUD 및 다차원 검색 API 개발**
    *   프롬프트 및 섹션(Section) 등록, 수정, 삭제, 상세 조회 API 엔드포인트 구현.
    *   이름(Name), 태그(Tag), 업무(Task) 기반의 다차원 프롬프트 검색(Full Text Search) API 구현 및 유닛 테스트 작성.
* [ ] **Day 05 (1h): Version API 및 Markdown Import/Export 개발**
    *   프롬프트 변경 시 자동으로 신규 버전을 생성하고 추적하는 이력 관리 API 및 롤백 기능 개발.
    *   프롬프트 템플릿의 Markdown 파일 Import/Export 지원 API 구현.
* [ ] **Day 06 (1h): 1주차 주간 정렬 및 하네스 검증**
    *   작성된 API 서버 코드에 대해 Ruff 정렬, MyPy 타입 검사, DRF 유닛 테스트 구동 및 오류 제로 달성.

---

## 📦 2주차: 서버 기능 고도화 및 Python SDK Core 개발 (약 6시간)
**목표**: 서버의 메타데이터 비즈니스 로직을 정교화하고, 프롬프트 변수 검증 및 변환을 제공하는 Python SDK 핵심 라이브러리를 개발합니다.

* [ ] **Day 07 (1h): Label API 및 Fallback 로직 구현**
    *   프롬프트 라벨 지정(dev, draft 등) 기능 API 개발.
    *   조회 시 라벨이 생략된 경우 `production` 라벨 버전을 자동으로 탐색 및 반환하는 Fallback 로직 서버 구현.
* [ ] **Day 08 (1h): Web Playground 기초 UI 및 변수 입력 폼 API 설계**
    *   실제 컴파일 연동은 제외하고, 관리자가 프롬프트의 동적 변수를 입력받을 수 있는 Playground 기초 UI 레이아웃 및 변수 스키마 조회 API 개발.
* [ ] **Day 09 (1h): Python SDK (`packages/promptkit`) 환경 셋업 및 REST Client 개발**
    *   독자적인 패키지 디렉토리 구조 및 `pyproject.toml` 설정 후 즉시 Git subdirectory 독립 설치 테스트 실행.
    *   서버 API와 통신하여 프롬프트를 원격 조회하는 REST Client 모듈 및 유닛 테스트 작성.
* [ ] **Day 10 (1h): SDK compile() 로컬 렌더링 엔진 개발**
    *   프롬프트 내 동적 변수를 파싱하고 렌더링하는 `compile()` 메서드 개발.
    *   헌법 규정에 명시된 **Pydantic v2**를 연동하여 주입될 변수의 구조 및 유효성(Validation) 검증 로직 및 유닛 테스트 작성.
* [ ] **Day 11 (1h): Gemini Adapter 및 OpenAI Adapter 구현**
    *   컴파일된 `CompiledPrompt`를 각 공급자 SDK(Gemini 및 OpenAI) 형식에 맞는 호출 인자 규격으로 치환하는 어댑터들 개발 및 어댑터 유닛 테스트 작성.
* [ ] **Day 12 (1h): LiteLLM Adapter 구현 및 SDK 전체 하네스 통합 검증**
    *   LiteLLM 규격에 대응하는 어댑터 추가 구현.
    *   SDK core의 모든 Public API에 대해 `pytest` 100% 통합 하네스 검증 구동.

---

## ⚡ 3주차: Django Integration 및 최종 교차 검증 (약 6시간)
**목표**: Django 환경 전용 연동 패키지를 완성하고, 모노레포의 빌드 배포 방식 및 에이전트 독립 감사를 거쳐 릴리즈를 준비합니다.

* [ ] **Day 13 (1h): Django Integration 패키지 (`packages/promptkit-django`) 셋업**
    *   Django 설정(`settings.py`) 파일과의 연동 매커니즘 구현 및 SDK 인스턴스 자동 등록.
    *   패키지 생성 직후 Git subdirectory 독립 설치 가능 여부 즉시 검증.
* [ ] **Day 14 (1h): Django Cache 기반 캐싱 및 ETag/TTL 정합성 메커니즘**
    *   조회 성능 향상 및 서버 부하 최소화를 위한 Django 내장 Cache API 연동 데코레이터/헬퍼 구현.
    *   HTTP ETag / If-None-Match 헤더 기반의 조건부 검증 및 짧은 TTL(Time-To-Live) 적용을 통한 캐시 정합성 전략 구현.
* [ ] **Day 15 (1h): Playground SDK 연동 및 E2E 예제 구현**
    *   `examples/` 디렉토리에 실제 DRF 서버-SDK-Gemini API 호출에 이르는 엔드투엔드 예제 시나리오 코드 작성.
    *   Day 08에 개발한 Playground 뷰에 SDK의 `compile()` 엔진을 최종 결합하여 **LLM 호출 없는 CompiledPrompt 텍스트 프리뷰 기능** 완성.
* [ ] **Day 16 (1h): 모노레포 통합 배포 및 패키지 상호 운용성 검증**
    *   모노레포의 개별 패키지들이 상호 간섭 없이 각각 독립적으로 설치되고 연동되는지 전체 빌드/배포 격리 테스트.
* [ ] **Day 17 (1h): E2E 통합 테스트 및 예외 시나리오 정밀 점검**
    *   서버 다운, 잘못된 변수 주입, 권한 오류 발생 시 SDK의 예외 처리와 로깅 구조의 복원성 검증.
* [ ] **Day 18 (1h): 에이전트 교차 검증(Audit) 및 Sign-off**
    *   `AGENTS.md` 7항의 명세서에 의거하여 `auditor` 서브에이전트를 동적으로 정의 및 호출하여 독립 코드 검토 수행.
    *   감사 리포트 피드백 루프(최대 3회)를 거쳐 발견된 결함 자가 치유 및 `[SIGN-OFF: PASSED]` 최종 승인 획득 후 릴리즈 완료.

---

## 📝 관리 및 복원 팁 (하루 1시간 성공 전략)
1.  **시작 전 기계적 체크**: 작업을 시작하기 전 [AGENTS.md](../AGENTS.md) 2.2항의 하네스 검증 명령어를 실행하여 코드 베이스의 정적 분석 및 테스트 상태를 먼저 점검합니다.
2.  **커밋의 최소화**: 매일 1시간의 작업이 완료되면 반드시 변경 사항을 쪼개어 Conventional Commit 메시지 규약에 맞게 로컬 커밋을 수행합니다.
3.  **진도 지연 시 대응**: 예외 디버깅 등으로 하루치 진도가 밀릴 경우, 다음 날의 목표를 무리하게 합치지 말고 일정을 하루씩 뒤로 밀어 무결성을 유지합니다. (속도보다 헌법의 '무결성'이 최우선입니다.)

---

## ⚠️ 핵심 기술 리스크 및 대책
1.  **원격 Prompt Server 장애 및 SDK ↔ Server 통신 지연 리스크**
    *   *부작용*: 비즈니스 애플리케이션(SDK 사용자 코드)이 실행 중에 Prompt Server로부터 프롬프트를 실시간 조회할 때, 서버 네트워크 장애나 성능 저하로 인해 비즈니스 서비스 전체가 지연되거나 마비될 수 있습니다.
    *   *대책*: SDK 내부 REST Client에 엄격한 Connection/Read Timeout(예: 1~2초)을 설정하고, 조회 실패 시 개발자가 코드상에 지정한 로컬 Fallback 프롬프트(기본 템플릿)가 반환되는 예외 복구(Graceful Degradation) 로직을 구현합니다. 또한 `packages/promptkit-django` 연동 라이브러리의 캐시 레이어를 활성화하여 실시간 API 호출 빈도를 낮춥니다.
2.  **프롬프트 템플릿 변수 Injection 공격 리스크**
    *   *부작용*: 사용자가 입력하는 프롬프트 변수 내에 LLM 지시사항을 무력화하는 시스템 프롬프트 주입(Injection) 공격이 침투할 수 있습니다.
    *   *대책*: SDK `compile()` 메서드 내에서 Pydantic v2 스키마를 사용하여 특수 문자를 이스케이프하거나 허용된 타입 및 문자열 길이 규격을 엄격히 검증합니다.
3.  **캐싱 무효화(Cache Invalidation) 및 동기화 지연 리스크**
    *   *부작용*: Django API 서버에서 프롬프트가 수정되었으나 SDK의 로컬 캐시 또는 Django Cache 데코레이터에 의해 구버전 프롬프트가 계속 제공되는 현상이 발생합니다.
    *   *대책*: HTTP ETag / If-None-Match 조건부 헤더 대조 및 적절한 TTL(Time-To-Live) 설정을 통해 서버 상태 변경 시 캐시를 효과적으로 재검증 및 무효화합니다.

---

## 🔒 개발 보안 및 로깅 표준
1.  **보안 표준 준수**: 시크릿 및 자격 증명 관리는 [constitution.md](../.specify/memory/constitution.md)의 **절대 보안 (No Hardcoding)** 조항을 엄격히 준수합니다.
2.  **구조화된 로깅 (Structured Logging)**: 프롬프트 컴파일 실패, 변수 유효성 검사 실패, 캐시 동기화 오류 및 API 통신 실패 등 주요 예외 발생 시 원인 분석이 가능하도록 표준화된 Python logging 시스템을 통해 컨텍스트 정보를 기록합니다.
