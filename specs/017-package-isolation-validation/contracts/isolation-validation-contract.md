# Isolation Validation Contract

This is an internal test-harness contract, not a public runtime API.

## Scenario matrix

| Scenario ID | Unit(s) | Installation path | Required observable |
|---|---|---|---|
| `promptkit-wheel` | Core SDK | Fresh built wheel | Package-root import and fixture-backed compile succeed; Django and provider SDKs are absent |
| `promptkit-git` | Core SDK | Local committed Git snapshot, `packages/promptkit` | Same core public smoke succeeds from installed files |
| `promptkit-django-wheel` | Django integration + matching core wheel | Fresh built wheels | Minimal Django initialization and single registered client succeed |
| `promptkit-django-git` | Django integration Git snapshot + matching core wheel | Local committed Git snapshot, `packages/promptkit-django` | Minimal Django initialization succeeds from installed files |
| `server-wheel` | Prompt Server + matching core wheel | Fresh built wheel | Installed settings load and health endpoint returns local success response |
| `server-git` | Prompt Server Git snapshot + matching core wheel | Local committed Git snapshot, `apps/server` | Same installed server smoke succeeds |
| `sdk-django-core-first` | Core SDK + Django integration | Fresh wheels | Core requested before integration; public compile contract succeeds |
| `sdk-django-integration-first` | Core SDK + Django integration | Fresh wheels | Integration requested before core; final public contract matches core-first |

## Isolation invariants

- Each scenario uses a distinct temporary virtual environment and working directory.
- Child processes remove inherited `PYTHONPATH` and do not run from repository root.
- No scenario uses an editable install, source-path injection, package index lookup for unpublished core, external Prompt Server, or non-temporary database service.
- Child-process assertions inspect installed distribution locations and reject locations outside the scenario environment.

## Failure contract

Harness errors identify `<scenario-id>:<stage>` before subprocess diagnostics. Stages are `build`, `install`, `import`, `smoke`, and `interoperability`. A failed scenario does not prevent independent scenarios from producing their own result.

## Artifact metadata contract

- Every wheel reports its intended distribution name and current version.
- `promptkit-django` and server resolve matching core only through declared dependency metadata and the scenario wheelhouse.
- The server artifact includes packages and non-code resources required by installed settings and health smoke.
