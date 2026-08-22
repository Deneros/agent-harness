# Patrones: cuándo valen la pena

> Complementa [../../ecc/common/patterns.md](../../ecc/common/patterns.md), que
> prescribe patrones sin contrapartida, y aplica la escalera de
> [../../ecc/common/simplicity.md](../../ecc/common/simplicity.md).

Un patrón es una compra: pagas indirección a cambio de algo. Si no sabes qué
compras, no lo compres. La regla por defecto es **código directo**; el patrón
entra cuando el dolor ya existe, no cuando se imagina.

## Envelope de respuesta de API

```
{ "data": <payload|null>, "error": { "code": string, "message": string } | null,
  "meta": { "page", "size", "total" }?  }
```

- **Vale la pena cuando**: varios clientes consumen la API, o el front necesita
  distinguir "vacío" de "falló" de forma uniforme, o hay paginación en más de
  dos endpoints.
- **No vale cuando**: un solo cliente que tú controlas y los códigos HTTP ya
  dicen todo. Envolver un `204 No Content` en `{data:null,error:null}` no añade
  información, añade unwrapping en cada llamada.
- **Costo**: cada consumidor desenvuelve. Si el envelope no se aplica en el
  100% de los endpoints, es peor que no tenerlo: el front necesita dos rutas.
- **Regla**: o todos los endpoints, o ninguno. Un envelope parcial es deuda.

## Repository

- **Vale la pena cuando**: hay más de una fuente de datos real para la misma
  entidad, o necesitas testear lógica de negocio sin base de datos.
- **No vale cuando**: envuelve un solo `JpaRepository` y sus métodos son
  `findAll` → `findAll`. Eso no es una abstracción, es un reenvío. Spring Data
  **ya es** el repositorio.
- **Costo**: una interfaz, una implementación y un mock por entidad.

## Capa de servicio

- **Vale la pena cuando**: la operación toca varias entidades, tiene una
  transacción, o la regla se invoca desde más de un punto de entrada.
- **No vale cuando**: el servicio solo llama al repositorio y devuelve. Un CRUD
  puro puede vivir en el controlador sin vergüenza.

## DTO + mapper

- **Vale la pena siempre en la frontera HTTP**: nunca expongas entidades JPA.
  Esto no es negociable — ver [api-security.md](./api-security.md).
- **No vale cuando**: mapeas DTO→DTO entre capas internas. Eso es ceremonia.

## Result / Either en vez de excepciones

- **Vale la pena cuando**: el fallo es esperado y el llamante debe decidir
  (validación, parseo, reglas de negocio).
- **No vale cuando**: el fallo es excepcional y nadie lo maneja localmente. En
  Java, propagar una excepción hasta un `@ControllerAdvice` es más simple y más
  idiomático que un `Result` que todos hacen `.orElseThrow()`.

## Strategy

- **Vale la pena cuando**: existen **tres o más** variantes reales, hoy, y se
  eligen en runtime.
- **No vale cuando**: hay dos y una es "por si acaso". Un `if` es más legible
  que una interfaz con dos implementaciones y un registro.

## Factory

- **Vale la pena cuando**: la construcción es genuinamente compleja o depende de
  datos de runtime.
- **No vale cuando**: envuelve un `new`. Un constructor con nombre claro gana.

## Cache-aside

- **Vale la pena cuando**: tienes una medición que muestra el cuello de botella
  y los datos toleran estar rancios.
- **No vale cuando**: no has perfilado. Una caché sin invalidación pensada es
  un generador de bugs con buen hit rate.
- **Costo**: invalidación. Siempre es la invalidación.

## Eventos de dominio

- **Vale la pena cuando**: un efecto secundario es opcional, puede fallar
  independientemente y no debe bloquear la transacción principal.
- **No vale cuando**: reemplazas una llamada directa por un evento "para
  desacoplar". Acabas de convertir un stack trace en una búsqueda de logs.

## CQRS

- **Vale la pena cuando**: las lecturas y escrituras tienen formas o cargas
  radicalmente distintas y ya duele.
- **No vale cuando**: es un CRUD. Separar el modelo duplica el trabajo para
  siempre.

## Feature flags

- **Vale la pena cuando**: despliegas continuo y necesitas separar deploy de
  release, o haces rollout gradual.
- **No vale cuando**: la rama vive días, no meses. Un flag sin fecha de retiro
  es un `if` permanente. Todo flag nace con dueño y fecha de borrado.

## Antes de introducir cualquier patrón

- [ ] ¿El dolor existe hoy, o lo estoy imaginando?
- [ ] ¿Cuántas variantes reales hay? (menos de tres → probablemente un `if`)
- [ ] ¿Qué me cuesta esto en cada cambio futuro?
- [ ] ¿El framework ya lo resuelve?
- [ ] ¿Puedo introducirlo después sin reescribir? Si sí, hazlo después.
