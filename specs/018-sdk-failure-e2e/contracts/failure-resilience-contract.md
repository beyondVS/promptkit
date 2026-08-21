# Failure Resilience Contract

## Public outcome matrix

| Scenario | Boundary reached | Required public outcome | Prohibited outcome |
|---|---:|---|---|
| Empty or whitespace API key | No HTTP request | `InvalidConfigurationError` | Authentication or communication error |
| Reserved non-listening loopback endpoint | Real socket connection attempt | `CommunicationError` | Retry, fallback prompt, authentication error |
| Local Prompt Server rejects non-empty key | Real HTTP request and 401 response | `AuthenticationError` | Credential disclosure, prompt response, invalid-response error |
| Required variable omitted | Retrieved prompt, local compilation | `MissingVariableError` | Partial compiled content or downstream call |
| Undeclared variable supplied | Retrieved prompt, local compilation | `UnexpectedVariableError` | Ignored input, partial output, or downstream call |
| Incompatible variable type supplied | Retrieved prompt, local compilation | `InvalidVariableTypeError` | Coercion, partial output, or downstream call |

## Real-HTTP setup contract

1. The test suite owns a loopback HTTP Prompt Server and its transactional test database.
2. The health endpoint must return the established ready response before SDK assertions run.
3. A test-owned prompt must be published and on-live before the successful SDK retrieval.
4. The accepted and rejected API keys are non-production sentinels.
5. Server setup failure fails the fixture/setup phase and is never asserted as `CommunicationError`.

## Exception safety contract

Every scoped exception must:

- inherit from the public `PromptKitError` hierarchy;
- remain distinguishable by class without parsing message text;
- provide a safe stage or affected-field explanation;
- exclude API keys, authorization-header values, supplied variable values, full template content, and compiled content;
- preserve the no-retry and no-fallback contract.

Exact message wording is not a compatibility guarantee.

## Logging ownership contract

- Communication, authentication, credential-configuration, and compilation-validation failures emit zero records from the PromptKit SDK.
- The SDK does not install handlers or mutate logger/root handler, level, propagation, or disabled state during these scenarios.
- Records from the live Django server are not SDK records and must be filtered separately.
- The calling application may log only the safe public exception type and message through its own logger, handler, level, and destination.
- Existing adapter warning behavior outside these failure scenarios is unchanged.

## Atomicity and downstream contract

- Compilation validates the complete input before returning any `CompiledPrompt`.
- A failed compilation produces no aggregate or role-section result.
- Provider conversion or invocation remains outside the SDK failure flow and the downstream spy count stays at zero.
- Repeating the matrix three times creates no logger handlers, SDK records, cached protected value, or cross-run result reuse.
