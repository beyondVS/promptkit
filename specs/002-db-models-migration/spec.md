# Feature Specification: DB Modeling and Migrations for Prompt Specification

**Feature Branch**: `002-db-models-migration`

**Created**: 2026-07-27

**Status**: Draft

**Input**: User description: "Day 02 (1h): DB 모델링 및 마이그레이션 - 프롬프트 명세를 위한 Django ORM 모델 설계 (Prompt, Version, Label, VariableDefinition, Section 모델). 각 모델간의 관계 설정(1:N) 및 마이그레이션 실행."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prompt & Version Core Entity Storage (Priority: P1)

As a prompt manager or system administrator, I want to store top-level prompt definitions and maintain immutable version records for each prompt, so that every change to a prompt can be safely tracked and retrieved over time.

**Why this priority**: Core prompt registration and versioning form the foundational data structure of PromptKit. Without this, no prompt retrieval or label-based resolution can exist.

**Independent Test**: Can be tested independently by creating a prompt entity and adding multiple version records under it, verifying that prompt metadata and versions are correctly linked and queryable.

**Acceptance Scenarios**:

1. **Given** a new prompt definition request, **When** a user creates a prompt with a unique identifier and description, **Then** the prompt is saved and ready to accept version records.
2. **Given** an existing prompt definition, **When** a user registers a new version for that prompt, **Then** the new version is independently stored and associated with the parent prompt via a 1:N relationship without altering previous versions.
3. **Given** an existing version record, **When** attempts are made to update core version payload attributes, **Then** historical consistency is preserved through version immutability standards.

---

### User Story 2 - Label-Based Version Tagging & Resolution (Priority: P2)

As an application developer using the PromptKit registry, I want to assign release labels (e.g., `production`, `draft`, `dev`, `experiment`) to specific prompt versions, so that runtime clients can query prompts by label without needing explicit numeric version identifiers.

**Why this priority**: Label-driven resolution is a core architectural principle (Constitution Principle IV), enabling smooth deployment and testing of prompt changes across environments.

**Independent Test**: Can be tested independently by creating multiple versions of a prompt, assigning different labels (such as `production` and `draft`) to specific versions, and querying versions by label.

**Acceptance Scenarios**:

1. **Given** a prompt with multiple versions, **When** a `production` label is assigned to a specific version, **Then** querying for the prompt's active production version resolves to that exact version.
2. **Given** a prompt version with an existing label, **When** the label is reassigned to a newer version of the same prompt, **Then** the label reference is updated so that only one version of that prompt holds that unique label context at a time.
3. **Given** a prompt query where no label parameter is specified, **When** the registry processes the request, **Then** it defaults to resolving the version tagged with the `production` label.

---

### User Story 3 - Variable Definitions & Prompt Structure Sections (Priority: P3)

As a prompt designer, I want to define typed dynamic variables (e.g., input parameter name, type, default value) and structural prompt sections (e.g., system context, user message template, role order) for each prompt version, so that clients can safely validate inputs and render structured prompts.

**Why this priority**: Enables variable validation and multi-section/modular prompt composition required for advanced LLM interactions.

**Independent Test**: Can be tested independently by defining variable definitions and sections for a given prompt version, and verifying that variable specifications and section orderings are accurately stored and linked to the version.

**Acceptance Scenarios**:

1. **Given** a prompt version, **When** dynamic variable parameters (name, data type, required flag, default value) are attached to the version, **Then** they are stored in a 1:N relationship under that version.
2. **Given** a prompt version, **When** multiple prompt sections with explicit roles and ordering sequence are added, **Then** the sections are persisted and maintain their designated execution sequence for assembly.

---

### Edge Cases

- What happens when a prompt is deleted? (All associated versions, labels, variables, and sections must handle deletion according to cascading rules to prevent orphaned records).
- How does the system handle duplicate variable names within the same prompt version? (Variable names must be unique within a single version context).
- How does the system handle duplicate label assignment within the same prompt? (A specific label like `production` must point to at most one version per prompt).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store `Prompt` entities containing unique identifying names, descriptions, and creation/update timestamps.
- **FR-002**: System MUST store `Version` entities linked to a parent `Prompt` in a 1:N relationship, tracking incremental version numbers, template content, and metadata.
- **FR-003**: System MUST store `Label` entities linked to a specific `Prompt` and `Version` in a 1:N relationship per prompt, allowing environment/release tagging (e.g., `production`, `draft`, `dev`, `experiment`).
- **FR-004**: System MUST enforce that a specific label name (e.g., `production`) is unique per prompt, ensuring a label points to exactly one active version at a time for a given prompt.
- **FR-005**: System MUST store `VariableDefinition` entities linked to a specific `Version` in a 1:N relationship, specifying variable names, data types, optional default values, and required flags.
- **FR-006**: System MUST enforce unique variable names within the scope of a single `Version`.
- **FR-007**: System MUST store `Section` entities linked to a specific `Version` in a 1:N relationship, retaining section role/type, ordering position index, and template content block.
- **FR-008**: System MUST provide schema migrations to initialize and apply database table structures and constraints cleanly.

### Key Entities

- **Prompt**: The top-level root concept representing a managed prompt asset (e.g., "customer-support-agent"). Attributes include unique identifier/slug, human-readable name, description, created_at, and updated_at.
- **Version**: A immutable snapshot of a prompt's content and structure. Belongs to a single Prompt (1:N). Attributes include version number/identifier, raw prompt body/template, change summary, and created_at.
- **Label**: A pointer tag (e.g., `production`, `staging`, `draft`) referencing a specific Version of a Prompt. Belongs to a Prompt and Version (1:N relationship to Prompt, 1:N relationship to Version).
- **VariableDefinition**: Specification of a dynamic input placeholder expected by a Version. Belongs to a Version (1:N). Attributes include variable name, parameter type (string, integer, etc.), required flag, and default value.
- **Section**: A structural segment of a modular or multi-role prompt within a Version. Belongs to a Version (1:N). Attributes include role/type (system, user, assistant), ordering index, and content block.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of defined entities (`Prompt`, `Version`, `Label`, `VariableDefinition`, `Section`) and their 1:N relationships can be initialized via database migration without errors.
- **SC-002**: Prompt version queries by label resolve the target version record with zero data ambiguity.
- **SC-003**: Cascading integrity checks prevent orphaned records when parent entity operations occur.
- **SC-004**: Database operations across all 5 entities pass comprehensive automated model test suites with 100% coverage on ORM relationships and constraints.

## Assumptions

- **Database Engine**: PostgreSQL or standard relational storage capable of enforcing foreign key constraints and unique indexes.
- **Immutability of Versions**: Once a `Version` record is created, its core content payload is treated as immutable; updates or iterations result in a new `Version` record.
- **Default Production Fallback**: Querying for a prompt without specifying a version or label defaults to resolving the `production` label version.
- **Out of Scope**: LLM API calls, prompt execution rendering/compilation logic, and analytics dashboards are handled outside the database model scope.
