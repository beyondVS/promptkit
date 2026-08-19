# Tasks: 모노레포 패키지 격리 및 상호 운용성 검증

**Input**: Design documents from `/specs/017-package-isolation-validation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [isolation-validation-contract.md](./contracts/isolation-validation-contract.md), [quickstart.md](./quickstart.md)

**Tests**: 수용 기준이 실제 artifact와 격리 설치 실행을 요구하므로 pytest 통합 테스트를 선행 작성한다.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 루트 pytest 수집 대상에 배포 검증 패키지를 준비한다.

- [X] T001 Create the deployment-test package marker in `tests/deployment/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 시나리오가 공유할 uv-only artifact/environment 실행 도구를 만든다.

**⚠️ CRITICAL**: 이 단계가 끝날 때까지 사용자 스토리 구현을 시작하지 않는다.

- [X] T002 Implement uv local-Git preflight, dependency acquisition, wheelhouse-only `--no-index --find-links` resolution, local Git snapshots, isolated environments, `PYTHONPATH` removal, and stage diagnostics in `tests/deployment/helpers.py`

**Checkpoint**: uv가 로컬 Git 서브디렉터리를 처리하며 각 시나리오가 새 wheelhouse, 전용 가상환경, 저장소 밖 작업 디렉터리를 만들 수 있다. preflight 실패 시 direct pip fallback 없이 prerequisite failure로 중단한다.

---

## Phase 3: User Story 1 - 개별 배포 단위 독립 검증 (Priority: P1) 🎯 MVP

**Goal**: 코어 SDK, Django 통합 패키지, Prompt Server를 각자의 wheel과 Git 서브디렉터리 경로로 격리 설치하고 artifact metadata와 최소 공개 동작을 입증한다.

**Independent Test**: `uv run pytest tests/deployment/test_isolated_installation.py -k "wheel or git"`를 실행하여 6개 단위/경로 시나리오가 저장소 source path 없이 통과한다.

### Tests for User Story 1

- [X] T003 [US1] Add failing six-path install, Prompt Server namespace, package-data, and artifact-metadata contract tests in `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 1

- [X] T004 [US1] Configure the Prompt Server installed namespace, complete package tree, templates, and migrations in `apps/server/pyproject.toml`
- [X] T005 [US1] Align all affected installed-runtime imports and startup references across `apps/server/config/`, `apps/server/core/`, `apps/server/prompts/`, and `apps/server/manage.py` only if T004 cannot preserve the existing `apps.server.*` namespace
- [X] T006 [US1] Validate wheel `Name`, `Version`, `Requires-Python`, `Requires-Dist`, public modules, and Prompt Server package data in `tests/deployment/test_isolated_installation.py`
- [X] T007 [US1] Implement the six artifact-install smoke scenarios, installed-distribution location assertions, and core fixture-backed compilation checks in `tests/deployment/test_isolated_installation.py`
- [X] T008 [US1] Run the six-scenario P1 matrix from `tests/deployment/test_isolated_installation.py` and record a passing result

**Checkpoint**: 세 배포 단위가 wheel과 local committed Git-subdirectory 설치를 모두 통과하며 metadata, namespace, templates, migrations가 검증된다.

---

## Phase 4: User Story 2 - 패키지 조합 상호 운용 검증 (Priority: P2)

**Goal**: 현재 동일 릴리스의 코어 SDK와 Django 통합 패키지가 두 요청 설치 순서 모두에서 동일한 공개 계약을 유지함을 보인다.

**Independent Test**: `uv run pytest tests/deployment/test_isolated_installation.py -k "sdk_django"`를 실행하여 core-first와 integration-first 결과가 일치하는지 확인한다.

### Tests for User Story 2

- [X] T009 [US2] Add failing core-first and integration-first interoperability scenarios with matching-version assertions in `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 2

