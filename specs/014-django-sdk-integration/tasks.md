# Tasks: Django SDK Integration Setup

**Input**: Design documents from `/specs/014-django-sdk-integration/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [python-public-api.md](contracts/python-public-api.md), [quickstart.md](quickstart.md)

**Tests**: Required. The specification requires repeatable automated coverage for all public integration behavior and failure paths.

**Organization**: Tasks are grouped by user story so each increment is independently testable after the shared package foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with other marked tasks after its stated dependency is complete.
- **[Story]**: User-story traceability label.
- Every task includes an exact repository-relative file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the independently distributed package shell and make the workspace resolve it.

- [ ] T001 Create the `promptkit-django` PEP 621/Hatchling package metadata, direct Django/promptkit/Pydantic runtime dependencies, package README, and typed source marker in `packages/promptkit-django/pyproject.toml`, `packages/promptkit-django/README.md`, and `packages/promptkit-django/src/promptkit_django/py.typed`
- [ ] T002 Create the deliberate package root and test-package markers in `packages/promptkit-django/src/promptkit_django/__init__.py`, `tests/promptkit_django/__init__.py`, `tests/promptkit_django/unit/__init__.py`, and `tests/promptkit_django/integration/__init__.py`
- [ ] T003 Update the workspace resolution for the new distribution and verify reproducibility in `uv.lock`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the safe configuration and public-error boundaries used by every user story.

**⚠️ CRITICAL**: Complete this phase before lifecycle or packaging integration work.

- [ ] T004 [P] Add public, typed, credential-safe configuration and uninitialized error classes in `packages/promptkit-django/src/promptkit_django/exceptions.py`
- [ ] T005 [P] Write focused configuration-contract tests for missing, blank, wrong-type, unknown, unsafe URL, default timeout, and API-key redaction cases in `tests/promptkit_django/unit/test_configuration.py`
- [ ] T006 Implement the strict Pydantic `PROMPTKIT` mapping parser and core-client configuration-error normalization in `packages/promptkit-django/src/promptkit_django/configuration.py`
- [ ] T007 Export only the documented configuration/accessor/error public surface from `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: The package parses only `BASE_URL`, `API_KEY`, and optional `TIMEOUT`, and reports affected setting names without credential disclosure.

---

## Phase 3: User Story 1 - Configure PromptKit through the host project (Priority: P1) 🎯 MVP

**Goal**: A Django project declares one `PROMPTKIT` mapping and obtains a configured core SDK client without manual construction.

**Independent Test**: Configure a minimal Django Apps registry with valid settings, run startup, retrieve the registered client, and verify base URL/API-key construction behavior plus default timeout without a registry request.

- [ ] T008 [P] [US1] Write the minimal-Django startup contract tests for valid settings, omitted `TIMEOUT`, and immediate invalid-settings startup failure in `tests/promptkit_django/integration/test_django_lifecycle.py`
- [ ] T009 [US1] Implement eager settings validation and one client construction during Django application startup in `packages/promptkit-django/src/promptkit_django/apps.py`
- [ ] T010 [US1] Implement the documented `get_client()` accessor that resolves a completed integration registration without lazy construction in `packages/promptkit-django/src/promptkit_django/registry.py`
- [ ] T011 [US1] Document installation, `INSTALLED_APPS`, the `PROMPTKIT` mapping, defaults, and safe failure behavior in `packages/promptkit-django/README.md`

**Checkpoint**: A valid minimal host project can configure and access a client; malformed configuration stops startup and contains no API-key value.

---

## Phase 4: User Story 2 - Reuse one automatically registered SDK instance (Priority: P1)

**Goal**: Multiple application components reuse exactly one startup-registered client for each Django Apps registry.

**Independent Test**: Invoke startup/access repeatedly in one isolated registry and assert object identity; initialize a fresh registry and assert it does not reuse prior lifecycle state.

