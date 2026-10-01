# Frontend Engineering Conventions

> Applies to React code, frontend services, query hooks, mutations, cache
> updates, frontend DTOs, tabs, and data connectivity.

This document is separate from [ux.md](./ux.md).
UX defines what the user experiences; this document defines how frontend code
keeps that experience connected, fresh, testable, and maintainable.

## Required Guidance

Before implementing or reviewing non-trivial frontend work, apply the relevant
specialist guidance:

- `vercel-react-best-practices` for React state, rendering, data fetching, and
  performance.
- `test-driven-development` for behavior changes, payload mapping, hooks, and
  mutation/cache behavior.
- `interface-design` for internal app screens.
- `frontend-design` for public or landing experiences.
- `api-design-principles` when the frontend consumes or shapes an endpoint.
- `security-best-practices` when the UI touches permissions, PII, uploads,
  public endpoints, or auth-sensitive flows.

Do not treat a clean TypeScript build as UX or behavior verification.

## Module Structure

Use the module's existing pattern first. For new frontend module surfaces, keep
the shape predictable:

```text
src/modules/<module>/
├── components/
├── hooks/
├── pages/
├── services/
├── types/
└── routes.tsx
```

Expected responsibilities:

- `services/`: endpoint URLs, Axios calls, request/response mapping.
- `hooks/`: React Query hooks and reusable frontend behavior.
- `types/`: frontend DTOs that mirror backend request/response shapes.
- `pages/`: route-level orchestration, not low-level form/table details.
- `components/`: presentational and feature-specific UI pieces.

Do not call Axios directly from route components when a service/hook can own the
contract.

## Server State Ownership

React Query owns server state.

- Use query hooks for list/detail data.
- Query keys must include every filter that changes the result.
- Do not duplicate query data into ad-hoc local arrays just to mutate the UI.
- Derive view data with `useMemo` only when the transformation is meaningful.
- Prefer `keepPreviousData` or an equivalent pattern for filter/page changes
  where blanking the table would feel broken.
- Avoid `useEffect` + `useState` + Axios for new server-backed screens.

Local React state is for UI state: open dialogs, active tabs, selected rows,
temporary form values, and client-only filters.

## Loading, Empty, Error, And Previous Data

Every query-backed surface must explicitly handle:

- Initial loading.
- Empty result.
- Error.
- Refetching while previous data is visible, when applicable.

Visual loading patterns live in [ux.md](./ux.md).
Engineering owns making those states reachable and deterministic.

## Mutations And Cache Updates

After create/update/delete/status mutations:

- Update the relevant visible query with `queryClient.setQueryData` when the
  affected object is already known and the update is simple.
- Invalidate related list/detail queries when other derived data may change.
- Close dialogs only after success unless the flow is explicitly optimistic.
- Show one success toast and one clear error path.
- Never use `window.location.reload()` to refresh application state.
- Do not add a visible "Actualizar" button to compensate for stale cache.

For creates, the created record should appear without a manual refresh. If the
backend returns the created object, insert it into the cached list or invalidate
the list immediately after success.

## Optimistic UI

Optimistic UI is allowed when the action is reversible and the failure recovery
is clear.

Good candidates:

- Marking a low-risk item as viewed.
- Reordering local list items where rollback is easy.
- Updating a non-critical text field after the backend validates the same
  payload.

Use caution or avoid optimistic UI for:

- Permission overrides.
- Compliance-critical audit/HR state transitions.
- Destructive actions.
- File uploads.
- Actions that create legal, certificate, payroll, or evaluation records.

When optimistic UI is used:

1. Cancel in-flight queries for the affected key.
2. Snapshot previous cache state.
3. Apply the optimistic update.
4. Roll back on error.
5. Invalidate on settle.
6. Show a clear error toast when rollback happens.

For create actions with server-generated ids, prefer cache insert on success.
If true optimistic create is required, use a temporary id, visible pending
state, replacement after success, and rollback on failure.

