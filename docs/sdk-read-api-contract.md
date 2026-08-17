# PromptKit SDK Read API Contract

본 문서는 Core SDK distribution인 `promptkit`과 `apps/server` 간의 프롬프트 원격 조회(Read-Only API) 공식 데이터 및 HTTP 프로토콜 계약 문서입니다.

---

## 1. Access Boundary & Authentication

- **접근 범위**: SDK에는 프롬프트 CUD API가 전면 제외되며, 오직 Read-Only 조회 API만 제공합니다.
- **인증 방식**: HTTP Header `X-PromptKit-Api-Key: <api-key>` 검증 (서버 `.env` 내 `PROMPTKIT_API_KEY` 대조).
- **CUD 보호**: 대시보드 CUD 조작은 `/dashboard/` 경로의 Django Session Auth 및 CSRF 보호로 격리됩니다.

---

## 2. API Endpoint & HTTP Methods

```text
GET /api/v1/prompts/<slug>/
GET /api/v1/prompts/<slug>/?label=<published-label>

Headers:
  X-PromptKit-Api-Key: <api-key>
```

- **HTTP Method**: `GET` 전용 (`POST`, `PUT`, `DELETE` 요청 시 `405 Method Not Allowed` 응답).

---

## 3. Resolution & Fallback Policy

1. **라벨 생략 요청 (`GET /api/v1/prompts/<slug>/`)**:
   - 프롬프트의 `is_on_live=True`로 지정된 **발행(Published) 버전만** 반환합니다.
   - `on-live` 버전이 지정되어 있지 않은 경우 `latest`, 사용자 정의 라벨, 초안(Draft)으로 자동 fallback하지 않고 **`404 no_deployable_version`** 응답을 반환합니다.
2. **명시적 라벨 요청 (`GET /api/v1/prompts/<slug>/?label=<name>`)**:
   - `latest`: 프롬프트의 가장 마지막 발행 버전을 반환하는 시스템 예약 라벨.
   - 커스텀 라벨 (예: `staging`, `v1.2`): 해당 라벨이 매핑된 발행 버전만 반환. 초안(Draft) 버전을 가리키는 라벨은 허용되지 않습니다.
   - `production`: 시스템 또는 사용자 정의 라벨로 정의/사용할 수 없으며 요청 시 **`400 invalid_label`** 응답을 반환합니다.

---

## 4. Response Schema & Caching Contract

### 4.1 200 OK Response Schema (JSON)

```json
{
  "slug": "welcome-email",
  "name": "Welcome Email Prompt",
  "description": "",
  "category": {
    "name": "General",
    "slug": "general"
  },
  "version": 2,
  "version_status": "published",
  "is_on_live": true,
  "label": null,
  "template_text": "Hello {{ customer_name }}, welcome to {{ product_name }}!",
  "sections": [
    {
      "role": "system",
      "order": 0,
      "content": "You are a helpful customer support assistant."
    },
    {
      "role": "user",
      "order": 1,
      "content": "Hello {{ customer_name }}, welcome to {{ product_name }}!"
    }
  ],
  "variables": [
    {
      "name": "customer_name",
      "var_type": "string",
      "required": true,
      "default_value": "Customer",
      "description": "Target customer name"
    },
    {
      "name": "product_name",
      "var_type": "string",
      "required": true,
      "default_value": "PromptKit",
      "description": "Product brand name"
    }
  ],
  "created_at": "2026-08-05T12:00:00Z"
}
```

### 4.2 Conditional Retrieval and Caching Scope

- 모든 성공 `200 OK` 응답에는 해당 JSON 표현의 결정적 quoted `ETag` 헤더가 포함됩니다.
- 클라이언트는 이전 validator를 `If-None-Match`에 전송할 수 있습니다. 현재 표현과 일치하면 서버는 body 없이 동일한 `ETag`를 포함한 `304 Not Modified`를 반환합니다.
- 약한 validator, validator 목록, wildcard `*`를 지원하며 malformed 또는 부분 일치는 match로 처리하지 않습니다.
- `PromptKitClient.fetch()`는 기존 계약을 유지합니다. `PromptKitClient.fetch_conditional()`은 200 prompt 또는 bodyless 304 outcome을 `ConditionalFetchResult`로 구분하며, 성공 응답에 유효한 ETag가 없으면 `InvalidResponseError`를 발생시킵니다.
- Django cache 연동은 `promptkit-django`의 명시적 `fetch_cached()` helper만 사용합니다. 기존 `get_client().fetch()`는 cache-aware가 아닙니다.

### 4.3 Local Compilation Boundary
- `PromptKitClient.fetch()`는 원격 레지스트리에서 템플릿, 변수 선언, 섹션 및 버전 메타데이터를 조회할 뿐 자동 렌더링하지 않습니다.
- 조회된 `RetrievedPrompt`는 `compile(params=...)`으로 호출자 프로세스 안에서 별도로 검증·렌더링합니다. 컴파일 입력값은 이 HTTP API로 전송되지 않습니다.
- 컴파일은 선언된 `{{ variable_name }}` 변수만 처리하며, 유효성 실패 또는 잘못된 템플릿에서는 부분 결과를 반환하지 않습니다.
- 이 계약은 원격 조회 HTTP 프로토콜만 다룹니다. `CompiledPrompt`의 상세 데이터 및 오류 계약은 [Day 11 SDK 컴파일 계약](../specs/011-sdk-compile-rendering/contracts/sdk-compile-api.md)을 따릅니다.

---

## 5. HTTP Status Code Summary

| HTTP Status | Error Code / Reason | Description |
| :--- | :--- | :--- |
| **`200 OK`** | - | 프롬프트 정상 조회 완료 |
| **`304 Not Modified`** | matching `If-None-Match` | 본문 없이 현재 표현이 validator와 동일함을 확인 |
| **`400 Bad Request`** | `invalid_label` | `production` 금지 라벨 지정 시 응답 |
| **`401 Unauthorized`** | DRF 기본 detail | `X-PromptKit-Api-Key` 헤더 누락 또는 유효하지 않은 API 키 |
| **`404 Not Found`** | DRF 기본 detail | 요청한 slug의 Prompt가 존재하지 않는 경우 |
| **`404 Not Found`** | `no_deployable_version` | 라벨 미지정 시 on-live 발행 버전이 존재하지 않는 경우 |
| **`404 Not Found`** | `label_not_found` | 명시적 라벨이 없거나 발행 버전을 가리키지 않는 경우 |
| **`405 Method Not Allowed`**| DRF 기본 detail | GET 이외의 HTTP Method (POST, PUT, DELETE 등) 사용 시 |
