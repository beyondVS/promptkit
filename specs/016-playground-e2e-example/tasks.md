# Tasks: Playground Compilation and Gemini E2E Example

**Input**: Design documents from `/specs/016-playground-e2e-example/`

**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: FR-018 requires repeatable automated coverage. Tests are written before the corresponding implementation and must not require live credentials, network access, Gemini quota, or provider cost.

**Organization**: Tasks are grouped by user story so each story can be implemented and verified as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because the task changes different files and has no unmet dependency.
- **[Story]**: Maps the task to US1, US2, or US3 from `spec.md`.
- Every task names the exact file or files it changes.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish dependency boundaries and example configuration without changing runtime behavior.

- [ ] T001 [P] Declare the compatible local `promptkit` dependency for the Django server in `apps/server/pyproject.toml` and refresh the repository `uv.lock` with `uv` only
- [ ] T002 [P] Create the isolated Python 3.13+ consumer project with local `promptkit` and example-only `google-genai>=2.18.1,<3` dependencies in `examples/gemini-e2e/pyproject.toml` and generate `examples/gemini-e2e/uv.lock`
- [ ] T003 [P] Add secret-free placeholders and descriptions for `PROMPTKIT_BASE_URL`, `PROMPTKIT_API_KEY`, `PROMPTKIT_PROMPT_SLUG`, `PROMPTKIT_PROMPT_PARAMS`, `GEMINI_API_KEY`, and `GEMINI_MODEL` in `examples/gemini-e2e/.env.example`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Confirm the existing dashboard and SDK public contracts that every story must reuse.

**⚠️ CRITICAL**: Complete this phase before implementing any user story; do not add a migration, internal compile API, browser compiler, or provider dependency outside the example project.

- [ ] T004 [P] Create the dashboard service package marker in `apps/server/prompts/services/__init__.py` without adding persistence or provider abstractions
- [ ] T005 [P] Add regression assertions for the existing public `RetrievedPrompt`, `CompiledPrompt`, PromptKit validation exceptions, `PromptKitClient`, and `GeminiAdapter` imports in `tests/promptkit/integration/test_public_sdk_harness.py`

**Checkpoint**: Public SDK contracts and the existing protected Playground resource are ready for story work.

---

## Phase 3: User Story 1 - Playground compiled preview (Priority: P1) 🎯 MVP

**Goal**: Let an authenticated staff user submit typed variables for the selected version and receive SDK-compiled aggregate and ordered section text without persistence or an LLM call.

**Independent Test**: Submit valid values, including repeated variables, placeholder-like input text, whitespace, Unicode, and a version with no variables; confirm the response completes within 2 seconds, identifies the selected slug/version, performs only one substitution pass, preserves ordered compiled output, states that no LLM was called, and leaves registry records unchanged.

### Tests for User Story 1

> **Write these tests first and confirm they fail for the missing POST behavior.**

- [ ] T006 [US1] Extend `DashboardPlaygroundTests` using Django `TestCase` and `setUpTestData` in `apps/server/prompts/tests/test_dashboard_playground.py` to cover successful typed POST compilation within the 2-second SC-001 limit, repeated substitutions, placeholder-like input remaining literal after a single substitution pass, no-variable output, section ordering, empty/whitespace/Unicode preservation, HTML escaping, exactly one SDK `compile()` call, zero provider calls, and zero database writes

### Implementation for User Story 1

- [ ] T007 [P] [US1] Implement the request-scoped dynamic Playground form in `apps/server/prompts/forms.py` with `variable__<name>` fields, declaration order, defaults, string whitespace retention, strict integer/finite-float parsing, explicit boolean parsing, object-or-array JSON parsing, omission of blank optional values, and explicit rejection of submitted `variable__*` names absent from the selected version declarations
- [ ] T008 [P] [US1] Implement eager ORM snapshot loading plus ordered `Version`/variable/section mapping to public `RetrievedPrompt` and one-call `compile()` orchestration in `apps/server/prompts/services/playground.py`
- [ ] T009 [US1] Add CSRF-protected POST handling to `DashboardPlaygroundView` in `apps/server/prompts/views/dashboard.py`, binding the dynamic form for the URL-selected version and rendering a request-local `CompiledPrompt` without saving models or invoking providers
- [ ] T010 [US1] Replace the display-only controls with a named CSRF form and add auto-escaped, whitespace-preserving aggregate/ordered-section preview regions plus an explicit no-LLM notice in `apps/server/prompts/templates/prompts/playground.html`

