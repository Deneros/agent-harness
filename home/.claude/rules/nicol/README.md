# Convenciones propias

Namespace personal, separado de `rules/ecc/`. ECC no lo gestiona ni lo pisa en
un reinstall.

| Archivo | Alcance |
|---|---|
| `common/api-security.md` | Diseño de API, DTOs, validación, autorización, PII, secretos, uploads |
| `common/testing.md` | TDD por defecto, pirámide de tests, diseño de cobertura antes de implementar, E2E reproducible por un usuario normal, verificación por tipo de cambio |
| `common/patterns.md` | Cuándo un patrón vale la pena y cuándo es sobreingeniería |
| `common/architecture.md` | Decisiones estructurales por umbral: monolito modular, hexagonal, microservicios |
| `react/engineering.md` | Estructura de módulos, server state, mutaciones, caché, UI optimista |
| `react/ux.md` | Controles, formularios, tablas, filtros, estados vacíos, toasts, i18n |
| `delivery/dokploy.md` | Entornos, migraciones, gates de despliegue, rollback |

Origen: `aes-scaffold/docs/`, generalizadas quitando el acoplamiento al dominio.
`engineering-workflow-conventions.md` se queda en aes-scaffold: describe su
layout de submódulos y worktrees, no es reutilizable.

## Precedencia

Estas convenciones son **más específicas** que las de ECC, así que ganan cuando
chocan — igual que ECC declara que lo específico vence a lo general.

Excepciones que nunca se relajan: el piso de verificación de
[../ecc/common/testing.md](../ecc/common/testing.md) y los controles de
[../ecc/common/security.md](../ecc/common/security.md).
