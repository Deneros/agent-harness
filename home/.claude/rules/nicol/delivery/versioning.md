# Versioning And Release Conventions

> Applies to version numbers, git tags, container images, release artifacts,
> upgrade notes, and support windows for any product delivered to a customer.
> Complements [dokploy.md](./dokploy.md) (deployment, migrations, rollback).

These rules say **what** a version must guarantee. The registry, the tag
location, the release trigger and the support window are the project's to
declare in `AGENTS.md` (`## Conventions`) or the README that stands in for it.
A project that ships to customers without that declaration has its first
finding.

## One Product Version

- A product made of several services ships **one version number** for all of
  them, released together (lockstep). The customer installs "Product 1.4.0",
  never "back 1.4 + front 1.2".
- Independent per-service versions are justified only when services are
  released and supported separately to customers. An internal contract between
  services is not a reason: it creates combinations nobody tests.
- The version is visible at runtime (UI footer, `/info` or equivalent health
  metadata), so support can ask "which version?" and get an exact answer.

## SemVer With Operational Meaning

`MAJOR.MINOR.PATCH`, where each part tells the operator what an upgrade costs:

| Part | Bump when | Operator impact |
|---|---|---|
| MAJOR | The install or upgrade contract breaks: a manual step, a destructive migration, a renamed/removed env var, a removed public endpoint | Read the upgrade guide; backup mandatory |
| MINOR | New features, or **any schema migration**, even additive | Backup, then upgrade; migrations run per the project's declared mechanism |
| PATCH | Fixes and security patches **without schema migrations** | Upgrade; rollback is an image swap |

- **A migration never ships in a PATCH.** That is what keeps "patch rollback =
  previous image" true.
- Pre-releases use `-rc.N` (`1.0.0-rc.1`) for pilots and validation; they are not
  deployed to a customer's production without that customer's approval.
- A product edition or feature tier is configuration, not a version: the same
  images serve every edition.

## Tags And Images

- The release tag `vX.Y.Z` lives where the full product is pinned (the
  superproject that fixes every service's SHA, or the monorepo).
- Every image carries the exact version tag **and** an immutable source tag
  (`sha-<commit>`).
- Customer deployments reference exact versions. Never `latest`, never a floating
  `X.Y` tag. Release notes record each image digest.
- Images are built by CI from the tagged commit, never from a developer machine
  or a dirty worktree.

## Release Artifact

A release is not "a tag exists". It is published only after CI, on the tagged
commit:

1. Builds and pushes every image.
2. Scans images and dependencies for vulnerabilities.
3. Runs the critical E2E journeys **against those published images**.
4. Publishes a release that contains: the deployment file pinned to the version,
   the configuration template, the changelog, the list of new migrations, upgrade
   notes, an SBOM, and checksums.

## Branching

- Releases are cut from the project's declared integration branch.
- A maintenance branch `release/X.Y` is opened from the tag **only** when a
  customer still runs that line and needs a patch. The fix lands on the
  integration branch too.

## Support Window And Deployment Record

- The project declares which lines receive fixes (e.g. current MINOR plus the
  previous one for security patches during N months).
- Every customer deployment is recorded: customer, version, edition, deployment
  form, last upgrade date, last successful restore test. Without that record a
  security patch cannot be targeted.

## Checklist

- [ ] One version for the whole product, visible at runtime.
- [ ] Bump matches the table; no migration inside a PATCH.
- [ ] Tag on the commit that pins every service.
- [ ] Images tagged with version and `sha-<commit>`; no `latest` in customer files.
- [ ] CI built, scanned and E2E-tested the published images before release.
- [ ] Release carries pinned deploy file, config template, changelog,
      migrations, upgrade notes, SBOM, checksums.
- [ ] Deployment record updated for every customer that receives it.
