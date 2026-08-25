# Testing And TDD Conventions

> Applies to backend, frontend, E2E, and browser validation.

## TDD Is The Default

For behavior changes, bug fixes, refactors, and new features:

1. Write the smallest failing test.
2. Run it and verify it fails for the expected reason.
3. Implement the minimal code.
4. Run it again and verify it passes.
5. Refactor while keeping tests green.

Do not write production logic first and add tests afterward unless the task is
explicitly a throwaway prototype or documentation-only.

## Test Pyramid

| Layer | Purpose | Tools |
|---|---|---|
| Unit | Business rules, mappers, pure functions, hooks | JUnit, Vitest |
| Contract/security | Permissions, DTO payloads, endpoint behavior | Spring tests, security tests |
| Integration | Cross-service workflows, repository behavior, migrations | Spring Boot tests |
| E2E | Critical user journeys only | Playwright |
| Browser QA | Visual/interactive verification, auth/profile-dependent flows | Chrome/Google MCP or Playwright headed |

## Design Coverage Before Implementation

Test coverage is designed during refinement, before production code exists. It
means appropriate evidence for every acceptance behavior, not a target such as
"100% of lines" or one E2E for every screen.

For each feature, record an **acceptance-evidence map** in the issue, PR, or
flow matrix. It must name:

| Item | Question it answers |
|---|---|
| Business outcome | What changes for the user or operation when this succeeds? |
| Actor and permission | Who may do it, and who must be denied? |
| Preconditions | What state or deterministic data must already exist? |
| Boundaries | Does it cross UI, API, authorization, stored data, a module, or a state transition? |
| Evidence | Which unit, contract, component, browser, or E2E test proves each assertion? |
| Final observable result | What persisted result must be visible to the next user, module, or step? |

Choose the lowest layer that can fail for the real reason:

| Behavior | Required evidence | E2E needed? |
|---|---|---|
| Pure calculation, state rule, mapper | Unit test | No |
| Request shape, validation, endpoint status, authorization | Backend contract/security test | No |
| Form-to-payload mapping, loading, empty, error, permission UI | Component test | No |
| UI correctly renders data from a real endpoint | Read-only E2E smoke | When the UI/API seam is material |
| One user goal across boundaries or modules | Isolated full-journey E2E | Yes |

### Full-Journey E2E Contract

An E2E journey is correct only against an approved business rule, state
machine, requirement, or product decision; the current UI behavior is not the
oracle. Each journey specification must define:

1. Actor and permission.
2. Every business precondition, created through the rendered UI by a normal
   user; only a stable test login and the documented clock exception may exist
   beforehand.
3. The complete user action through the browser, including the meaningful setup
   steps.
4. Expected visible result and intentional HTTP/API result at critical seams.
5. Persistent business outcome, verified through the real UI of the next step or
   actor.
6. Invariants and denied/invalid cases, covered at the lowest useful layer
   rather than duplicated as slow E2E branches.

Use one E2E per distinct business objective. Perform the whole business
precondition and action path through UI; API/DB fixtures belong only to contract
tests and developer smokes, never to a claimed user E2E. Keep mutations in the
isolated stack. Record each journey in the project's flow-coverage matrix.

### Existing E2E Is Discovery Input, Not Automatic Coverage

When auditing or modernizing a suite, an existing spec may reveal a business
journey that is not represented in the current flow matrix. Do not delete that
signal merely because the implementation is stale. First record its intended
objective, source file, provisional classification, and missing product rule in
an E2E candidate inventory.

Only an E2E that has an approved rule, deterministic precondition, nonoptional
assertion, persistent outcome, and current matrix row is active coverage.
Specs that skip their core action, accept absent data, depend on retired routes,
or are debugging aids must be marked candidate, diagnostic, or retired. Their
underlying business objective remains available for later product discovery.

### Development And Review Gate

Before implementation, select the tests in the acceptance-evidence map. During
implementation, write the smallest failing lower-layer test first. Before
review, the feature is incomplete unless its selected evidence passes and its
flow-matrix entry is current. A clean build, a request listener, an optional
assertion, or a manually refreshed empty list is not evidence that a feature
works.

## Backend Tests

Backend uses Java 21 and Gradle. The host may not have JDK 21, so prefer the
backend container or a JDK 21 Docker image.

Targeted examples:

```bash
# Inside the backend container
./gradlew test --tests com.aes.erp.hr.application.service.HrAssignabilityServiceTest

# From project root when dev compose is running
docker compose -f docker-compose.dev.yml exec backend ./gradlew test --tests '*HrAssignability*'
```

Rules:

- Add tests for every new service rule, permission policy, migration-sensitive
  repository, and API contract.
- For authorization changes, cover positive and negative paths.
- For schema changes, verify entity mapping and migration assumptions.
- Do not accept "compile only" as backend verification for behavior changes.

## Frontend Unit And Component Tests

Use Vitest and React Testing Library for:

- Query hooks with non-trivial loading/empty/error behavior.
- Forms with validation and payload mapping.
- Cache updates after create/update/delete.
- Components that hide/disable actions by permissions or business state.
- Complex filters, date handling, or optimistic UI rollback.

