# Quickstart & Validation Guide: promptkit 컨셉 재정의 및 문서화

## Overview
본 가이드는 재정의된 `promptkit` 아키텍처(Django Template 대시보드 CUD, SDK Read-only 조회, 인증 분리 및 문서화)를 검증하기 위한 시연 및 하네스 가이드입니다.

---

## Prerequisites
- Python 3.13+
- `uv` 패키지 매니저
- Git 레포지토리 로컬 체크아웃

---

## 1. Verification Step 1: SDK Read-Only Interface Verification

`packages/promptkit` SDK 패키지에 프롬프트 CUD(생성/수정/삭제) 관련 메서드가 존재하지 않고 오직 Read-only `fetch()` 인터페이스만 노출되는지 검증합니다.

```python
# test_sdk_interface.py
from promptkit import PromptKitClient

def test_sdk_read_only_methods():
    client = PromptKitClient(api_key="test-key", base_url="http://localhost:8000")
    
    # 1. Fetch/Get 인터페이스 존재 검증
    assert hasattr(client, "fetch_prompt")
    
    # 2. CUD 메서드 부재 검증
    assert not hasattr(client, "create_prompt")
    assert not hasattr(client, "update_prompt")
    assert not hasattr(client, "delete_prompt")
```

---

## 2. Verification Step 2: Dashboard Auth & API Key Isolation Test

`X-PromptKit-Api-Key`로 대시보드 URL 진입 시 차단되는지 검증합니다.

```bash
# 1. SDK API Key로 대시보드 접근 시도 (Expect: 401 or 403)
curl -i -H "X-PromptKit-Api-Key: test-api-key" http://localhost:8000/dashboard/prompts/

# 2. SDK Read-Only API 호출 (Expect: 200 OK)
curl -i -H "X-PromptKit-Api-Key: test-api-key" http://localhost:8000/api/v1/prompts/my-prompt/
```

---

## 3. Verification Step 3: Documentation Consistency Audit

프로젝트 문서 4종 및 일정 로드맵에 새 아키텍처 규칙이 적용되어 있는지 확인합니다.

```bash
# 핵심 문서 내 새 아키텍처 키워드 검증
grep -i "Read-only" constitution.md AGENTS.md README.md
grep -i "Django Template" AGENTS.md docs/*.md
```
