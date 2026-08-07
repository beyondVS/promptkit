# Research: SDK Remote Prompt Retrieval

## Decision: Use httpx for the synchronous transport

- **Decision**: Declare `httpx` as a runtime package dependency and use a synchronous client with redirects disabled and environment-derived proxy configuration disabled.
- **Rationale**: The project SDK requirements already name httpx. It supports a reusable synchronous client, explicit default/caller-supplied timeout, transport injection, and direct testability through `httpx.MockTransport` without a separate mock-server dependency.
- **Alternatives considered**:
  - Standard-library `urllib`: avoids an extra dependency but needs custom redirect-handler and error-mapping plumbing, and conflicts with the existing SDK requirement.
  - `requests`: adds a dependency without an advantage over the project-specified transport.

## Decision: Use Pydantic v2 models for received prompt data

- **Decision**: Model the successful registry response with Pydantic v2 and configure models to ignore unknown response fields while requiring every documented field used by the SDK.
- **Rationale**: This satisfies the constitution's Pydantic requirement, prevents partial prompt use, and permits additive server response changes.
- **Alternatives considered**:
  - Untyped dictionaries: would make response validation and public API guarantees ambiguous.
  - Rejecting every unknown field: would make the independently deployed SDK unnecessarily fragile to additive server changes.

## Decision: Treat the active server serializer as the retrieval contract

- **Decision**: Build the SDK contract from `apps/server/prompts/views/api.py` and `SDKPromptFetchResponseSerializer`, with `apps/server/prompts/tests/test_read_only_api.py` as behavior evidence.
- **Rationale**: The durable `docs/sdk-read-api-contract.md` currently describes fields and ETag/304 behavior not emitted by the active endpoint. The SDK must interoperate with the code that is deployed and tested.
- **Alternatives considered**:
  - Implement against the durable document's sample response: rejected because its `version_number`, `status`, `revision`, `labels`, and `updated_at` fields are not produced by the active serializer.
  - Add ETag caching now: rejected because the feature explicitly excludes caching and the server does not implement conditional responses.

## Decision: Map response failures to typed, non-fallback exceptions

- **Decision**: Preflight invalid inputs and map the current server's response/status semantics to public SDK errors. In particular, distinguish unknown slug, no on-live deployable version, unavailable explicit label, authentication failure, rate limit, redirect, communication failure, and invalid response.
- **Rationale**: The feature requires actionable outcomes and prohibits silent fallback. The active server already distinguishes an unknown slug, `no_deployable_version`, and `label_not_found` in its payload behavior.
- **Alternatives considered**:
  - Return `None` for every unsuccessful fetch: rejected because the caller cannot recover safely or tell whether credentials, a label, or availability caused the result.
  - Retry requests automatically: rejected by clarification; the caller owns retry policy.

## Decision: Validate transport safety before network access

- **Decision**: Accept HTTPS registry URLs and HTTP only for loopback hosts; reject `production` labels before a request; reject all 3xx responses; use an explicit API key passed to client construction.
- **Rationale**: These decisions preserve credential confidentiality and the project label policy while keeping the SDK self-hosting-friendly for local development.
- **Alternatives considered**:
  - Permit arbitrary HTTP: rejected because the API key could cross an unencrypted network.
  - Follow redirects: rejected because credentials could be sent to an unintended destination.
  - Automatically read credentials from environment variables: rejected by clarification; callers may read their own configuration and pass it explicitly.

## Decision: Verify package isolation in two stages

- **Decision**: First validate package build/install from its local directory during implementation. After the package files are committed, validate actual Git subdirectory installation from a temporary virtual environment using a local Git URL and `#subdirectory=packages/promptkit`.
- **Rationale**: Git-based installation uses committed `HEAD` content and cannot prove uncommitted package files. A local Git URL verifies the same subdirectory mechanism without requiring a remote push.
- **Alternatives considered**:
  - Install the monorepo root: rejected because it would hide package isolation errors.
  - Use a remote Git URL during planning: rejected because it depends on pushed external state and does not validate the uncommitted implementation.