**Checkpoint**: US1 is independently usable as an LLM-free compiled preview and is the MVP.

---

## Phase 4: User Story 2 - Safe compilation error correction (Priority: P1)

**Goal**: Show actionable, value-safe field or template errors while retaining editable inputs and never displaying partial output.

**Independent Test**: Submit missing required, invalid number/boolean/JSON, undeclared, and template-mismatch cases; confirm the affected field or error category appears, safe input state remains editable, no partial preview is rendered, and no value, prompt text, write, or provider call leaks.

### Tests for User Story 2

> **Write these tests first and confirm the unsafe or unsupported cases fail before hardening.**

- [ ] T011 [US2] Add missing/invalid values, undeclared `variable__unknown` rejection, compiler/template failure, safe redisplay, no-partial-result, captured-log and response redaction of submitted values/full prompt text, repeated POST statelessness, no-write, CSRF, unauthenticated, non-staff, deleted-version, and unknown-version cases to `apps/server/prompts/tests/test_dashboard_playground.py`

### Implementation for User Story 2

- [ ] T012 [US2] Reject undeclared generated fields, map parsing failures and expected PromptKit missing/unexpected/type/template exceptions to actionable value-free form errors, discard all partial results, and prevent submitted values/full prompt text from entering logs across `apps/server/prompts/forms.py`, `apps/server/prompts/services/playground.py`, and `apps/server/prompts/views/dashboard.py`
- [ ] T013 [US2] Render preserved safe field values, field/non-field errors, and an explicit failure state without any preview region or unsafe markup in `apps/server/prompts/templates/prompts/playground.html`

**Checkpoint**: US1 success behavior and US2 correction behavior both work through the same protected Playground URL.

---

## Phase 5: User Story 3 - Prompt Server to Gemini E2E example (Priority: P2)

**Goal**: Provide one isolated consumer example that fetches an on-live prompt, compiles locally, converts through `GeminiAdapter`, and calls Gemini exactly once only with explicit `--live` consent.

**Independent Test**: Run fake-boundary tests for configuration, registry, compilation, adapter, non-live, live, provider-response, closure, and redaction behavior; then run the documented non-live command against a prepared local server and observe zero Gemini requests.

### Tests for User Story 3

> **Write these tests first; all provider and registry boundaries must be replaced so the suite remains offline and cost-free.**

- [ ] T014 [US3] Create orchestration tests in `tests/examples/test_gemini_e2e.py` covering stage order, omitted-label fetch, strict parameter JSON, stop-on-configuration/registry/compilation/adapter failure, zero Gemini import/construction/calls without `--live`, exactly one fake live call with no retry, client closure, non-empty/unexpected response handling, non-zero expected failures, and secret-safe output

### Implementation for User Story 3

- [ ] T015 [US3] Implement the typed synchronous CLI orchestration in `examples/gemini-e2e/gemini_e2e.py`: read environment configuration, fetch via `PromptKitClient.fetch(slug)` without fallback, compile locally, convert with `GeminiAdapter`, print only safe stage/source details, delay provider import and construction until `--live`, perform exactly one `generate_content` call, validate response text, close the client, and return stage-specific sanitized exit failures
- [ ] T016 [P] [US3] Document server/on-live prompt prerequisites, environment setup, isolated `uv` commands, responsibility boundaries, safe non-live behavior, explicit cost-bearing `--live` opt-in, expected stage output, and troubleshooting in `examples/gemini-e2e/README.md`

**Checkpoint**: US3 demonstrates the full consumer journey while keeping SDK/server free of LLM execution and default tests free of live calls.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Validate contracts across all stories and record any environment-limited checks.

