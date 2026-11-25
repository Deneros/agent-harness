---
name: desplegar
description: >
  Desplegar, redesplegar y verificar las aplicaciones de MRH y AuditGlow en Dokploy (VPS por
  Tailscale) con un script que usa su API: lista apps y entornos, lanza el despliegue de una app,
  espera a que termine con tiempo máximo, muestra el final del log y verifica la salud pública y el
  commit. Úsala cuando pidan "despliega", "desplegar", "sube a test", "súbelo a pruebas", "promueve
  a producción", "pasa a producción", "redeploy", "redespliega", "rebuild", "¿ya se desplegó?",
  "¿qué hay desplegado?", "¿está al día test?", "no se ve el cambio en app.auditglow.com" o "lista
  las apps de Dokploy". Producción siempre con confirmación explícita del usuario.
  No sirve para AES (VPS del cliente con Coolify) ni para cambiar configuración de Dokploy.
---

# Desplegar (Dokploy: MRH y AuditGlow)

Dokploy v0.31.4 en el VPS de Dokploy (`ssh auditglow-vps`), API solo por Tailscale en
`http://100.90.12.126:3000`. Token en `~/.dokploy-token` del Mac (600): el script lo lee, **nunca lo
imprimas, ni con `cat`, ni en un `curl` que se muestre**. No hagas llamadas `curl` a mano a la API
para desplegar: usa el script, que espera, enseña el log y verifica.

Accesos y contexto: `~/development/operaciones/docs/accesos/` (`mrh.md`, `auditglow.md`,
`dokploy-vps.md`). Reglas de entrega: `~/.claude/rules/nicol/delivery/dokploy.md` y `changelog.md`.

## El script

```bash
D=~/.agents/skills/desplegar/desplegar.py
python3 $D listar [--proyecto mrh]                    # apps por proyecto/entorno, rama, auto/manual, último despliegue
python3 $D estado mrh/test/front                      # ¿ya se desplegó? cabeza de la rama vs. lo desplegado + salud
python3 $D verificar auditglow/prod/back              # salud pública + commit, sin desplegar
python3 $D desplegar mrh/test/landing --dry-run       # qué haría (app, rama, commit, URLs de salud); no despliega
python3 $D desplegar mrh/test/back                    # lanza, espera (máx. 20 min), log final, salud y commit
python3 $D desplegar auditglow/prod/web --si-produccion   # SOLO tras el "sí" explícito del usuario en este chat
```

- App: `proyecto/entorno/nombre`. Entorno: `test`/`dev`/`staging`/`pruebas` = `development`;
  `prod`/`produccion` = `production`. También vale el `applicationId`. `listar` da los nombres.
- Opciones de `desplegar`: `--commit SHA` (esperado; por defecto la cabeza de la rama en GitHub
  vía `gh`), `--rebuild` (`application.redeploy`), `--timeout` (s, 1200), `--espera-salud` (s,
  180), `--lineas-log` (40), `--version-url URL` (si la app expone su commit).
- Salida: código `0` bien; `1` se intentó y falló (build, salud o commit; el log queda impreso);
  `2` rechazado sin cambiar nada (producción sin `--si-produccion`, despliegue ya en curso, app
  inexistente, sin token). Informa al usuario el veredicto final tal cual.
- Verificación: las URLs de salud salen de `~/development/operaciones/acris/app-health/config.json`
  (por host del dominio de Dokploy) o, si no hay, de la raíz del dominio. El commit lo comprueba con
  el que **Dokploy anota en el despliegue** (`Commit: <sha>`, también en despliegues por API desde
  0.31.4). Ninguna app expone hoy su versión/SHA por HTTP; cuando lo haga, añadir su URL a
  `config.json` (`version_urls`). Sin salud OK y commit OK no digas "desplegado".
- Tests (API simulada): `cd ~/.agents/skills/desplegar && python3 -B -m unittest discover -s tests`.

## Flujo por proyecto

### MRH (`~/development/mrh-scaffold`: `mrh-backend`, `mrh-front-web`, landing)

| Entorno | Apps Dokploy | Cómo llega |
|---|---|---|
| test (`development`) | `back`, `front`, `celery-worker-dev`, `celery-beat-dev`, `landing` | **push a `main`** → autodespliegue (webhook) |
| producción | `back`, `front`, `celery-worker`, `celery-beat` | **a mano** (autoDeploy apagado), tras verificar en test |

