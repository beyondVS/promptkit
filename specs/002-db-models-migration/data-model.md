# Data Model Specification: Prompt Registry Entities

## Entity Relationship Overview

```
+------------------+           1:N           +---------------------+
|      Prompt      | -----------------------> |       Version       |
| (slug, name, ...) |                         | (version_number, ..)|
+------------------+                         +---------------------+
         |                                              |
         | 1:N                                1:N       |       1:N
         v                                   +----------+----------+
+------------------+                         |                     |
|      Label       |                         v                     v
| (name, version)  |               +------------------+  +------------------+
+------------------+               |VariableDefinition|  |     Section      |
                                   | (name, var_type) |  | (role, order, ..)|
                                   +------------------+  +------------------+
```

---

## Entity Details

### 1. `Prompt`
Top-level container for a prompt asset in the registry.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Unique internal ID |
| `slug` | CharField(100) | Unique=True, db_index=True | Canonical string identifier (e.g. `customer-support`) |
| `name` | CharField(255) | Required | Human-readable name |
| `description` | TextField | Blank=True | Detailed description of prompt purpose |
| `created_at` | DateTimeField | auto_now_add=True | Timestamp of creation |
| `updated_at` | DateTimeField | auto_now=True | Timestamp of last modification |

### 2. `Version`
Immutable snapshot of a prompt template and configuration.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Unique internal version ID |
| `prompt` | ForeignKey | `Prompt`, on_delete=CASCADE, related_name='versions' | Parent Prompt reference |
| `version_number` | PositiveIntegerField | Required | Sequential version number (1, 2, 3...) |
| `template_text` | TextField | Blank=True | Full raw template text body |
| `changelog` | TextField | Blank=True | Version release notes or commit message |
| `created_at` | DateTimeField | auto_now_add=True | Timestamp when version was created |

**Constraints**:
- `UniqueConstraint(fields=['prompt', 'version_number'], name='unique_prompt_version_number')`

### 3. `Label`
Environment / release tag pointing to a specific `Version` of a `Prompt`.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Unique internal label ID |
| `prompt` | ForeignKey | `Prompt`, on_delete=CASCADE, related_name='labels' | Associated Prompt reference |
| `version` | ForeignKey | `Version`, on_delete=CASCADE, related_name='labels' | Target Version reference |
| `name` | CharField(50) | Required (e.g., `production`, `draft`, `dev`) | Tag identifier |
| `created_at` | DateTimeField | auto_now_add=True | Timestamp of creation |
| `updated_at` | DateTimeField | auto_now=True | Timestamp of tag assignment update |

**Constraints**:
- `UniqueConstraint(fields=['prompt', 'name'], name='unique_label_per_prompt')`

### 4. `VariableDefinition`
Dynamic parameter placeholder specification for a `Version`.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Unique variable ID |
| `version` | ForeignKey | `Version`, on_delete=CASCADE, related_name='variables' | Associated Version reference |
| `name` | CharField(100) | Required | Variable key name (e.g. `user_name`) |
| `var_type` | CharField(20) | Choices: `string`, `integer`, `float`, `boolean`, `json` | Expected parameter data type |
| `required` | BooleanField | default=True | Whether value must be supplied during compile |
| `default_value` | TextField | Blank=True, Null=True | Fallback value if optional |
| `description` | TextField | Blank=True | Documentation for variable usage |

**Constraints**:
- `UniqueConstraint(fields=['version', 'name'], name='unique_variable_per_version')`

### 5. `Section`
Modular message segment within a `Version`.

| Field Name | Type | Constraints / Attributes | Description |
|---|---|---|---|
| `id` | BigAutoField | Primary Key | Unique section ID |
| `version` | ForeignKey | `Version`, on_delete=CASCADE, related_name='sections' | Associated Version reference |
| `role` | CharField(20) | Choices: `system`, `user`, `assistant`, `tool` | Message role/context type |
| `order` | PositiveIntegerField | default=0 | Sequential ordering index |
| `content` | TextField | Required | Template content block for section |

**Constraints**:
- `UniqueConstraint(fields=['version', 'order'], name='unique_section_order_per_version')`
