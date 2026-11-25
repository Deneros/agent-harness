# Trabajo con agentes: cómo colaborar con Nicolás

> Sale de revisar cinco meses de sesiones (jul–nov 2026): ~1.900 mensajes, de los
> cuales ~300 fueron solo "sí, sigue con la fase N". Estas reglas quitan esa
> fricción sin perder control sobre lo que de verdad importa.

## Autonomía: plan aprobado = plan ejecutado

- Si Nicolás aprobó un plan con fases, **ejecuta todas las fases seguidas** y
  reporta al final. No pidas permiso fase por fase.
- **Detente y pregunta solo** ante:
  - cambios en **producción** (despliegues, migraciones, configuración, DNS);
  - **servidores de clientes** (p. ej. el VPS de AES): solo lectura sin permiso
    explícito, y nunca nuevas vías de acceso;
  - **borrados irreversibles** de datos, respaldos o archivos personales;
  - algo que **cueste dinero** (servicios de pago, planes, almacenamiento externo);
  - **decisiones de producto** o algo que se envíe a terceros (correos, mensajes,
    publicaciones, invitaciones).
- Al terminar una tarea, propone lo siguiente con una recomendación concreta; no
  una lista de opciones sin criterio.

## Delegar

- Tareas con varias partes independientes → **subagentes en paralelo** con un
  brief autocontenido (rutas, reglas, qué no tocar, quién hace commit).
- La sesión principal **diseña, fija contratos, revisa, commitea y resume**. No
  delegues búsquedas de un par de comandos.
- Evita que dos agentes editen lo mismo: asigna dueño de `CHANGELOG.md` y del
  plan; si el checkout está sucio por otro agente, trabaja en un **worktree**.
- Revisa lo que entrega un agente (tests, capturas, diff de seguridad) antes de
  desplegar. Su resumen no es evidencia.

## Contexto y accesos

- Antes de preguntar "¿cómo entro a X?" o "¿cuál es el endpoint?", busca en
  `operaciones/docs/accesos/`, en los runbooks y en la memoria.
- **Nunca pidas secretos por chat.** Si Nicolás pega uno (token, contraseña),
  úsalo solo para lo pedido y recomienda **rotarlo** al terminar.
- Para pedirle algo a Hermes usa el relay (skill `hermes-relay`), no SSH ad hoc.

## Comunicación

- Español, directo, sin jerga innecesaria. Primero el resultado, luego el detalle.
- Informes para clientes o personas no técnicas: punto, qué se hizo, estado.
  **Sin** commits, tarifas, nombres de archivos ni detalles internos.
- Cuando algo no se verificó, dilo explícitamente. No declares "desplegado" sin
  comprobar salud y versión en el entorno real.

## Costos de la sesión

- Nicolás vigila el uso (`/usage`). Prefiere scripts y tareas programadas sin IA
  para lo repetitivo; la IA para diseño, revisión y lo que no se puede
  automatizar de forma determinista.
