# Code Review Standards

Escala la revision al riesgo: un cambio de una linea no necesita el pipeline
completo (ver `simplicity.md`).

## Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Security vulnerability or data loss risk | **BLOCK** - Must fix before merge |
| HIGH | Bug or significant quality issue | **WARN** - Should fix before merge |
| MEDIUM | Maintainability concern, including an unexplained source file over the soft 800-line ceiling | **INFO** - Consider fixing |
| LOW | Style or minor suggestion | **NOTE** - Optional |

Approve: no CRITICAL or HIGH. Warning: only HIGH. Block: any CRITICAL.

## Security Review Triggers

Review security (security-reviewer agent or equivalent) when touching:

- Authentication or authorization code
- User input handling
- Database queries
- File system operations
- External API calls
- Cryptographic operations
- Payment or financial code

## Common Issues to Catch

- Security: hardcoded credentials, SQL injection, XSS, path traversal, missing CSRF, authentication bypasses.
- Quality: functions over ~50 lines, files over 800 lines, nesting over 4 levels, swallowed errors.
- Performance: N+1 queries, missing pagination, unbounded queries.
- Over-engineering: run the pass in `simplicity.md`.
