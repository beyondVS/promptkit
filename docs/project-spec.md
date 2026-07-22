# PromptKit Project Specification

## 1. Project Overview

PromptKit is a lightweight self-hosted Prompt Management Server.

Scope:
- Prompt management
- Version management
- Label management
- Prompt compilation
- Python SDK
- Django integration

Out of Scope:
- Tracing
- Evaluation
- Workflow Engine
- Agent Framework
- Analytics
- Cost Dashboard

---

# 2. Monorepo

```text
promptkit/
├── apps/
│   └── server/
├── packages/
│   ├── promptkit/
│   └── promptkit-django/
├── docs/
├── examples/
└── tests/
```

---

# 3. Packages

## apps/server

Responsibilities

- Prompt CRUD
- Version
- Label
- Variable
- Section
- Playground
- REST API
- Authentication

Technology

- Django
- Django REST Framework
- PostgreSQL

---

## packages/promptkit

Responsibilities

- REST Client
- Prompt Retrieval
- compile()
- Validation
- CompiledPrompt
- JSON Schema
- Adapters

Adapters

- Gemini
- OpenAI
- LiteLLM

SDK NEVER calls an LLM directly.

Adapters only convert CompiledPrompt into provider-specific request arguments.

---

## packages/promptkit-django

Responsibilities

- Django Settings
- Cache
- Helper APIs

Depends on promptkit only.

---

# 4. Compile Flow

```
Prompt
    ↓
Version
    ↓
Label
    ↓
Variables
    ↓
Compile
    ↓
CompiledPrompt
    ↓
Adapter
    ↓
LLM SDK
```

Example

```python
prompt = client.prompts.get("summary")

compiled = prompt.compile(
    params={
        "title": "...",
        "content": "...",
    }
)

compiled = GeminiAdapter().prepare(compiled)

response = gemini.models.generate_content(
    model="gemini-2.5-pro",
    **compiled,
)
```

---

# 5. Labels

Default label

- production

Optional labels

- draft
- dev
- experiment

If label is omitted, production must be returned.

---

# 6. API Requirements

Required APIs

- Prompt CRUD
- Version CRUD
- Label CRUD
- Playground
- Authentication

No LLM execution API.

---

# 7. Git Installation

Every package must be installable independently.

```bash
pip install "git+https://github.com/<org>/promptkit.git#subdirectory=packages/promptkit"
```

---

# 8. Design Principles

- Keep the project lightweight.
- Self-hosted first.
- SDK first.
- Framework agnostic core.
- Django only for server and integration.
- Prompts are application assets.
- Server stores prompts only.
- SDK compiles prompts.
- Adapter converts requests.
- LLM execution belongs to user code.

---

# 9. Coding Rules

- Python 3.13+
- uv
- Ruff
- MyPy
- pytest
- Type hints required
- Pydantic v2
- No hardcoded secrets
- Full unit tests for public APIs

---

# 10. Definition of MVP

- Prompt CRUD
- Version
- Label
- Compile
- Python SDK
- Gemini Adapter
- LiteLLM Adapter
- Django Integration
- Playground
