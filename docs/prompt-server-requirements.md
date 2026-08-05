# Prompt Server 요구사항 (1-Page)

## 1. 개요

Prompt Server는 LLM을 사용하는 애플리케이션에서 사용하는 Prompt를 코드와 분리하여 중앙에서 관리하고 배포하기 위한 서버이다.

애플리케이션은 Prompt를 직접 포함하지 않고 Prompt Server로부터 필요한 Prompt를 조회하여 사용하며, Prompt의 수정은 애플리케이션 배포 없이 즉시 반영할 수 있다.

Prompt Server는 LLM을 호출하지 않으며, Prompt만 관리하는 것을 기본 원칙으로 한다.

---

## 2. 개발 목적

* Prompt와 비즈니스 로직의 분리
* Prompt의 중앙 집중 관리
* Prompt 변경 시 애플리케이션 재배포 제거
* Prompt 버전 관리 및 운영 환경(dev/staging/prod) 지원
* Prompt 재사용성 향상
* AI 서비스(OpenAI, Gemini, Claude 등)와 독립적인 Prompt 관리

---

## 3. 시스템 구성

```text
                 +------------------+
                 |  Prompt Server   |
                 +------------------+
                  │
        Prompt 조회 API
                  │
      +-----------+-----------+
      │                       │
Business Server A      Business Server B
      │                       │
      └──────────────┬────────┘
                     │
               LLM Provider
      (OpenAI / Claude / Gemini ...)
```

Prompt Server는 Prompt만 제공하며, 실제 LLM 호출은 Business Server가 수행한다.

---

## 4. 핵심 기능

### Prompt Repository

* Prompt 등록
* Prompt 수정
* Prompt 삭제
* Prompt 조회

### Version Management

* 초안 작성·복제·삭제 및 발행 관리
* 발행 후 콘텐츠와 lifecycle 상태의 불변성 보장
* 발행 버전에서만 on-live 지정 또는 해제

### Label 및 배포 대상

* 라벨이 생략된 SDK 조회는 on-live 발행 버전만 반환
* `latest`는 마지막 발행 버전만 가리키는 시스템 예약 라벨
* 사용자 정의 라벨은 발행 버전만 가리키며 프롬프트 안에서 고유
* `production` 라벨 및 자동 fallback 금지

### Metadata

Prompt별

* 이름(Name)
* 설명(Description)
* 태그(Tag)
* 업무(Task)
* 작성자
* 생성일

관리

### Variable Definition

Prompt에서 사용하는 변수 정의

예)

* customer_name
* product_name
* language

### Validation

Prompt 조회 시

* 필수 변수 확인
* Prompt 존재 여부 검증

### Search

* 이름 검색
* 태그 검색

---

## 5. 접근 경계와 API

`GET /api/v1/prompts/{slug}/`와 명시적 발행 라벨 조회만 SDK에 제공한다. 라벨 생략 시 on-live 발행 버전을 반환하며, 없으면 배포 가능한 버전이 없음을 응답한다. 대시보드 CUD는 `/dashboard/`의 Django Session Auth 및 CSRF 보호로만 제공한다.

---

## 6. 비기능 요구사항

* REST API 제공
* JSON 기반 응답
* 캐시 지원
* 인증(Authentication) 지원

---

## 7. 개발 범위(MVP)

* Prompt CRUD (대시보드 CUD)
* Prompt Version 및 초안·발행·복제 관리
* On-live 및 Label 배포 관리
* Metadata 관리
* Variable 정의 및 템플릿 검증
* Read-only REST API

---

## 8. 향후 확장

* Prompt Component 재사용
* Prompt Compile
* Prompt Diff
* Prompt Approval Workflow
* Prompt Test
* Prompt Playground
* Prompt Dependency 분석
* Prompt 품질 평가(Evaluation)

---

## 설계 원칙

Prompt Server는 **LLM Gateway**가 아니다.

Prompt를 저장하고 제공하는 **Prompt Registry** 역할에 집중하며, 실제 LLM 호출, 모델 선택, 토큰 관리, 비용 관리 등은 Business Server 또는 별도의 AI Runtime이 담당한다.

장기적으로는 Enterprise Configuration Server의 AI Domain(Prompt, Model, Tool, Agent 설정)을 구성하는 하나의 도메인으로 확장 가능하도록 설계한다.