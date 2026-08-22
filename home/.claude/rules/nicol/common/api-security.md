# API And Security Conventions

> Applies to backend endpoints, frontend services, permissions, DTO contracts,
> public forms, uploads, and sensitive data.

## API Design

- Use resource-oriented routes under `/api/v1`.
- Use nouns for resources and HTTP verbs for actions.
- Use command-style subroutes only when the domain action is meaningful:
  `/hr/vacancies/{id}/transition`, `/scheduled-audits/{id}/auto-assign`.
- Keep endpoint paths centralized in frontend service files.
- Do not build API URLs directly inside React components.

## DTO Contract

- Never expose JPA/domain entities directly from controllers.
- Backend request/response DTO names must be mirrored by frontend types.
- Frontend payload property names must match backend DTO fields exactly.
- If a backend DTO expects `auditorId`, do not send `employeeId`.
- If the API shape changes, update backend DTO, controller/service, frontend
  type, frontend service, form payload, and tests in one PR.

## Validation And Errors

- Validate request bodies with `@Valid` and JSR-303 annotations.
- Validate uniqueness and business invariants in services.
- Use `ResourceNotFoundException` for missing entities.
- Do not leak `DataIntegrityViolationException` to users.
- Return user-friendly Spanish errors in the UI.
- Field-level backend validation should map to field-level frontend errors when
  possible.

## Authorization

the project is migrating to granular permissions with scopes.

- Read [../security/role-scope-matrix.md](../security/role-scope-matrix.md)
  before changing guards, seeders, policies, sidebars, or permission tests.
- Do not add new role-only `hasAnyRole` guards in migrated modules.
- Do not use `hasAuthority(...) or hasPermission(...)` for scoped resources.
- Per-id scoped endpoints must use `hasPermission(#id, 'ResourceType', 'ACTION')`.
- List endpoints for scoped resources must apply server-side scope filtering.
- Create/update endpoints must not trust owner ids from request bodies.
- New permissions must be seeded and tested.

## Frontend Permission UX

- Hide actions that the user does not have permission to perform.
- Disable actions blocked by business state and show the reason.
- Overrides, destructive actions, and compliance-critical transitions require
  explicit confirmation and a reason when the backend stores one.

## Sensitive Data And PII

- Do not log document numbers, emails, tokens, evaluation details, or uploaded
  file metadata unnecessarily.
- Do not put PII in URLs unless the route explicitly requires it.
- Do not store PII in `localStorage` or `sessionStorage`.
- Do not include sensitive data in toast messages.
- Use human-readable labels in pickers, but keep PII as secondary
  disambiguation only when necessary.

## Secrets And Configuration

- Secrets must come from environment variables or managed secret stores.
- Do not commit real secrets, tokens, API keys, or production credentials.
- Development defaults are acceptable only for local/dev profiles.
- Production must override JWT, database, S3, CORS, and integration secrets.
- Any new integration must default to disabled until configured.

## Uploads And Documents

- Enforce file size and type on backend.
- Show allowed types/size, progress, success, failure, and retry/replacement in
  the UI.
- Store files in S3/MinIO, not local server disk.
- Do not expose private document URLs publicly unless explicitly intended.
- Uploaded file names rendered in UI must be escaped.

## Public Endpoints

For public/client portal/OEA-facing endpoints:

- Derive ownership from the authenticated principal or signed token.
- Do not trust `clientId`, `userId`, or owner fields from the request body.
- Rate-limit or otherwise protect high-risk public submission endpoints.
- Validate CORS and allowed origins.
- Add tests for unauthenticated, wrong-owner, and happy-path access.
