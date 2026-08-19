# Tasks: 모노레포 패키지 격리 및 상호 운용성 검증

**Input**: Design documents from `/specs/017-package-isolation-validation/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [isolation-validation-contract.md](./contracts/isolation-validation-contract.md), [quickstart.md](./quickstart.md)

**Tests**: 이 기능의 수용 기준은 새 배포 산출물과 격리 설치의 실제 실행이므로 pytest 통합 테스트를 선행 작성한다.

**Organization**: 작업은 사용자 스토리별로 분리되어 각 증분을 독립적으로 검증할 수 있다.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: 루트 pytest 수집 대상에 배포 검증 패키지를 준비한다.

- [ ] T001 Create the deployment-test package marker in `tests/deployment/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: 모든 격리 시나리오가 공유할 안전한 artifact/environment 실행 도구를 만든다.

**⚠️ CRITICAL**: 이 단계가 끝날 때까지 사용자 스토리 구현을 시작하지 않는다.

- [ ] T002 Implement isolated artifact, local Git snapshot, seeded environment, source-path removal, and stage-diagnostic helpers in `tests/deployment/helpers.py`

**Checkpoint**: 각 시나리오가 새 wheelhouse, 전용 가상환경, 저장소 밖 작업 디렉터리를 만들 수 있다.

---

## Phase 3: User Story 1 - 개별 배포 단위 독립 검증 (Priority: P1) 🎯 MVP

**Goal**: 코어 SDK, Django 통합 패키지, Prompt Server를 각자의 wheel과 Git 서브디렉터리 경로로 격리 설치해 최소 공개 동작을 입증한다.

**Independent Test**: `uv run pytest tests/deployment/test_isolated_installation.py -k "wheel or git"`를 실행하여 6개 단위/경로 시나리오가 저장소 source path 없이 통과한다.

### Tests for User Story 1

- [ ] T003 [US1] Add failing core SDK, Django integration, and Prompt Server wheel/Git-subdirectory scenario tests to `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 1

- [ ] T004 [P] [US1] Configure the complete installed Prompt Server package tree and non-code resources in `apps/server/pyproject.toml`
- [ ] T005 [P] [US1] Make the Prompt Server settings and startup path usable from an installed artifact in `apps/server/config/settings.py` and `apps/server/manage.py`
- [ ] T006 [US1] Implement the six artifact-install smoke scenarios, installed-distribution location assertions, and core fixture-backed compilation checks in `tests/deployment/test_isolated_installation.py`
- [ ] T007 [US1] Run and fix the P1 matrix command documented in `tests/deployment/test_isolated_installation.py`

**Checkpoint**: All three deployment units pass both wheel and local committed Git-subdirectory installation with no repository-root import, editable install, live service, or external database.

---

## Phase 4: User Story 2 - 패키지 조합 상호 운용 검증 (Priority: P2)

**Goal**: 현재 동일 릴리스의 코어 SDK와 Django 통합 패키지가 두 요청 설치 순서 모두에서 동일한 공개 계약을 유지함을 보인다.

**Independent Test**: `uv run pytest tests/deployment/test_isolated_installation.py -k "sdk_django"`를 실행하여 core-first와 integration-first의 최소 Django 초기화·SDK 공개 컴파일 결과가 일치하는지 확인한다.

### Tests for User Story 2

- [ ] T008 [US2] Add failing core-first and integration-first interoperability scenarios with matching-version assertions in `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 2

- [ ] T009 [US2] Implement ordered wheel installation, minimal Django setup, single-client registration, and equivalent installed-core compilation assertions in `tests/deployment/test_isolated_installation.py`
- [ ] T010 [US2] Run and fix the two-order interoperability matrix in `tests/deployment/test_isolated_installation.py`

**Checkpoint**: Both installation orders resolve only the freshly built matching core artifact and expose identical supported behavior.

---

## Phase 5: User Story 3 - 재현 가능한 배포 격리 판정 (Priority: P3)

