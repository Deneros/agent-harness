# Release, Deployment, And Production Conventions

> Applies to Docker, Dokploy, environment config, database migrations, releases,
> production changes, and rollback planning.

## Environments

| Environment | Purpose | Notes |
|---|---|---|
| Local/dev | Fast iteration | `./dev.sh`, Hibernate `ddl-auto=update` in dev profile |
| Dokploy dev | Shared remote dev validation | `docker-compose.dokploy-dev*.yml` |
| `prerelease` | Integration branch | Feature branches merge here before production promotion |
| Production | Real users/data | `ddl-auto=validate`; Flyway currently disabled in prod config |

## Production Database Rule

Production currently has:

```properties
spring.jpa.hibernate.ddl-auto=validate
spring.flyway.enabled=false
```

Implications:

- Hibernate will not create/update production tables.
- Flyway migrations in the repo do not automatically apply unless operations
  enables Flyway or runs SQL manually.
- Every schema change must include a migration file and a production application
  plan.
- Destructive migrations must use `IF EXISTS` / safe guards when environments may
  differ.
- Any production schema change must document manual SQL or Flyway enablement
  steps.

## Migration Convention

- Add migrations under `aes-back/src/main/resources/db/migration/`.
- Use the next free `V{N}__description.sql`.
- Keep migrations idempotent where reasonable (`IF EXISTS`, `IF NOT EXISTS`).
- Separate destructive cleanup from additive changes when rollback risk differs.
- Do not rely on local Hibernate update as proof that production is safe.
- For data migrations, include pre-counts, post-counts, and rollback notes.

## Pre-Deployment Gate

Before deploying:

- Superproject and submodules are clean.
- Feature branch is based on current `prerelease`.
- Backend targeted tests pass.
- Frontend `npm run build` passes.
- Critical Playwright/browser smoke paths pass.
- New permissions are seeded and tested.
- Migrations are reviewed and ordered.
- Environment variables/secrets are documented.
- Rollback plan exists.

## Rollout Procedure Template

Use this structure for any non-trivial deployment:

1. Executive summary: what changes, why, affected users, risk level.
2. Prerequisites: approvals, backups, secrets, image tags, migration readiness.
3. Preflight checks: current health, logs, DB connectivity, S3/MinIO, CORS.
4. Deployment steps: exact commands or Dokploy actions.
5. Verification: health endpoint, login, affected module smoke, logs, metrics.
6. Rollback: image rollback, schema rollback/manual compensation, feature flag off.
7. Post-deploy watch: first 15 minutes, first hour, next business day.

For high-risk changes, use the `devops-rollout-plan` skill before writing the
final rollout.

## Docker And Image Rules

- Production images must be built from committed code, not dirty worktrees.
- Image tags must identify branch/SHA or release version.
- Do not deploy `latest` without knowing the digest/SHA.
- Backend runtime image should not run as root.
- Frontend production build must set `VITE_API_URL` explicitly.

## Runtime Configuration

- Production secrets must not use development defaults.
- CORS must list explicit production origins.
- Integration toggles default off until their adapters are configured.
- Health endpoints must stay available for readiness/liveness checks.
- Logging level in production should be informative but not leak sensitive data.

## Rollback Rules

- Every deployment must have a rollback path before it starts.
- If schema changes are backward-compatible, prefer image rollback first.
- If schema changes are destructive, define manual restore/compensation steps.
- Never start a destructive deployment without a database backup or confirmed
  snapshot strategy.
- If rollback is not safe, call that out explicitly and require approval.

## Production Safety

- Do not deploy high-risk changes Friday afternoon unless critical.
- Do not combine unrelated features, schema changes, and infrastructure changes
  in one production rollout.
- Do not run manual SQL in production without recording the exact statement,
  timestamp, target DB, and verification result.
- Do not perform destructive browser actions in production through automation
  without explicit user approval.
