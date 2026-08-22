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