Commands:

```bash
cd aes-front
npm run test
npm run build
```

## E2E Tests

Use Playwright for critical workflows:

- Login and role-gated navigation.
- Create/update/transition flows that cross backend and frontend.
- Scheduling, assignability, recruitment conversion, audit execution, QASF/CRM
  workflows with business state transitions.

Rules:

- Prefer accessible locators (`getByRole`, labels, names).
- Do not rely on brittle CSS selectors.
- Do not test implementation details that unit tests should cover.
- Keep E2E focused; not every field needs an E2E test.
- Update or delete E2E tests when modules are intentionally removed.

Commands:

```bash
cd aes-front
npx playwright test e2e/<module>/
npx playwright test e2e/<module>/<file>.spec.ts --headed
npx playwright show-report
```

## Browser QA With Chrome/Google MCP

Use Chrome/Google MCP when a UI change needs real browser validation, especially:

- Logged-in flows that depend on the user's Chrome session.
- Visual alignment, responsive layout, modals, popovers, tables, FAB placement.
- Network/API verification from the actual app.
- File uploads or downloads.
- Reproducing user-reported UX issues.

Rules:

- Prefer Chrome MCP for interactive smoke validation after implementation.
- Use Playwright for repeatable automated E2E coverage.
- If Chrome MCP is unavailable, use Playwright headed mode and screenshots.
- Do not inspect cookies, passwords, local storage, or unrelated browser data.
- Do not perform destructive production actions through browser automation
  without explicit user approval.

### Browser/E2E Must Be UI-Replicable By A Normal User (mandatory)

Any flow verified with Chrome MCP or claimed as an end-to-end pass **must be
fully reproducible by an ordinary user operating only the rendered UI** — a user
who cannot seed the database and cannot call the API directly.

- **No DB seeding** (`psql`, SQL `INSERT`/`UPDATE`, fixtures) to create the state
  under test.
- **No direct API calls** (`curl`, HTTP clients) to set up preconditions or to
  perform any *step* of the flow (creating the request, advancing a stage, etc.).
- If the scenario needs data that does not exist, **create it through the UI** as
  part of the test (e.g., create the client, run the job from the admin console,
  submit the form). The setup is part of the journey.
- If a required step **cannot** be done through the UI, that is a **product gap /
  finding** — report it as a defect (missing screen, broken form, permission gap,
  missing empty-state CTA). Do **not** paper over it with SQL or API calls and
  then call the test "passing".
- Read-only inspection (`psql SELECT`, reading a log line, `curl GET`) is allowed
  as a *developer aid* to confirm what you observed in the UI, but the test's
  pass/fail and its reproduction steps must never depend on a write a normal user
  could not perform.
- **Exception — simulating the passage of time / external clock.** The one thing
  no user can do is fast-forward the clock. Seeding *only* a date/timestamp to
  simulate elapsed time — e.g., setting an already-issued certificate's expiration
  near so a "renewal due" state is reachable today — **is acceptable, provided it
  is documented in the test report.** This is the *only* legitimate seed, and it
  must be the minimum (the date, nothing else). It is categorically different from,
  and must never be conflated with, seeding that skips steps a user can perform in
  the UI (creating records, advancing stages, submitting forms) — that stays
  forbidden. Rule of thumb: **seed the clock, never the steps.**

**Why:** a test that passes only because rows were hand-seeded or a `POST` was
sent via `curl` proves nothing about the real user experience. It hides exactly
the defects browser QA exists to catch: missing UI surfaces, broken/over-strict
forms, permission gaps, and empty-state bugs. (Concretely: a renewal E2E that
fabricates an entire issued certificate via SQL and files the request via a
direct `POST` verifies the backend, not the product — the user still can't do
it. The correct version produces the certificate by running the lifecycle
through the UI across its real actors, and seeds *only* the expiration date to
simulate the three years that would otherwise have to pass.)

**How to apply:** start from a clean login and reach the target state only through
clickable UI. Write the report so the reproduction steps are pure UI actions a
normal user could follow. If you had to seed/curl to make it work, the flow is
**not** verified end-to-end — say so explicitly and log the missing UI path.

Minimum browser QA for frontend PRs:

- Desktop viewport.
- Mobile or narrow viewport for forms/tables affected by the change.
- One successful create/update path when the page mutates data.
- One error/empty/loading path when feasible.

## Required Verification By Change Type

| Change | Minimum verification |
|---|---|
| Backend business rule | Targeted JUnit test, compile/test for touched area |
| Permission change | Security/contract tests for allowed and denied paths |
| Frontend form | Vitest/component test for payload + browser smoke |
| React Query mutation | Test or inspect cache update/invalidation |
| New table/list page | Browser smoke + loading/empty state review |
| Critical workflow | Playwright E2E or documented browser MCP smoke |
| Schema change | Migration review + backend mapping test |

## Reporting Test Results

Final responses and PRs must say:

- What was run.
- What passed.
- What failed or could not run.
- Why anything could not run.
- Residual risk.