- [X] T010 [US2] Implement ordered uv wheel installation, minimal Django setup, single-client registration, and equivalent installed-core compilation assertions in `tests/deployment/test_isolated_installation.py`
- [X] T011 [US2] Run the two-order interoperability matrix from `tests/deployment/test_isolated_installation.py` and record a passing result

**Checkpoint**: 두 설치 순서가 freshly built matching core artifact만 사용하고 동일한 공개 동작을 제공한다.

---

## Phase 5: User Story 3 - 재현 가능한 배포 격리 판정 (Priority: P3)

**Goal**: 한 번의 실행이 배포 단위·설치 방식·실패 단계·통과 여부를 요약하고 다른 시나리오를 오염시키지 않는 반복 가능한 판정을 제공한다.

**Independent Test**: focused matrix를 깨끗한 조건에서 두 번 실행하고 malformed artifact 실패가 `<scenario-id>:<stage>`로 귀속되며 두 결과 요약이 일치하는지 확인한다.

### Tests for User Story 3

- [X] T012 [US3] Add failing diagnostic, scenario-isolation, release-summary, and repeated-run result tests in `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 3

- [X] T013 [US3] Implement stage-prefixed subprocess reporting and non-mutating malformed-artifact seams in `tests/deployment/helpers.py`
- [X] T014 [US3] Implement matrix aggregation, per-scenario isolation, and repeated-run assertions in `tests/deployment/test_isolated_installation.py`
- [X] T015 [US3] Implement one-row-per-scenario release summary assertions for unit, installation kind, failed stage, and verdict in `tests/deployment/test_isolated_installation.py`
- [X] T016 [US3] Run the full focused matrix twice from `tests/deployment/test_isolated_installation.py` and record identical per-scenario verdicts

**Checkpoint**: 실패가 정확한 scenario/stage로 귀속되고 한 요약만으로 5분 이내 판정 가능한 결과가 두 실행에서 동일하다.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 소비자 문서와 프로젝트 하네스가 확정된 독립 배포 계약을 반영하는지 검증한다.

- [X] T017 [P] Document uv-only Prompt Server artifact and Git-subdirectory installation prerequisites in `apps/server/README.md`
- [X] T018 [P] Document the three-unit matrix, offline validation boundary, and focused command in `README.md`
- [X] T019 Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy .`, and `uv run pytest` from `pyproject.toml` and record passing results
- [X] T020 Run the focused release-decision command from `specs/017-package-isolation-validation/quickstart.md` and verify every summary row is present

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: starts immediately.
- **Phase 2**: depends on T001 and blocks every story.
- **US1**: depends on T002 and establishes valid artifacts.
- **US2**: depends on T007 because it reuses the artifact contract.
- **US3**: depends on T010 because it aggregates the complete supported matrix.
- **Polish**: depends on T016.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories after the foundation.
- **US2 (P2)**: reuses the artifact and isolation proof from US1.
- **US3 (P3)**: reuses the complete US1/US2 matrix for reporting and repeatability.

### Parallel Opportunities

- T017 and T018 can run in parallel after T016 because they modify distinct documentation files.
- Server namespace implementation is intentionally sequential after T003: T004 first attempts preservation, and T005 runs only if broader runtime-path alignment is required.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T002 and stop if the uv local-Git preflight fails.
2. Write T003 before production packaging changes.
3. Preserve the existing namespace through T004 where possible; execute T005 only when the artifact test proves broader alignment is necessary.
4. Complete T006-T008 and verify all six independent paths.

### Incremental Delivery

1. Deliver US1 artifact metadata and independent installation.
2. Deliver US2 two-order interoperability.
3. Deliver US3 stable, actionable release diagnostics.
4. Finish documentation and the standard quality harness.

## Notes

- Every package operation uses uv; direct pip fallback is prohibited.
- Third-party dependencies may be acquired before validation, but release-decision scenarios resolve only from their temporary wheelhouse.
- No task publishes packages, contacts external services, or changes production data.
- A failed run returns to the owning implementation task; validation tasks do not authorize unspecified “fix” edits.
