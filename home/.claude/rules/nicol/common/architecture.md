# Arquitectura: elegir por umbral, no por aspiración

> Aplica [../../ecc/common/simplicity.md](../../ecc/common/simplicity.md) a las
> decisiones estructurales. La arquitectura es la decisión más cara de revertir,
> por eso la regla es empezar simple y escalar con evidencia.

## Por defecto: monolito modular con slices verticales

Un despliegue, una base de datos, módulos con fronteras explícitas. Organiza por
**feature**, no por capa técnica:

```
modules/invoicing/{api,domain,persistence}   ← todo lo de facturación junto
modules/hr/{api,domain,persistence}
```

En vez de `controllers/ services/ repositories/` con todo mezclado.

Por qué es el default: mueve la complejidad al lugar barato. Refactorizar un
módulo dentro de un monolito es una tarde; extraer un servicio es un trimestre.

**Regla de frontera**: los módulos se hablan por interfaces públicas o eventos,
nunca importando el `persistence` del vecino. Si respetas esto, extraer un
servicio después es mecánico. Si no, ninguna arquitectura te salva.

## Hexagonal / puertos y adaptadores

- **Vale la pena en fronteras reales**: pasarelas de pago, proveedores de email,
  almacenamiento, integraciones de terceros. Ahí el puerto te deja testear sin
  red y cambiar proveedor sin tocar el dominio.
- **No vale para tu propia base de datos**. Un puerto sobre tu Postgres, que no
  vas a cambiar, es indirección pura.
- Aplícalo **selectivamente**, no como estructura global del proyecto.

## Microservicios

Los criterios reales son organizativos, no técnicos:

- [ ] ¿Hay **equipos separados** que se bloquean entre sí al desplegar?
- [ ] ¿Un módulo necesita un **perfil de escalado genuinamente distinto**?
- [ ] ¿Hay un requisito de aislamiento de cumplimiento o datos?

Sin al menos uno de estos, un monolito modular gana en todo: menos latencia,
transacciones reales, un solo deploy, debugging con stack traces.

**Señales de que NO los necesitas**: un equipo, un dominio, tráfico que cabe en
una máquina, o "escalabilidad" como justificación sin un número detrás. Los
microservicios cambian complejidad de código por complejidad operativa
distribuida — y esa segunda no se refactoriza.

## Base de datos

- **Una base de datos compartida** hasta que duela de verdad.
- Transacciones sobre consistencia eventual mientras quepan en un proceso.
- Normaliza primero; desnormaliza con una consulta lenta medida en la mano.
- Migraciones siempre hacia adelante y compatibles — ver
  [../delivery/dokploy.md](../delivery/dokploy.md).

## Event sourcing

- **Vale la pena cuando**: la auditoría del *cambio* es un requisito del
  negocio (finanzas, cumplimiento, historial legal).
- **No vale cuando**: solo quieres un log de auditoría. Una tabla `audit_log`
  resuelve el 95% de los casos por el 5% del costo.

## Frontend

- Un solo SPA hasta que varios equipos se pisen en el mismo repo.
- Microfrontends solo con equipos independientes y ciclos de release distintos.
- El estado de servidor vive en la capa de queries, no en un store global — ver
  [../react/engineering.md](../react/engineering.md).

## Cómo decidir

1. Escribe el umbral concreto que dispararía el cambio ("cuando X pase de N").
2. Elige la opción más simple que quepa bajo ese umbral.
3. Deja el umbral escrito en un ADR o en el propio código.
4. Revísalo cuando el número se acerque, no antes.

Un umbral escrito convierte "algún día migramos" en una decisión con fecha. Sin
él, la migración pasa demasiado pronto (por moda) o demasiado tarde (por
inercia).

## Cuando ya te equivocaste

Sobreingeniería existente: no la reescribas por principio. Bórrala cuando
toques ese código por otra razón. Una capa inútil pero estable cuesta menos que
una migración que nadie pidió.
