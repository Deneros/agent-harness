# Registro de cambios y tipos de entrega

> Aplica a todo repositorio que se despliega. Complementa
> [versioning.md](./versioning.md) (número de versión, tags, imágenes,
> artefacto de release, soporte) y [dokploy.md](./dokploy.md) (entornos,
> migraciones, rollback). Si algo choca, manda `versioning.md` en lo que es de
> versión y release; esta regla manda en el registro de cambios y en cómo se
> entrega cada tipo de cambio.

## Regla base

- Cada repositorio desplegable tiene un `CHANGELOG.md` en su raíz, formato
  [Keep a Changelog 1.1](https://keepachangelog.com/es-ES/1.1.0/).
- **Todo cambio con efecto para un usuario, operador o integrador añade su
  entrada en `## [Sin publicar]` en el mismo lote de commits**, nunca
  "después".
- No llevan entrada: `test`, `refactor`, `style`, `chore` y `docs` internos sin
  efecto observable.
- Se escribe para personas: qué cambia y para quién, no cómo se programó. El
  detalle técnico vive en el commit; la entrada lo referencia (`abc1234`).
- Idioma: el del producto. Términos de código entre backticks.

## Secciones (en este orden, solo las que tengan entradas)

| Sección | Qué va | Efecto en la versión (ver versioning.md) |
|---|---|---|
| `### Seguridad` | Vulnerabilidades y fugas de datos corregidas | PATCH si no hay migración |
| `### Incompatible` | Rompe el contrato de instalación o de API, o a clientes ya instalados | MAJOR (en 0.x, MINOR) |
| `### Añadido` | Funcionalidad nueva | MINOR |
| `### Cambiado` | Cambio de comportamiento existente | MINOR o PATCH según el caso |
| `### Corregido` | Errores | PATCH si no hay migración |
| `### Eliminado` | Funcionalidad retirada | MAJOR si es pública; si no, MINOR |
| `### Obsoleto` | Funcionalidad que se retirará | MINOR |

Toda entrada que lleve **migración de esquema** lo dice (`Migración aditiva` o
`Migración destructiva`), porque según versioning.md una migración nunca viaja
en un PATCH.

## Producto con varios repos

- Cada repo registra sus propios cambios en su `[Sin publicar]`.
- El **superproyecto** (donde se fija el SHA de cada servicio y vive el tag del
  producto) tiene su `CHANGELOG.md` de producto: en cada lote coordinado resume
  el cambio y enlaza los commits de cada repo.
- Un cambio que cruza repos lleva en cada uno la línea
  `Coordinado con: <repos>. Orden de despliegue: <A → B → C>.`
- Si rompe clientes ya instalados (apps móviles publicadas, integraciones), va
  en `### Incompatible` con la condición para desplegar (por ejemplo, "publicar
  la app antes que el backend en producción").

## Tipos de entrega

### Cambio normal
1. Test que falla → implementación → verde (ver
   [../common/testing.md](../common/testing.md)).
2. Entrada en `[Sin publicar]`.
3. Commit en la rama de trabajo que declara el proyecto.

### Cambio grande (varios repos, migración, contrato de API, pagos)
1. Plan en el directorio de planes que declara el proyecto, con su mapa de
   evidencia.
2. Entradas en cada repo con la línea `Coordinado con` y el orden de despliegue;
   resumen en el changelog del superproyecto.
3. Migraciones con su plan de aplicación en producción (ver dokploy.md).

### Hotfix (error en producción)
1. Se parte de la **etiqueta desplegada en producción**. Si la rama de trabajo
   no lleva cambios sin publicar, basta con ella; si los lleva, rama
   `release/X.Y` desde la etiqueta, como indica versioning.md.
2. Test que reproduce → corrección mínima → verde.
3. PATCH (sin migración), entrada movida a su versión, tag, despliegue con su
   verificación y rollback.
4. El arreglo se integra también en la rama de trabajo y `[Sin publicar]` queda
   coherente.

### Publicación
1. Cada repo publicado mueve `[Sin publicar]` a `## [X.Y.Z] - AAAA-MM-DD` y deja
   `[Sin publicar]` vacío arriba.
2. El changelog de producto del superproyecto recoge la versión y es el que va
   dentro del artefacto de release (versioning.md).
3. Tag `vX.Y.Z` donde lo declara versioning.md (el superproyecto o el monorepo).

## Lo que declara cada proyecto

En su `AGENTS.md` (`## Conventions`) o README:

| El proyecto declara | Ejemplo |
|---|---|
| Rama de trabajo y cómo llega cada rama a cada entorno | `main` → test automático; producción a mano |
| Dónde viven los planes de cambios grandes | `docs/plans/` |
| Cuál es el superproyecto que lleva el changelog de producto | `<producto>-scaffold` |

## Checklist antes de commitear un lote

- [ ] Entrada en `[Sin publicar]` por cada cambio con efecto observable.
- [ ] Migraciones señaladas en su entrada.
- [ ] Cambios entre repos con `Coordinado con` y orden de despliegue, y resumen
      en el superproyecto.
- [ ] Incompatibilidades marcadas con su condición.
- [ ] Tests y build de los repos tocados, reportados.