- [ ] T017 [P] Run `uv run pytest apps/server/prompts/tests/test_dashboard_playground.py` and resolve only feature-related failures in the files changed by US1/US2
- [ ] T018 [P] Run `uv run pytest tests/examples/test_gemini_e2e.py` without live credentials and prove the test doubles observe zero real network/provider requests
- [ ] T019 Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy .`, and `uv run pytest`, resolving only regressions caused by this feature
- [ ] T020 Execute the non-live workflow from `specs/016-playground-e2e-example/quickstart.md` against a prepared local Prompt Server and record registry → compilation → adapter completion with zero Gemini calls in the implementation completion report; if the server prerequisites are unavailable, record the exact unmet prerequisite and mark this check unverified rather than passing it by assumption
- [ ] T021 After separate explicit authorization acknowledging network use and possible Gemini cost, execute the `--live` smoke workflow from `specs/016-playground-e2e-example/quickstart.md`, verify completion within the 10-minute SC-004 target and exactly one Gemini request with a non-empty response, and record sanitized evidence in the implementation completion report; without that authorization, record this check as explicitly deferred and do not make the request

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Starts immediately; T001, T002, and T003 can proceed in parallel.
- **Phase 2 (Foundational)**: Depends on Phase 1 and blocks all story implementation.
- **Phase 3 (US1)**: Depends on Phase 2 and supplies the MVP success path.
- **Phase 4 (US2)**: Depends on the US1 form/service/view/template integration because it hardens those same components.
- **Phase 5 (US3)**: Depends on Phase 1 and Phase 2 public SDK confirmation, but is otherwise independent of the Playground implementation.
- **Phase 6 (Validation)**: T017 depends on US1/US2, T018 depends on US3, T019 depends on both focused suites, T020 depends on the completed example plus a prepared local server, and T021 additionally depends on separate live-call authorization and valid Gemini credentials.

### User Story Dependencies

- **US1 (P1)**: Starts after Foundation; no dependency on US2 or US3.
- **US2 (P1)**: Builds on US1's shared Playground components but remains independently testable through invalid submissions.
- **US3 (P2)**: Uses the confirmed public SDK only; it can be developed in parallel with US1/US2 after Foundation.

### Within Each User Story

- Write the story test task first and verify the new assertions fail for the expected missing behavior.
- US1: form and ORM mapping may proceed in parallel, then view integration, then template rendering.
- US2: failure tests precede backend exception mapping and failure-state template rendering.
- US3: fake-boundary tests precede CLI implementation; documentation can proceed in parallel from the approved contracts.
- Never run the live Gemini smoke check as part of automated validation; T021 is a separately authorized manual check and otherwise ends as explicitly deferred.

### Parallel Opportunities

- T001, T002, and T003 touch independent dependency/configuration files.
- T007 and T008 implement independent form and mapping boundaries.
- US3 tasks can proceed alongside US1/US2 after T004.
- T016 can proceed alongside T015 because `contracts/gemini-e2e-cli.md` and `quickstart.md` define the approved behavior.
- T017 and T018 are independent focused test runs.

---

## Parallel Example: User Story 1

```text
Task T007: Implement dynamic typed form in apps/server/prompts/forms.py
Task T008: Implement ORM-to-SDK mapping in apps/server/prompts/services/playground.py
```

## Parallel Example: User Story 3

```text
Task T015: Implement examples/gemini-e2e/gemini_e2e.py after T014
Task T016: Document examples/gemini-e2e/README.md from the approved contract
```

---

## Implementation Strategy

### MVP First

1. Complete Setup and Foundation.
2. Complete US1 from T006 through T010.
3. Run the focused Playground test command from T017.
4. Stop and demonstrate the local, zero-write, zero-LLM compiled preview.

### Incremental Delivery

1. **US1**: Deliver valid local compilation preview.
2. **US2**: Add safe error correction without changing the success contract.
3. **US3**: Add the isolated, opt-in provider consumer journey.
4. **Polish**: Run focused and repository-wide gates, validate the non-live quickstart, and either perform the separately authorized live smoke check or explicitly record its deferral.

### Scope Guardrails

- Do not create database migrations or persistent preview records.
- Do not add an internal compile API or browser-side compiler.
- Do not add `google-genai` to the root, server, core SDK, or SDK extras.
- Do not log or display API keys, submitted mappings, full compiled prompts in errors, authorization headers, or provider arguments.
- Do not execute the live Gemini request without a separate explicit authorization acknowledging possible cost.
