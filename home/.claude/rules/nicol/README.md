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
| `delivery/dokploy.md` | Entornos, migraciones, gates de despliegue, rollback (Dokploy es un ejemplo de plataforma, no el supuesto) |
| `delivery/versioning.md` | Una versión por producto, SemVer con significado operativo, tags e imágenes, artefacto de release, ventana de soporte |

Origen: `aes-scaffold/docs/`. La generalización estuvo a medias hasta el
2026-09-08: quedaban comandos, rutas, componentes y entidades de ese repo dentro
de reglas que se presentaban como globales — un `cd aes-front` no le sirve a
nadie más, y una regla que nombra `EmployeePicker` no se puede cumplir donde no
existe. Desde esa fecha el acoplamiento está fuera y lo específico se declara por
proyecto (ver abajo).

`engineering-workflow-conventions.md` se queda en aes-scaffold: describe su
layout de submódulos y worktrees, no es reutilizable.

## Lo que declara cada proyecto

Estas reglas dicen **qué** hay que cumplir y con **qué evidencia**. El **cómo**
—el comando, la ruta, el componente— lo declara cada proyecto en su `AGENTS.md`
(sección `## Conventions`) o en el README que haga las veces.

Ese reparto es lo que las vuelve reutilizables: dos proyectos que comparten estas
reglas no comparten build, ni sistema de diseño, ni plataforma de despliegue.

| El proyecto declara | Lo consume |
|---|---|
| Comandos de test por capa y por servicio, con sus precondiciones | `common/testing.md` |
| Runner de E2E, o su ausencia declarada | `common/testing.md` |
| Dónde vive la matriz de flujos | `common/testing.md` |
| Ruta de migraciones y quién las aplica en producción | `delivery/dokploy.md` |
| Nombres de entornos y plataforma de despliegue | `delivery/dokploy.md` |
| Registro de imágenes, dónde vive el tag de release y qué lo dispara | `delivery/versioning.md` |
| Qué líneas reciben parches y dónde se registra cada instalación de cliente | `delivery/versioning.md` |
| Mapa categoría de valor → componente, y sistema de color | `react/ux.md` |
| Dónde vive su matriz de roles y permisos | `common/api-security.md` |
| Idioma por defecto del producto y si hay i18n | `react/ux.md` |

Un proyecto que no declara nada de esto **no queda exento**: la declaración que
falta es el primer hallazgo de cualquier revisión que toque esa área.

## Precedencia

Estas convenciones son **más específicas** que las de ECC, así que ganan cuando
chocan — igual que ECC declara que lo específico vence a lo general.

Excepciones que nunca se relajan: el piso de verificación de
[../ecc/common/testing.md](../ecc/common/testing.md) y los controles de
[../ecc/common/security.md](../ecc/common/security.md).
