# Phase 0 Research: API Routing and API Key Authentication Setup

## Overview

This research document analyzes key architectural decisions for implementing Django REST Framework (DRF) routing, custom API Key authentication, and harness linting/type-checking integration for `apps/server`.

---

## 1. DRF Authentication Class Design

### Decision
Implement a custom authentication backend class `APIKeyAuthentication` inheriting from `rest_framework.authentication.BaseAuthentication`.

### Rationale
DRF provides a extensible `BaseAuthentication` interface. Extending `BaseAuthentication` allows PromptKit server to inspect incoming HTTP headers for `X-API-Key` and validate it against the configured server secret without pulling in heavy third-party user-session libraries.

### Alternatives Considered
- `rest_framework.authentication.TokenAuthentication`: Rejected because standard Token authentication requires Django `User` and `Token` DB tables. PromptKit Registry focus keeps authentication simple and lightweight without mandatory user account tables.

---

## 2. API Key Storage & Verification Strategy

### Decision
Store the server's valid API Key in environment variables (`PROMPTKIT_API_KEY`) loaded via `python-dotenv` in `settings.py`.

### Rationale
Aligns with PromptKit Constitution Principle "No Hardcoding (Absolute Security)". API keys are supplied through `.env` files or environment variables and never committed to version control.

---

## 3. Header Specification & Error Handling

### Decision
- Target Header: `HTTP_X_API_KEY` (client sends `X-API-Key: <key>`).
- 401 Unauthorized (`AuthenticationFailed`): Returned when `X-API-Key` header is missing or invalid.

### Rationale
`X-API-Key` is the standard industry header for service-to-service REST API key authentication. DRF's `exceptions.AuthenticationFailed` automatically formats a structured JSON error response with HTTP 401 status.

---

## 4. Mechanical Quality Harness Integration

### Decision
Enforce strict typing and linting via `ruff check`, `ruff format`, and `mypy` with `django-stubs`.

### Rationale
Ensures zero-defect quality across all newly added views, authentication classes, and URL routing configurations before proceeding to CRUD API phases.
