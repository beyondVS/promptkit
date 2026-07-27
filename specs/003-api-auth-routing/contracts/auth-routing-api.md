# Contract: API Key Authentication & Route Specifications

## Overview
This document specifies the HTTP header contract, authentication failure responses, and public vs protected endpoints for PromptKit API Server.

---

## 1. Authentication Contract

### Request Header
```http
X-API-Key: <valid_api_key>
```

### Success Response (Protected Endpoints)
When a valid `X-API-Key` is supplied, requests proceed to view processing normally.

### Failure Responses

#### Missing or Invalid API Key (HTTP 401 Unauthorized)
```json
{
  "detail": "Invalid or missing API Key."
}
```

---

## 2. Endpoint Routing Map

| Endpoint | Method | Access Level | Description |
|---|---|---|---|
| `/api/v1/health/` | GET | Public | Health check / server status |
| `/api/v1/prompts/` | GET, POST | Protected | Prompt management (Day 04) |
