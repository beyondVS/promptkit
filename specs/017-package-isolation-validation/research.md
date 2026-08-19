# Phase 0 Research: 모노레포 패키지 격리 및 상호 운용성 검증

## Decision 1: Use a pytest deployment-isolation harness under `tests/deployment/`

**Rationale**: Root pytest discovery already targets `tests/`, while server-internal tests are not included in a default test run. A single focused harness can create fresh artifacts and attribute a failure to the exact deployment unit and validation stage.

**Alternatives considered**:

- Extend separate package integration tests: rejected because the matrix would duplicate environment/snapshot code and cannot produce one release decision.
- Use an external CI workflow only: rejected because local reproducibility and ordinary pytest failure diagnostics are required.

## Decision 2: Validate both built wheels and Git-subdirectory installation from local snapshots

**Rationale**: A wheel proves included files and installed metadata; a local committed Git snapshot with `#subdirectory=` proves the constitutional installation path. Each scenario must run from outside the repository with `PYTHONPATH` removed and assert that imported distributions reside in its isolated environment.

**Alternatives considered**:

- Git installation only: rejected because it can hide missing wheel package data.
- Wheel installation only: rejected because it omits the required Git-subdirectory consumer path.
- Editable installs: rejected by FR-010 because they expose repository source.

## Decision 3: Build all three units into a temporary wheelhouse and supply unpublished core dependencies from it

**Rationale**: `promptkit-django` and Prompt Server declare `promptkit`, but project policy does not publish core to an index. A fresh core wheel supplied with `--find-links` is a real artifact dependency and does not leak a workspace import into consumer scenarios.

**Alternatives considered**:

- Resolve `promptkit` from a public index: rejected because it is not the stated distribution policy.
- Add the repository root to imports: rejected because it invalidates isolation.
- Change this feature into package-index publication: rejected as out of scope.

## Decision 4: Use uv for environment creation and every package operation

**Rationale**: Project policy requires uv-only package management. `uv venv --seed` creates each environment and `uv pip install --python <environment-python>` installs wheels and local Git-subdirectory sources. The current uv version must pass a local `git+file` preflight before implementation proceeds; a failure is reported as a blocked prerequisite rather than silently falling back to direct pip.

**Alternatives considered**:

- Invoke the seeded interpreter's pip directly: rejected because it violates the uv-only project rule.
- Skip local Git verification on Windows: rejected because it would leave the key contract untested.
- Use remote Git URLs: rejected because it adds network availability and external state to the test.

## Decision 5: Separate dependency acquisition from offline artifact validation

**Rationale**: Third-party dependencies may be acquired into a temporary wheelhouse with uv before the scenario begins. Each release-decision scenario then installs with `--no-index --find-links <wheelhouse>` so package-index availability cannot alter its verdict and unpublished `promptkit` resolves only from the freshly built core wheel.

**Alternatives considered**:

- Leave package-index access enabled during scenarios: rejected because it makes results dependent on external state.
- Vendor third-party dependencies into the repository: rejected as unnecessary scope and maintenance cost.

## Decision 6: Make the Prompt Server distribution self-contained before validating it

**Rationale**: Its current wheel target includes only `config`, while settings and URLs import `apps.server.core` and `apps.server.prompts`; templates and migrations also need package-data coverage. The source-tree-only `manage.py` path setup cannot be the installed distribution contract. Packaging must include the complete server package tree and resources and expose an installed-runtime-safe settings/health-check path.

**Alternatives considered**:

- Treat the server as workspace-only: rejected by the clarified three-unit scope.
- Smoke test only source checkout: rejected because it does not prove the artifact.

## Decision 7: Keep smoke behavior local and network/database-service free

**Rationale**: Core compilation can use a local transport/fixture payload; the Django integration can initialize minimal settings and compile a `RetrievedPrompt`; the server can run its database-independent health endpoint with an ephemeral configuration. This verifies packaging without external calls or production data.

**Alternatives considered**:

- Start a real registry or call an external service: rejected by FR-011 and the feature scope.
