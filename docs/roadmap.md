# PromptKit Future Roadmap & Extensions

본 문서는 PromptKit MVP 이후 확장 예정인 기능 구상, 로드맵 및 기술 고도화 아이템을 정리한 문서입니다.

---

## 📌 Post-MVP Future Features (기능적 확장 구상)

1. **Prompt Component 재사용 (Prompt Composition)**
   - 자주 사용되는 공통 시스템 프롬프트(예: 페르소나, 안전 가이드라인)를 모듈화하여 여러 프롬프트에서 재사용할 수 있는 컴포넌트 구조 지원.

2. **Prompt Diff & History Visualizer**
   - 대시보드 내에서 임의의 두 버전(Version) 간 텍스트/변수/섹션 차이점을 나란히 비교(Side-by-Side Diff)하는 시각화 도구.

3. **Prompt Approval Workflow (승인 워크플로우)**
   - 대형 조직을 위한 프롬프트 발행 전 승인 요청, 리뷰어 지정 및 승인/반려 절차 기능.

4. **Prompt Dependency & Impact Analysis (의존성 분석)**
   - 프롬프트 변경 시 해당 프롬프트를 원격 참조하는 서비스/애플리케이션 영향 범위 및 의존성 시각화.

5. **Prompt Test & Playground Execution**
   - 대시보드 Playground 내에서 사용자의 API Key를 이용하여 실제 LLM API 호출 테스트를 수행할 수 있는 테스트 모듈.

---

## ⚙️ Technical & Architectural Roadmap (기술 고도화 및 품질 개선 구상)

1. **LLM Adapters 데이터 계약 상세화 (`CompiledPrompt` 확장)**
   - `CompiledPrompt` 데이터 포맷과 다양한 LLM 공급자 어댑터(Gemini, OpenAI, LiteLLM 등)의 변환 인터페이스 규격을 더욱 정교하게 명세.

2. **Strict Prompt Injection Sanitization Layer**
   - SDK 컴파일 시 사용자 입력 데이터에 포함될 수 있는 시스템 명령어 주입 공격(Prompt Injection)을 감지하고 이스케이프하는 보안 레이어 추가.

3. **Server-side ETag & Conditional 304 Caching Engine**
   - 서버 레지스트리 및 `packages/promptkit-django` 간의 `ETag` (`W/"<slug>-v<ver>-r<rev>"`) 기반 `304 Not Modified` 조건부 Caching 엔진 고도화.

4. **표준화된 DRF JSON Error Schema & 코드 체계**
   - 서버 전체 API의 에러 응답 포맷(`{"error": {"code": "...", "message": "...", "details": {}}}`)과 모듈별 에러 코드를 상용 레벨로 가공 및 공통화.

5. **Zero-Dependency SDK Architecture Enforcement**
   - `packages/promptkit` 코어 SDK의 외부 프레임워크 의존성을 0%로 철저히 유지하며 경량화된 독립 패키지로 배포 및 격리.

6. **SDK Strict Network Timeout & Fallback Resilience**
   - 서버 네트워크 지연 시 호스트 서비스 마비를 방지하기 위한 SDK 레벨의 Strict Timeout(Connect 1초, Read 2초) 및 예외 복구 메커니즘 고도화.
