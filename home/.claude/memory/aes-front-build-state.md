---
name: aes-front-build-state
description: "aes-front master tiene 641 errores de tipos preexistentes en 296 archivos, ocultos hasta 2026-08-22 tras un error de parseo."
metadata: 
  node_type: memory
  type: project
  originSessionId: 947f5f8b-8c69-44fc-a78d-a2d0e5227021
  modified: 2026-08-22T06:03:37.050Z
---

En `aes-front` (submódulo de `aes-scaffold`), `master` no compilaba: `DocumentsList.tsx` tenía el bloque `return` duplicado y un segundo `return` huérfano fuera de la función (TS1128 en la línea 429).

Como TS1128 es un error de **parseo**, `tsc` se detenía ahí y nunca type-checkeaba el resto. Al corregirlo (2026-08-22) afloraron **641 errores de tipos en 296 archivos**, todos preexistentes: 222 TS6133 (sin usar), 106 TS2339, 83 TS2322, 33 TS2698, 33 TS2345. El lint reporta aparte ~877 errores.

**Cómo atacarlos:** empezar por las causas raíz compartidas. `src/components/ui/badge.tsx` no declara las variantes `success` ni `warning` que usa medio código — arreglarlo mata 10 errores de golpe. Los 222 TS6133 son mecánicos y buena parte los cubre `eslint --fix`.

Ramas locales creadas, **sin push**:
- `fix/build-documentslist-duplicate-return` — el fix de sintaxis (commit `217258a3`)
- `chore/update-deps-security` — `npm audit fix` no rompedor, 27 → 8 vulnerabilidades (commit `0db85d87`). Majors pendientes: vitest→4.1.11, vite→8.2.2, react-router-dom→7.18.2.

`tsconfig.app.tsbuildinfo` está trackeado por error en el repo; es un artefacto de build y debería ir al `.gitignore`.

Las convenciones de `aes-scaffold/docs/` se generalizaron a `~/.claude/rules/nicol/`; siguen duplicadas en el proyecto y van a divergir. Ver [[agent-harness-repo]].