- [ ] T012 [P] [US2] Add lifecycle identity, repeated-ready idempotence, pre-initialization access, absent-app access, and fresh-registry isolation tests in `tests/promptkit_django/unit/test_registry.py`
- [ ] T013 [US2] Complete AppConfig-scoped registration guards and accessor error translation for repeated startup and unavailable registrations in `packages/promptkit-django/src/promptkit_django/apps.py` and `packages/promptkit-django/src/promptkit_django/registry.py`
- [ ] T014 [US2] Add the explicit `PromptKitDjangoConfig` application configuration and all supported public exports to `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: Repeated startup/access returns the identical client within one registry, while missing or incomplete initialization never constructs a client lazily.

---

## Phase 5: User Story 3 - Install the integration package independently (Priority: P1)

**Goal**: The Django integration can be installed from only its Git subdirectory with the declared core SDK dependency resolved as a distribution artifact.

**Independent Test**: Build the core wheel, commit a temporary Git snapshot containing only `packages/promptkit-django`, install its subdirectory into a fresh `uv` environment with the wheelhouse supplied, and run minimal Django startup/import assertions outside the repository import path.

- [ ] T015 [P] [US3] Write the isolated Git-subdirectory installation test that builds a core wheel, snapshots only the Django package, creates a fresh environment, installs with a temporary wheelhouse, and asserts installed distribution locations in `tests/promptkit_django/integration/test_git_subdirectory_install.py`
- [ ] T016 [US3] Adjust `packages/promptkit-django/pyproject.toml` packaging metadata and dependency bounds until the isolated installation test resolves `promptkit`, Django, and Pydantic without sibling paths or editable workspace resolution
- [ ] T017 [US3] Extend the installation usage and verification notes in `packages/promptkit-django/README.md` with the Git subdirectory command and the no-server/no-live-registry boundary

**Checkpoint**: A clean environment installs, imports, and initializes the Django integration from its Git subdirectory with no repository-root or Prompt Server source access.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the public package contract, workspace quality gates, and independently installable artifact together.

- [ ] T018 [P] Add public-export, `py.typed`, docstring, and secret-redaction regression assertions in `tests/promptkit_django/unit/test_public_api.py`
- [ ] T019 Run the focused package suite and full project test suite, recording and fixing only Day 14 failures: `tests/promptkit_django/` and `tests/`
- [ ] T020 Run formatting, linting, and static typing against the new package and tests: `packages/promptkit-django/`, `tests/promptkit_django/`, and `uv.lock`
- [ ] T021 Execute every scenario in `specs/014-django-sdk-integration/quickstart.md` and update only inaccurate validation commands or expected outcomes in that file

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** has no dependencies.
- **Phase 2** depends on T001–T003 and blocks every user-story phase.
- **US1** depends on T004–T007.
- **US2** depends on US1's AppConfig and accessor implementation (T009–T010).
- **US3** depends on the package metadata and the working public integration from US1–US2.
- **Polish** depends on every desired story checkpoint.

### User Story Dependencies

- **US1** delivers the MVP configuration-to-client path.
- **US2** extends the same public lifecycle contract with identity and isolation guarantees, so it follows US1.
- **US3** validates the finished package artifact and therefore follows US1 and US2.

### Parallel Opportunities

- T001, T002, and T003 can proceed in parallel when no lock update is actively running.
- T004 and T005 can run in parallel; T006 consumes their public contract.
- T008 may be prepared in parallel with foundational implementation once the expected contract is fixed.
- T012 can be written in parallel with the US1 documentation task T011 after T009–T010 behavior is available.
- T015 can be prepared in parallel with US2 tests but must execute after package behavior is complete.
- T018 can run in parallel with T019 after all implementation tasks are complete.

## Parallel Example: Foundational and US1

```text
Task: "T004 public integration errors in packages/promptkit-django/src/promptkit_django/exceptions.py"
Task: "T005 configuration contract tests in tests/promptkit_django/unit/test_configuration.py"

Then:
Task: "T008 minimal Django startup tests in tests/promptkit_django/integration/test_django_lifecycle.py"
Task: "T011 package usage documentation in packages/promptkit-django/README.md"
```

## Implementation Strategy

### MVP First (US1)

1. Finish package metadata and strict configuration foundation.
2. Implement and test eager AppConfig registration plus `get_client()`.
3. Stop at the US1 checkpoint and run its focused lifecycle tests.

### Incremental Delivery

1. Add US2 identity and fresh-registry isolation checks without changing the core SDK.
2. Add US3 isolated artifact installation validation.
3. Run the full validation phase only after every public contract is covered.

### Scope Boundaries

- Do not modify `packages/promptkit` behavior or add a Django dependency to it.
- Do not add caching, retry, prompt CUD, provider calls, LLM invocation, or runtime reconfiguration.
- Do not use a process-global singleton or expose credential values in errors/logs.
