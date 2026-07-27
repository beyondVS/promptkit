# Data Model Specification: API Key & Auth Configuration

## Overview
This feature introduces authentication credential models and configuration structures used by the Django REST Framework authentication middleware.

---

## Data Structures

### 1. `APIKeyHeader` (In-Memory Request Representation)

| Parameter Name | Header Key | Type | Description |
|---|---|---|---|
| `key` | `X-API-Key` | String | Secret API Key string passed by client |

### 2. `APIKeyConfig` (Environment Configuration)

| Setting Name | Default Value | Description |
|---|---|---|
| `PROMPTKIT_API_KEY` | `dev-secret-key` | Server-side valid API Key secret |
| `REST_FRAMEWORK` | `DEFAULT_AUTHENTICATION_CLASSES` | `apps.server.core.auth.APIKeyAuthentication` |
