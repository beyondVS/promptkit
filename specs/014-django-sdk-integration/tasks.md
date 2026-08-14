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

- [X] T001 Create the `promptkit-django` PEP 621/Hatchling package metadata with direct `Django>=5,<6`, `promptkit>=0.1,<0.2`, and `pydantic>=2,<3` runtime bounds, package README, and typed source marker in `packages/promptkit-django/pyproject.toml`, `packages/promptkit-django/README.md`, and `packages/promptkit-django/src/promptkit_django/py.typed`
- [X] T002 Create the deliberate package root and test-package markers in `packages/promptkit-django/src/promptkit_django/__init__.py`, `tests/promptkit_django/__init__.py`, `tests/promptkit_django/unit/__init__.py`, and `tests/promptkit_django/integration/__init__.py`
- [X] T003 After T001, update the workspace resolution for the new distribution and verify reproducibility in `uv.lock`
- [X] T004 Immediately after T001–T003, add and run a packaging smoke test that builds the core SDK wheel, snapshots only `packages/promptkit-django`, installs its Git subdirectory with the wheelhouse, and fails the scaffold gate on metadata, dependency-resolution, installation, or import errors in `tests/promptkit_django/integration/test_git_subdirectory_install.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the safe configuration and public-error boundaries used by every user story.

**⚠️ CRITICAL**: Complete this phase before lifecycle or packaging integration work.

- [X] T005 [P] Add public, typed, credential-safe configuration and uninitialized error classes in `packages/promptkit-django/src/promptkit_django/exceptions.py`
- [X] T006 [P] Write focused configuration-contract tests for missing, blank, wrong-type, unsafe URL, default timeout, aggregated reporting of every affected or unknown key, and non-disclosure when API keys contain whitespace or non-ASCII characters in `tests/promptkit_django/unit/test_configuration.py`
- [X] T007 Implement the strict Pydantic `PROMPTKIT` mapping parser and core-client configuration-error normalization in `packages/promptkit-django/src/promptkit_django/configuration.py`

**Checkpoint**: The package parses only `BASE_URL`, `API_KEY`, and optional `TIMEOUT`, and reports affected setting names without credential disclosure.

---

## Phase 3: User Story 1 - Configure PromptKit through the host project (Priority: P1) 🎯 MVP

**Goal**: A Django project declares one `PROMPTKIT` mapping and obtains a configured core SDK client without manual construction.

**Independent Test**: Configure a minimal Django Apps registry with valid settings, run startup, retrieve the registered client, and verify base URL/API-key construction behavior plus default timeout without a registry request.

- [X] T008 [P] [US1] Write the minimal-Django startup contract tests for valid settings, omitted `TIMEOUT`, deployment/test settings overrides in fresh Apps registries, and immediate invalid-settings startup failure in `tests/promptkit_django/integration/test_django_lifecycle.py`
- [X] T009 [US1] Implement eager settings validation and one client construction during Django application startup in `packages/promptkit-django/src/promptkit_django/apps.py`
- [X] T010 [US1] Implement the documented `get_client()` accessor that resolves a completed integration registration without lazy construction in `packages/promptkit-django/src/promptkit_django/registry.py`
- [X] T011 [US1] Document installation, `INSTALLED_APPS`, the `PROMPTKIT` mapping, defaults, and safe failure behavior in `packages/promptkit-django/README.md`

**Checkpoint**: A valid minimal host project can configure and access a client; malformed configuration stops startup and contains no API-key value.

---

## Phase 4: User Story 2 - Reuse one automatically registered SDK instance (Priority: P1)

**Goal**: Multiple application components reuse exactly one startup-registered client for each Django Apps registry.

**Independent Test**: Invoke startup/access repeatedly in one isolated registry and assert object identity; initialize a fresh registry and assert it does not reuse prior lifecycle state.

- [X] T012 [P] [US2] Add lifecycle identity, repeated-ready idempotence, pre-initialization access, absent-app access, and fresh-registry isolation tests in `tests/promptkit_django/unit/test_registry.py`
- [X] T013 [US2] Complete AppConfig-scoped registration guards and accessor error translation for repeated startup and unavailable registrations in `packages/promptkit-django/src/promptkit_django/apps.py` and `packages/promptkit-django/src/promptkit_django/registry.py`
- [X] T014 [US2] Add the explicit `PromptKitDjangoConfig` application configuration and all supported public exports to `packages/promptkit-django/src/promptkit_django/__init__.py`

**Checkpoint**: Repeated startup/access returns the identical client within one registry, while missing or incomplete initialization never constructs a client lazily.

---

## Phase 5: User Story 3 - Install the integration package independently (Priority: P1)

**Goal**: The Django integration can be installed from only its Git subdirectory with the declared core SDK dependency resolved as a distribution artifact.

**Independent Test**: Build the core wheel, commit a temporary Git snapshot containing only `packages/promptkit-django`, install its subdirectory into a fresh `uv` environment with the wheelhouse supplied, and run minimal Django startup/import assertions outside the repository import path.

- [X] T015 [US3] Extend the scaffold smoke test into the full isolated lifecycle test by asserting installed distribution locations, public imports, minimal `django.setup()`, and repeated `get_client()` identity without repository-root or server paths in `tests/promptkit_django/integration/test_git_subdirectory_install.py`
- [X] T016 [US3] Verify the exact metadata and dependency bounds declared by T001 against the full isolated test, and correct only demonstrated packaging defects without adding sibling paths, direct Git dependencies, or editable workspace resolution in `packages/promptkit-django/pyproject.toml`
- [X] T017 [US3] Extend the installation usage and verification notes in `packages/promptkit-django/README.md` with the Git subdirectory command and the no-server/no-live-registry boundary

**Checkpoint**: A clean environment installs, imports, and initializes the Django integration from its Git subdirectory with no repository-root or Prompt Server source access.

---

## Phase 6: Polish & Cross-Cutting Validation

**Purpose**: Verify the public package contract, workspace quality gates, and independently installable artifact together.

- [X] T018 Add public-export, `py.typed`, docstring, and secret-redaction regression assertions in `tests/promptkit_django/unit/test_public_api.py`
- [X] T019 After T018, run the focused package suite and full project test suite, recording and fixing only Day 14 failures: `tests/promptkit_django/` and `tests/`
- [X] T020 Run Ruff formatting/linting and MyPy validation for `packages/promptkit-django/` and `tests/promptkit_django/`, then separately verify locked workspace synchronization against `uv.lock`
- [X] T021 Execute every scenario in `specs/014-django-sdk-integration/quickstart.md` and update only inaccurate validation commands or expected outcomes in that file

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** has no dependencies.
- **T003** depends on T001; **T004** depends on T001–T003 and is the immediate package-scaffold gate required by FR-016.
- **Phase 2** depends on successful completion of T004 and blocks every user-story phase.
- **US1** depends on T005–T007.
- **US2** depends on US1's AppConfig and accessor implementation (T009–T010).
- **US3** depends on the package metadata and the working public integration from US1–US2.
- **Polish** depends on every desired story checkpoint.

### User Story Dependencies

- **US1** delivers the MVP configuration-to-client path.
- **US2** extends the same public lifecycle contract with identity and isolation guarantees, so it follows US1.
- **US3** validates the finished package artifact and therefore follows US1 and US2.

### Parallel Opportunities

- T001 and T002 can proceed in parallel; T003 must wait for T001, and T004 must wait for T001–T003.
- T005 and T006 can run in parallel; T007 consumes their public contract.
- T008 may be prepared in parallel with foundational implementation once the expected contract is fixed.
- T012 can be written in parallel with the US1 documentation task T011 after T009–T010 behavior is available.
- T015 starts only after the US2 checkpoint because it extends the shared T004 installation test with the completed lifecycle behavior.
- T020 can run independently of T019 after T018 and all implementation tasks are complete.

## Parallel Example: Foundational and US1

```text
Task: "T005 public integration errors in packages/promptkit-django/src/promptkit_django/exceptions.py"
Task: "T006 configuration contract tests in tests/promptkit_django/unit/test_configuration.py"

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
