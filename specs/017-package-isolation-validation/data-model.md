# Phase 1 Data Model: 배포 격리 검증

This feature adds no persistent application data. These are in-memory test-harness entities.

## DeploymentUnit

| Field | Meaning | Validation |
|---|---|---|
| identifier | Stable prefix: `promptkit`, `promptkit-django`, or `server` | Exactly one supported unit |
| source_subdirectory | Repository-relative package location | Points to that unit's `pyproject.toml` |
| distribution_name | Installed distribution name | Matches built artifact metadata |
| public_smoke | Minimal consumer-visible action | Needs no repository source, live service, or production credentials |

## DistributionArtifact

| Field | Meaning | Validation |
|---|---|---|
| unit | Owning `DeploymentUnit` | Required |
| kind | `wheel` or `git-subdirectory` | Required |
| location | Temporary wheel path or local Git URL | Created during the scenario |
| version | Artifact metadata version | Satisfies declared current-release dependency constraints |

## IsolatedScenario

| Field | Meaning | Validation |
|---|---|---|
| identifier | Deployment/unit/path/stage identifier | Unique in a test run |
| requested_install_order | One unit or ordered SDK/Django pair | Pair scenarios include both supported orders |
| environment_path | Fresh seeded virtual environment | Not reused by another scenario |
| working_directory | Directory outside repository root | Required for child process |
| dependency_artifacts | Explicit artifacts supplied to resolver | Built artifacts only, never workspace source paths |

## VerificationResult

| Field | Meaning | Validation |
|---|---|---|
| scenario | Source `IsolatedScenario` | Required |
| stage | `build`, `install`, `import`, `smoke`, or `interoperability` | Required |
| outcome | Pass or fail | Failure message includes unit and stage |
| distribution_locations | Installed distribution locations inspected by child process | Every location is inside the scenario environment |

## Relationships and lifecycle

1. A `DeploymentUnit` creates one or more fresh `DistributionArtifact` values.
2. An `IsolatedScenario` receives only its declared artifacts and creates its own environment.
3. The harness evaluates ordered `VerificationResult` stages and stops that scenario on the first failure while leaving other scenarios unaffected.
4. The final matrix aggregates results by scenario without persisting them outside test output.
