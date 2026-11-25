# Instrucciones globales del harness

ECC esta recortado a lo de uso diario (`prune-ecc.sh` del repo agent-harness). Las
convenciones propias estan en `rules/nicol/` y mandan sobre `rules/ecc/`, salvo
el piso de seguridad y verificacion (`rules/ecc/common/security.md` y `testing.md`).

## Antes de cada commit

- Sin secretos en el codigo (claves, tokens, contrasenas): variables de entorno.
- Entradas validadas en la frontera, consultas parametrizadas, salida escapada.
- Autenticacion y autorizacion verificadas; los errores no filtran datos sensibles.
- Ante un hallazgo de seguridad: parar, corregir lo critico, rotar lo expuesto.

## Estilo

- Preferir crear objetos nuevos a mutar los existentes, salvo donde el idioma o el
  ORM (Django, JPA, Dart) haga natural mutar.
- Archivos cohesivos, funciones pequenas, sin anidacion profunda; errores siempre
  manejados de forma explicita.

## Biblioteca de ECC

Lo que no se usa a diario esta en `~/.claude/skills-library/`, `agents-library/` y
`commands-library/`; Claude Code no lo carga. Para reactivar algo, moverlo y abrir
una sesion nueva: `mv ~/.claude/skills-library/<nombre> ~/.claude/skills/`
(agentes y comandos igual, con `.md`). Para que no vuelva a recortarse, anadir el
nombre a `ecc-daily/*.txt` del repo y ejecutar `./prune-ecc.sh`.
