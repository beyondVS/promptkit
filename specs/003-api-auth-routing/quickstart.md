# Quickstart Validation Guide: API Routing & Auth

## Overview
This guide provides runnable scenarios to validate DRF API Key authentication and routing setup for `apps/server`.

---

## 1. Automated Unit Tests

Run test cases for API Key authentication:

```bash
uv run pytest tests/server/test_auth.py
```

---

## 2. Linter & Type Check Harness Validation

Execute static analysis and type checks:

```bash
# Linter check
uv run ruff check

# Formatter check
uv run ruff format

# Static type check
uv run mypy .
```

---

## 3. Interactive Health & Auth Endpoint Verification

Start the Django dev server or test client:

```bash
# 1. Access Public Health Check (expect 200 OK)
curl -X GET http://127.0.0.1:8000/api/v1/health/

# 2. Access Protected Endpoint without API Key (expect 401 Unauthorized)
curl -X GET http://127.0.0.1:8000/api/v1/protected/

# 3. Access Protected Endpoint with valid API Key (expect 200 OK)
curl -X GET http://127.0.0.1:8000/api/v1/protected/ -H "X-API-Key: dev-secret-key"
```
