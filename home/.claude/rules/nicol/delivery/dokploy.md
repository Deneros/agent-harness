# Release, Deployment, And Production Conventions

> Applies to Docker, Dokploy or an equivalent deployment platform, environment
> config, database migrations, releases, production changes, and rollback
> planning.

## Environments

| Environment role | Purpose | Notes |
|---|---|---|
| Local/dev | Fast iteration | Project declares its local run command and local schema strategy in `AGENTS.md` (`## Conventions`) or its README |
| Shared remote dev | Team-visible validation before integration | Project declares its compose file(s)/deploy target |
| Integration branch | Feature branches merge here before production promotion | Project declares the branch name |
| Production | Real users/data | Project declares its schema-application policy — see Production Database Rule below |

If the project does not declare these, that absence is itself a finding before
relying on any assumed default.

## Production Database Rule

The project declares, in `AGENTS.md` (`## Conventions`) or the README that
stands in for it, who applies schema changes in production: the ORM/framework
at boot, a migration tool, or a human running SQL by hand. If it does not
declare this, that gap is the first finding — do not assume any specific
tool's default (e.g. do not assume Hibernate `ddl-auto` or Flyway's own
default behavior without checking).

Whatever the declared mechanism, these hold regardless:

- Every schema change must include a migration file and a documented
  production application plan.
- Destructive migrations must use `IF EXISTS` / safe guards when environments
  may differ.
- Any production schema change must document the manual SQL or the
  enablement/trigger steps that make it take effect in production.
- Do not rely on a local ORM auto-update as proof that production is safe.

## Migration Convention

- Migrations live where the project declares in `AGENTS.md` (`## Conventions`)
  or its README; if it does not declare a path, that absence is the first
  finding.
- Number and order migrations per the project's declared convention (e.g. the
  next free `V{N}__description.sql`).
- Keep migrations idempotent where reasonable (`IF EXISTS`, `IF NOT EXISTS`).
- Separate destructive cleanup from additive changes when rollback risk differs.
- Do not rely on a local schema auto-sync (Hibernate `ddl-auto`, Django
  auto-migrate, or equivalent) as proof that production is safe.
- For data migrations, include pre-counts, post-counts, and rollback notes.

## Pre-Deployment Gate

Before deploying:

- Superproject and submodules are clean.
- Feature branch is based on the project's declared integration branch.
- Targeted tests pass for every service the change touched.
- The frontend production build passes, with the project's declared command.
- Critical smoke paths pass, through the project's E2E runner or as documented
  browser QA when it declares none.
- New permissions are seeded and tested.
- Migrations are reviewed and ordered.
- Environment variables/secrets are documented.
- Rollback plan exists.

## Rollout Procedure Template

Use this structure for any non-trivial deployment:

1. Executive summary: what changes, why, affected users, risk level.
2. Prerequisites: approvals, backups, secrets, image tags, migration readiness.
3. Preflight checks: current health, logs, DB connectivity, S3/MinIO, CORS.
4. Deployment steps: exact commands or actions in the project's deployment
   platform (Dokploy is one example).
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
