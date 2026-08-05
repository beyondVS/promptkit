# PromptKit SDK Read API Contract

본 문서는 `promptkit-sdk`와 `apps/server` 간의 프롬프트 원격 조회(Read-Only API) 공식 데이터 및 HTTP 프로토콜 계약 문서입니다.

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
  If-None-Match: "<etag_value>" (Optional - 조건부 Caching 검증)
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
  "version_number": 2,
  "status": "published",
  "is_on_live": true,
  "revision": 3,
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
  "labels": ["latest", "staging"],
  "updated_at": "2026-08-05T12:00:00Z"
}
```

### 4.2 Caching & ETag Policy
- 서버는 응답 시 `ETag` 헤더를 포함하여 반환할 수 있습니다 (예: `ETag: "w/revision-3"`).
- 클라이언트(SDK 및 Django Cache Integration)가 `If-None-Match: "w/revision-3"` 헤더로 요청 시, 프롬프트 변경이 없으면 서버는 본문(Body) 없이 **`304 Not Modified`**로 응답하여 네트워크 트래픽 및 지연을 최소화합니다.

---

## 5. HTTP Status Code Summary

| HTTP Status | Error Code / Reason | Description |
| :--- | :--- | :--- |
| **`200 OK`** | - | 프롬프트 정상 조회 완료 |
| **`304 Not Modified`** | - | `If-None-Match` ETag 일치 시 본문 없이 응답 |
| **`400 Bad Request`** | `invalid_label` | `production` 금지 라벨 지정 시 응답 |
| **`401 Unauthorized`** | `authentication_failed` | `X-PromptKit-Api-Key` 헤더 누락 또는 누락된 API 키 |
| **`404 Not Found`** | `no_deployable_version` | 요청한 slug가 없거나, 라벨 미지정 시 on-live 버전 미존재 |
| **`405 Method Not Allowed`**| `method_not_allowed` | GET 이외의 HTTP Method (POST, PUT, DELETE 등) 사용 시 |