## Data Connectivity Contract

A frontend route, tab, drawer, or modal is not complete until it is connected to
real data or explicitly marked as pending product work.

For every data-backed surface:

- Define frontend types matching backend DTO names and fields.
- Create or reuse a service method.
- Create or reuse a query/mutation hook.
- Render loading, empty, error, and success states.
- Update cache or invalidate after mutations.
- Remove hidden production mock data.
- Verify the surface in a browser.

If the backend endpoint does not exist yet, the UI must say so through a
controlled disabled/empty state. Do not silently ship local mock arrays in
production routes.

## Tab Connectivity

Every tab in a profile/detail page must be evaluated independently.

A tab is considered done only when:

- It fetches the correct data for the selected entity.
- It has loading, empty, and error states.
- Its create/update/delete actions hit real endpoints when visible.
- Its mutations update visible state without page refresh.
- Its disabled state explains what prerequisite is missing.

Do not leave a tab visually present if it is disconnected and not intentionally
marked as pending.

## Frontend DTO And API Contract

Frontend DTOs must mirror backend contracts exactly.

- If the backend expects `ownerId`, the frontend sends `ownerId`.
- If the backend exposes `evaluationType`, do not invent `type`.
- If a field is optional in the backend, model it as optional or nullable
  intentionally in TypeScript.
- If a backend contract changes, update types, services, forms, hooks, tests,
  and consuming UI in the same PR.

Endpoint strings belong in service files, not scattered across components.

## Date Payloads

Display format and payload format are different concerns.

- Date-only backend fields (`LocalDate`) use `YYYY-MM-DD`.
- Date-time backend fields (`LocalDateTime`, `Instant`) use ISO date-time
  strings with explicit timezone semantics.
- Do not send a date-only value with `toISOString()` unless the date part is
  intentionally extracted afterward; timezone shifts can change the day.
- Forms should store date objects or date-only strings consistently, not a mix
  of localized display text and payload values.
- Date labels and display formatting remain Spanish/Colombian as defined in
  [ux.md](./ux.md).

## Filters And URL State

For list pages:

- Include filters in query keys.
- Persist filters in the URL when they define a shareable operational view.
- Keep purely temporary form filter state local until the user applies it.
- Clear filters without clearing unrelated form work.
- Debounce free-text search.

## Permissions In The Frontend

Frontend permission checks improve UX; backend authorization remains the source
of truth.

- Hide actions the user cannot perform.
- Disable actions blocked by business state and show the reason.
- Do not trust hidden buttons as security.
- Do not store broad permission snapshots in unsafe browser storage.
- Keep permission names aligned with backend seeders and guards.

## React Quality Rules

- Keep route components thin; move reusable logic into hooks/components.
- Avoid prop drilling through many layers when a local context or hook is
  clearer.
- Do not memoize everything by default; memoize when there is a measured or
  obvious rendering cost.
- Keep dependency arrays honest. Do not silence hook lint warnings by removing
  real dependencies.
- Prefer stable component boundaries over large route files with many nested
  inline components.
- Clean up timers, subscriptions, and external listeners.

## Frontend Engineering Checklist

Before requesting review on frontend code changes:

- [ ] Server data is owned by query hooks, not ad-hoc local arrays.
- [ ] Query keys include filters, pagination, and entity ids that affect data.
- [ ] Mutations update cache and/or invalidate related queries.
- [ ] Created records appear without manual refresh.
- [ ] Optimistic UI has rollback/error recovery when used.
- [ ] No hidden mock data remains in production routes.
- [ ] Each touched tab/panel has loading, empty, error, and connected data
      states.
- [ ] Frontend DTOs match backend request/response fields exactly.
- [ ] Date-only payloads are `YYYY-MM-DD`.
- [ ] Endpoint URLs are centralized in service files.
- [ ] Permission-dependent actions are hidden/disabled consistently.
- [ ] Browser verification covered at least one successful mutation path when
      the page mutates data.