**Goal**: 한 번의 실행이 배포 단위·시나리오·실패 단계를 식별하고, 다른 시나리오를 오염시키지 않는 재현 가능한 릴리스 판정을 제공한다.

**Independent Test**: focused matrix를 동일한 깨끗한 조건에서 두 번 실행하고, 누락 artifact와 누락 package-data를 모의한 helper 단위 실패가 `<scenario-id>:<stage>`로 귀속되는지 확인한다.

### Tests for User Story 3

- [ ] T011 [US3] Add failing diagnostic, scenario-isolation, and repeated-run result tests to `tests/deployment/test_isolated_installation.py`

### Implementation for User Story 3

- [ ] T012 [US3] Implement stage-prefixed subprocess failure reporting and non-mutating malformed-artifact test seams in `tests/deployment/helpers.py`
- [ ] T013 [US3] Implement matrix aggregation, per-scenario isolation, and repeated-run assertions in `tests/deployment/test_isolated_installation.py`
- [ ] T014 [US3] Run and fix the full focused matrix twice using `tests/deployment/test_isolated_installation.py`

**Checkpoint**: Failures name the impacted scenario and stage, and repeated full runs provide the same per-scenario verdicts.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: 소비자 문서와 프로젝트 하네스가 확정된 독립 배포 계약을 반영하는지 검증한다.

- [ ] T015 [P] Document Prompt Server artifact and Git-subdirectory installation prerequisites in `apps/server/README.md`
- [ ] T016 [P] Document the complete three-unit isolation matrix and focused command in `README.md`
- [ ] T017 Run `uv run ruff check`, `uv run ruff format --check`, `uv run mypy .`, and `uv run pytest` from `pyproject.toml`
- [ ] T018 Run the focused release decision command from `specs/017-package-isolation-validation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: starts immediately.
- **Phase 2**: depends on T001 and blocks every story because all scenarios use the helper.
- **US1 (Phase 3)**: depends on T002; it is the MVP and establishes valid artifacts for later work.
- **US2 (Phase 4)**: depends on T006 because it reuses the completed artifact and isolated-install contracts.
- **US3 (Phase 5)**: depends on T009 because it aggregates the complete supported matrix.
- **Polish (Phase 6)**: depends on T014.

### User Story Dependencies

- **US1 (P1)**: no dependency on other stories after the foundation.
- **US2 (P2)**: reuses the isolated artifact helpers and successful installation proof from US1.
- **US3 (P3)**: reuses the complete US1/US2 matrix to verify result attribution and reproducibility.

### Parallel Opportunities

- T004 and T005 can run in parallel after T003 because they modify distinct server packaging/runtime files.
- T015 and T016 can run in parallel after T014 because they modify distinct documentation files.
- Story phases are intentionally sequential: US2 depends on the artifact contract from US1, and US3 needs the full supported matrix from US2.

## Parallel Example: User Story 1

```text
After T003 has defined the expected artifact behavior, run in parallel:

Task: "Configure the complete installed Prompt Server package tree and non-code resources in apps/server/pyproject.toml"
Task: "Make the Prompt Server settings and startup path usable from an installed artifact in apps/server/config/settings.py and apps/server/manage.py"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete T001-T002 to establish isolated build/install primitives.
2. Write T003 and make the server distribution packageable through T004-T005.
3. Complete T006-T007 and verify all six independent installation paths.
4. Stop and assess the P1 checkpoint before adding cross-package order coverage.

### Incremental Delivery

1. Deliver US1: every deployment unit is independently installable through both required paths.
2. Deliver US2: core and Django integration are proven interoperable in both requested-install orders.
3. Deliver US3: the complete matrix produces stable, actionable release diagnostics.
4. Finish with docs and the repository's standard quality harness.

## Notes

- Every task follows the required checkbox, task ID, optional parallel, story-label, and file-path format.
- No task publishes packages, contacts external services, or changes production data.
- The server distribution change is limited to making the existing Prompt Registry application installable; it does not alter registry business behavior.
