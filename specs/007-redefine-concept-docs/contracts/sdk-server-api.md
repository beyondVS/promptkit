# Interface Contract: SDK Read-Only Fetch API & Dashboard Auth Boundaries

## 1. Overview
본 계약문서는 `promptkit-server`가 외부에 노출하는 SDK 전용 Read-only API 규격과 Django Template 대시보드 접근 권한 경계를 정의합니다.

---

## 2. Authentication Contracts

### SDK Read-Only Authentication
- **Header**: `X-PromptKit-Api-Key: <PROMPTKIT_API_KEY>`
- **Verification Source**: 서버 환경 변수 `.env` (또는 Django Settings)의 `PROMPTKIT_API_KEY`와 요청 헤더 값 일치 검증 (DB 조회가 아닌 정적 시크릿 검증).
- **Scope**: SDK 전용 API 엔드포인트(`GET /api/v1/prompts/*`)만 허용.
- **Unauthorized Handling**: 헤더가 없거나 `.env`에 설정된 `PROMPTKIT_API_KEY`와 불일치 시 `401 Unauthorized` 반환. 대시보드 URL 진입 시 `403 Forbidden` 반환.

### Dashboard Session Authentication
- **Mechanism**: Django Standard Session Cookie (`sessionid`) & `django.contrib.auth`
- **Scope**: Django Template 대시보드 (`/dashboard/*`) CUD 및 카테고리/프롬프트 관리 전용.
- **Unauthorized Handling**: 미인증 시 `/dashboard/login/`으로 리다이렉트.

---

## 3. SDK Endpoint Specifications (Read-Only)

### Endpoint: Fetch Prompt by Name & Label

- **HTTP Method**: `GET`
- **URL Path**: `/api/v1/prompts/{slug}/`
- **Query Parameters**:
  - `label` (optional, string, default: `production`): 프롬프트 버전 라벨 (`production`, `dev`, `draft` 등)

#### Request Headers
```http
GET /api/v1/prompts/customer-support/?label=production HTTP/1.1
Host: api.promptkit.local
X-PromptKit-Api-Key: pk_live_1234567890abcdef
Accept: application/json
```

#### Success Response (`200 OK`)
```json
{
  "slug": "customer-support",
  "name": "Customer Support Prompt",
  "category": {
    "name": "Customer Support",
    "slug": "customer-support"
  },
  "version": 3,
  "label": "production",
  "template_text": "Hello {user_name}, welcome to {service_name} support!",
  "variables": [
    {
      "name": "user_name",
      "var_type": "string",
      "required": true
    },
    {
      "name": "service_name",
      "var_type": "string",
      "required": true
    }
  ],
  "sections": [
    {
      "role": "system",
      "order": 0,
      "content": "You are a helpful customer support agent."
    },
    {
      "role": "user",
      "order": 1,
      "content": "Hello {user_name}, welcome to {service_name} support!"
    }
  ],
  "created_at": "2026-07-31T10:00:00Z"
}
```

#### Error Responses
- **`401 Unauthorized`**: `X-PromptKit-Api-Key` 헤더가 없거나 `.env` 설정값과 다른 경우
  ```json
  {
    "error": "unauthorized",
    "detail": "Invalid or missing X-PromptKit-Api-Key header"
  }
  ```
- **`404 Not Found`**: 요청한 프롬프트 슬러그 또는 라벨이 존재하지 않는 경우
  ```json
  {
    "error": "not_found",
    "detail": "Prompt 'customer-support' with label 'production' not found"
  }
  ```

---

## 4. Disallowed Contracts (SDK Read-Only Scope Enforcement)

아래 HTTP 메서드 및 엔드포인트는 `promptkit-sdk` 또는 외부 API Key를 통한 호출이 엄격히 금지(Disallowed)되며, 대시보드 내부 세션으로만 동작합니다:
- `POST /api/v1/prompts/` (Create Prompt) -> **405 Method Not Allowed / 403 Forbidden**
- `PUT/PATCH /api/v1/prompts/{slug}/` (Update Prompt) -> **405 Method Not Allowed / 403 Forbidden**
- `DELETE /api/v1/prompts/{slug}/` (Delete Prompt) -> **405 Method Not Allowed / 403 Forbidden**
