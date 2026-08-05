# Research: Prompt Management Dashboard

## Decision: Default SDK lookup resolves on-live, not a label

**Rationale**: The feature specification defines on-live as the single deployable version per prompt and explicitly disallows the `production` label. A label omitted from the SDK request therefore resolves the on-live published version only. If none is on-live, the API returns a documented no-deployable-version result and never falls back to a draft, `latest`, or a custom label.

**Alternatives considered**:

- Keep `production` as an alias: rejected because it duplicates on-live and contradicts the feature specification.
- Fall back to `latest`: rejected because latest publication is not necessarily deployed.

## Decision: Publish is an irreversible lifecycle transition

**Rationale**: A published version is an immutable release record. Changes start by cloning either a draft or published source into a new draft. Only drafts may be edited or deleted.

**Alternatives considered**:

- Roll a published version back to draft: rejected because it invalidates release history and published-only labels.
- Edit the most recent version in place: rejected because it breaks immutable history.

## Decision: Labels point only to published versions

**Rationale**: Explicit label lookups must not expose a draft through the read-only SDK API. `latest` is a system label that moves when a version is published; custom labels are unique within a prompt and may be moved only through an explicit target-change action.

**Alternatives considered**:

- Permit draft labels: rejected because it creates an external draft exposure path.
- Auto-move duplicate custom labels: rejected because it can silently change a deployed consumer's target.

## Decision: Prompt identity uses stable slug plus category-scoped display name

**Rationale**: The SDK route already uses a global slug. Keep it as the stable external identifier while making the human-facing prompt name unique only within its category, as required by the feature specification.

**Alternatives considered**:

- Use the name as SDK identity: rejected because identical names may exist in different categories.
- Retain global name uniqueness: rejected because it contradicts the approved category-scoped rule.

## Decision: Use relational constraints and transactional writes for lifecycle integrity

**Rationale**: Django ORM constraints enforce per-prompt version and label uniqueness, while transactional on-live changes prevent two versions from becoming live simultaneously. A revision or timestamp comparison protects against stale dashboard writes.

**Alternatives considered**:

- Validate only in views: rejected because concurrent requests can bypass application-only checks.
- Last-write-wins editing: rejected because the specification requires conflict detection.

## Decision: Treat template validation as registry validation, rendering as SDK work

**Rationale**: The server validates only the supported roles, declared variable references, and type-compatible defaults. It does not compile prompts. The SDK continues to render `{{ variable_name }}` references.

**Alternatives considered**:

- Server-side rendering preview as part of this feature: rejected by the SDK compilation principle.
- Permit unrecognized references until runtime: rejected because drafts must be valid before publication.

## Decision: Resolve route duplication before changing the SDK contract

**Rationale**: Current nested includes can expose the SDK route as `/api/v1/v1/...` and through dashboard paths. The target contract has one public API prefix and one dashboard prefix.

**Alternatives considered**:

- Document the existing nested route: rejected because it disagrees with existing consumers and obscures authorization boundaries.
