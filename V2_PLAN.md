# LLMBench Version 2 Plan

## Version 2 Goal

Version 2 will keep the useful evaluation features from Version 1 while making the platform secure, reliable, scalable, easier to maintain, and clearer to use.

## Current Progress

- [x] Remove exposed secrets and close HTML-injection paths.
- [x] Make real and mock evaluations impossible to confuse.
- [x] Add strict request, model, result, and judge validation.
- [x] Add queue-failure handling, bounded retries and timeouts, cancellation, progress reporting, and idempotent result storage.
- [x] Protect historical data and evaluation reproducibility.
- [x] Improve concurrency, pagination, and database performance.
- [x] Rebuild the dashboard states and accessibility.
- [x] Expand tests, CI checks, monitoring, and deployment safety.

Version 2's eight-step build order is complete. Future enhancements can extend
role-based identity, distributed rate limiting, full tracing, and persistent
live-model CI baselines without reopening the Version 1 reliability gaps.

## Planned Improvements

### 1. Security

- Remove hard-coded API keys from backend, frontend, Docker, scripts, and CI.
- Keep secrets only in environment variables or a secret manager.
- Add proper user or service authentication and permission levels.
- Restrict CORS to approved frontend addresses.
- Escape or safely render all user-, database-, and model-generated content.
- Add request limits and basic abuse protection.

### 2. Trustworthy Evaluations

- Never present mock output as a real evaluation result.
- Clearly separate demo mode from real model mode.
- Mark runs as failed when a required provider is unavailable.
- Validate supported models and require at least one selected model.
- Validate judge scores, types, ranges, and required fields.
- Record provider, model version, judge version, prompt version, and pricing version.

### 3. Reliable Background Jobs

- Publish jobs safely and record queue failures.
- Prevent runs from remaining stuck in `PENDING` or `RUNNING`.
- Add timeouts, retries, cancellation, and retry limits.
- Make jobs idempotent so retries do not create duplicate results.
- Add worker health and job progress reporting.

### 4. Performance and Scale

- Run model evaluations with controlled concurrency.
- Add provider-specific rate limits.
- Use efficient bulk database inserts.
- Avoid loading every evaluation result in list endpoints.
- Add proper pagination, filtering, and maximum page sizes.
- Move RCA and red-team generation into background jobs.

### 5. Data Integrity and Reproducibility

- Preserve historical datasets and prompts used by completed runs.
- Store immutable evaluation snapshots.
- Compare only compatible, completed runs.
- Add uniqueness rules for regression reports and versioned resources.
- Use Alembic as the single database migration system.
- Add missing indexes for common filters and relationships.

### 6. Accurate Cost and Quality Metrics

- Version the model pricing table and make it configurable.
- Use provider-reported token usage wherever available.
- Show when a value is estimated.
- Separate target-model cost from judge-model cost.
- Store failures and partial results without reporting false success.

### 7. API and Architecture

- Separate API, evaluation orchestration, provider adapters, judging, and reporting.
- Use typed provider interfaces instead of model-name prefix checks.
- Return structured error codes instead of hiding exceptions.
- Add structured logs, request IDs, metrics, and tracing.
- Create real readiness and liveness checks.

### 8. UI and UX

- Build a clearer Version 2 dashboard with consistent loading, empty, success, and error states.
- Show live job progress and allow cancellation.
- Make destructive actions safer.
- Add searchable and paginated datasets, prompts, runs, and results.
- Improve mobile layout, keyboard navigation, focus handling, labels, and chart alternatives.
- Remove mixed `EvalForge` naming and use `LLMBench` consistently.

### 9. Testing and Delivery

- Add database integration tests and worker tests.
- Add provider-adapter contract tests.
- Test queue failures, retries, timeouts, invalid model output, and partial runs.
- Add frontend security and end-to-end tests.
- Run the complete test suite in CI before report generation or deployment.
- Pin dependencies and add automated dependency/security checks.
- Deploy reports only from trusted main-branch workflows.

## Recommended Build Order

1. Remove exposed secrets and close HTML-injection paths.
2. Make real and mock evaluations impossible to confuse.
3. ~~Add strict request, model, and judge validation.~~ Completed.
4. ~~Fix job state handling, timeouts, retries, and idempotency.~~ Completed.
5. ~~Protect historical data and evaluation reproducibility.~~ Completed.
6. ~~Improve concurrency, pagination, and database performance.~~ Completed.
7. ~~Rebuild the dashboard states and accessibility.~~ Completed.
8. ~~Expand tests, CI checks, monitoring, and deployment safety.~~ Completed.

## Working Rule

Version 2 changes will be handled one problem at a time. Before each correction begins, the exact Version 1 drawback and the planned Version 2 change will be stated clearly.