- "Sube a test" = commit + push a `main` del repo; luego `estado mrh/test/<app>` hasta ver `AL DÍA`
  (1–4 min). Si sigue `NO DESPLEGADO` pasados ~5 min, `desplegar mrh/test/<app>`.
- Un cambio de backend despliega también los workers: comprueba `back`, `celery-worker-dev` y
  `celery-beat-dev`.
- Producción: backend = `back` + `celery-worker` + `celery-beat` (mismo commit); orden si hay
  cambios incompatibles: el que diga el `CHANGELOG.md` (hoy: app móvil publicada → web → backend).

### AuditGlow (`~/development/auditglow-scaffold`: `auditglow-back`, `auditglow-web`, landing, Expo)

| Entorno | Apps Dokploy | Rama | Cómo llega |
|---|---|---|---|
| pruebas (`development`) | `back-staging`, `web-staging` | `staging` | `git push origin origin/prerelease:staging` y luego `desplegar auditglow/test/back-staging` y `.../web-staging` (no confíes en el webhook: `estado` lo confirma) |
| producción | `back`, `web`, `landing`, `download` | `main` | promoción `git push origin origin/prerelease:main` (**es un despliegue a producción**: confirmación antes) → autodespliegue |

- Trabajo en `feat/*`/`fix/*` desde `prerelease`; se integra en `prerelease` (no despliega nada).
- Tras promover, `estado auditglow/prod/back` **y** `estado auditglow/prod/web`: el caso repetido
  "no se desplegó nada en app.auditglow.com" se detecta aquí (`NO DESPLEGADO`). Si el webhook no
  saltó, `desplegar auditglow/prod/web --si-produccion` (ya confirmado al promover).
- **Esquema:** back de producción y staging corren con `SPRING_JPA_HIBERNATE_DDL_AUTO=validate` y
  Flyway apagado: toda migración `V*.sql` nueva se aplica a mano (tras un dump verificado) **antes**
  del backend, o no arranca. Compara migraciones contra `information_schema` en solo lectura.
- La app móvil (Expo) no pasa por Dokploy: `auditglow-scaffold/docs/release-movil.md`.

## Gates antes de desplegar (de `delivery/dokploy.md`)

Para test bastan los tres primeros; para producción, **todos**, y anótalos en el mensaje de
confirmación al usuario:

1. Tests del área tocada en verde (MRH: `docker exec django-mrh-dev python manage.py test ...`;
   AuditGlow: Gradle en contenedor) y build del front (`flutter build web` / `npm run build`).
2. Árbol limpio y commit empujado: lo que se despliega es lo que está en GitHub, nunca un worktree sucio.
3. `CHANGELOG.md` con su entrada en `[Sin publicar]` (y `Coordinado con` + orden si cruza repos).
4. Verificado en test: el flujo afectado recorrido por la UI y sin errores en el log de `back`.
5. Migraciones revisadas (`git diff <último desplegado>..main -- '*/migrations/*'` o `V*.sql`):
   aditivas, o con plan; AuditGlow: SQL aplicado antes del back.
6. Respaldo de la base de hoy presente (Acris, `backup-watch`) o un dump manual antes de migrar.
7. Rollback escrito: commit/etiqueta que se reemplaza (`estado` lo muestra). Volver atrás es
   redesplegar ese commit (la limpieza nocturna borra la imagen anterior).
8. Ventana: no viernes por la tarde; no durante respaldos (03:30–05:10 Bogotá) ni la limpieza (23:50 UTC).

## Producción: siempre pedir confirmación

Antes de cualquier despliegue a producción —incluido un push que dispara autodespliegue
(`main` de AuditGlow) y un `--rebuild`— **para y pregunta**, con: app(s), commit actual → commit
nuevo, migraciones, estado de los gates y rollback. Solo con un "sí" explícito del usuario en
este chat usa `--si-produccion`. "Despliega" a secas significa test. Una aprobación vale para ese
despliegue, no para los siguientes. Después: `verificar`, login y el flujo afectado, y avisa (si lo
piden) con la skill `hermes-relay` (`avisar "..."`).

## Qué no hacer

- No imprimir el token ni el `env` de las apps (secretos de Stripe, PayPal, base de datos...).
- No cambiar configuración de Dokploy (env, dominios, ramas, autoDeploy, Traefik) desde aquí.
- No `--rebuild` ni redeploy "para probar" en producción.
- No usarla con AES: su VPS es del cliente (Coolify), solo lectura sin permiso (`docs/accesos/aes.md`).
- No declarar "desplegado" con el script en `FALLO` o sin haber pasado `verificar`.
