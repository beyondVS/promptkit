# AI / LLM Application & RAG Architecture Rules (AI & RAG 시스템 아키텍처 지침)

특정 언어나 프레임워크에 귀속되지 않고 범용적으로 적용되는 모던 AI 애플리케이션, RAG(Retrieval-Augmented Generation) 파이프라인 및 자율 에이전트 시스템 구축 아키텍처 규범입니다.

---

## 🤖 1. 스키마 기반 타입 안전 구조화 출력 (Schema-driven Structured Outputs)

- **타입 스키마 객체 파싱 강제**:
  - LLM 응답을 파싱할 때 불안정한 정규표현식이나 암묵적 문자열 파싱을 금지하고, 사용 언어의 정적 타입 스키마(Pydantic, Zod, TypeBox, Protobuf 등)를 활용하여 입출력 데이터 구조를 엄격히 강제하십시오.
- **유효성 검사 실패 처리 (Validation Error Handling)**:
  - LLM 응답이 스키마 유효성 검사(Validation)에 실패할 경우, 프로젝트의 레이턴시 및 에러 처리 정책에 맞춰 즉시 예외를 발생(Fast Fail)시키거나 검사 오류 메시지를 피드백하여 선택적으로 재시도(Self-Correction Retry)를 수행하도록 구성하십시오.

---

## 📚 2. RAG & 검색 데이터 파이프라인 수칙 (RAG & Vector Retrieval)

- **구조 보존 의미적 청킹 (Semantic Chunking)**:
  - 무작위 고정 길이(Fixed-size) 청킹을 지양하고, 문서의 헤더, 문단 경계 및 구조적 맥락을 보존하는 의미적 청킹(Semantic Chunking) 또는 그래프 기반 연관 구조(GraphRAG) 적용을 권장합니다.
- **도메인 특화 검색 파이프라인 (Hybrid Search & Reranking)**:
  - 단순 벡터 유사도(Dense Vector) 검색으로 정밀도가 부족하거나 전문 용어가 포함된 도메인에서는, 키워드 검색(BM25/Sparse)과 벡터 유사도 검색을 결합한 하이브리드 검색 및 재순위화(Reranking) 파이프라인 도입을 적용하십시오.
- **임베딩 모델 및 차원 무결성**:
  - 임베딩 생성 모델과 Vector DB 인덱스 간의 벡터 차원(Dimension) 불일치를 시스템 시동 시점에 미리 검증하십시오.

---

## 🔌 3. AI 에이전트 도구 연결 표준 (Agent Tools & MCP Protocols)

- **표준 MCP / 인터페이스 프로토콜 준수**:
  - LLM 에이전트에 도구를 제공할 때는 Model Context Protocol (MCP) 등 표준 프로토콜을 준수하고, 도구(Tool)의 인자 타입과 설명을 명확히 선언하십시오.
- **부작용(Side-effect) 기반 도구 격리**:
  - 단순 데이터 조회 도구(Read-only Tools)와 DB/시스템 변경을 유발하는 사이드 이펙트 도구(Stateful Mutation Tools)를 명확히 분리하여 안전 제어 레이어를 배치하십시오.

---

## 🛡️ 4. 프롬프트 보안 및 격리 (Prompt Security & Sanitization)

- **프롬프트 주입(Prompt Injection) 방어**:
  - 사용자 입력값(`user_input`)을 시스템 프롬프트 구획에 직접 결합(String Interpolation)하지 말고, 반드시 독립된 User Role 메시지 세그먼트로 격리하여 전달하십시오.
- **민감 정보 하드코딩 금지**:
  - 프롬프트 템플릿 내에 API Key, 자격 증명, 개인정보(PII)를 절대로 직접 매립하지 마십시오.

---

## 📚 5. 외부 생태계 & 레퍼런스 (Ecosystem & References)

- **온디맨드 생태계 참조**: 프로젝트의 주요 기술 스택(Python, TypeScript, Go 등)에 맞춰 널리 검증된 AI/LLM/RAG 서드파티 라이브러리 및 MCP 도체인 레퍼런스를 온디맨드로 참조하십시오.
