---
name: gestion-documental-co
description: Usar para diseñar, revisar o auditar un sistema de gestión documental en Colombia: AGN/Acuerdo 001 de 2024 (entidades públicas), empresas privadas (retención, ISO 9001 7.5) y Leyes 1581, 1712, 1755 y 527. Incluye auditar en navegador si un aplicativo cumple sus flujos PUB-, PRIV- y TRV-.
---

# Gestión documental Colombia

Skill de referencia normativa y de auditoría. No es asesoría legal: todo requisito sale de los
catálogos en `references/`, cada uno con norma, artículo y marca de verificación. Ante la duda,
validar con un archivista (sector público) o con contador/abogado (sector privado).

## Cuándo usarla

- Diseñar un módulo de documentos, retención, radicación, expedientes o disposición final.
- Revisar un PR o una pantalla que toque reglas documentales.
- Auditar un aplicativo ya construido, en navegador, contra los flujos normativos.

## Modelo: núcleo común + perfil

Un solo producto con **núcleo siempre activo** y **un perfil por instalación**. No hay bifurcación de código.

**Núcleo (todos los perfiles):** documento con metadatos y tipo documental; versiones; permisos por
rol y confidencialidad; bitácora inalterable; integridad (hash); expediente; búsqueda; y un **motor
de retención**.

**Regla de retención** (unidad del motor; es genérica, no de un producto concreto):

```
tipo / serie  →  plazo  +  evento disparador  +  base legal (con versión)  +  acción de disposición
```

- El disparador es configurable: creación, cierre del expediente, último asiento, 1 de enero siguiente,
  firmeza, retiro del trabajador, evento manual, etc. Ver el catálogo de disparadores en `references/privado.md` §1.4.
- Mientras el disparador no ocurra, el vencimiento es **indeterminado**. Nunca se calcula desde la
  creación por defecto.
- La regla guarda su **origen** (`TRD convalidada` o `plantilla legal`), no un booleano global.

**Perfil `publico`** (AGN, Acuerdo 001 de 2024): CCD/TRD/TVD con estado de convalidación e inscripción
RUSD; radicación con consecutivo anual; expediente electrónico con índice firmado al cierre; FUID;
transferencias primaria y secundaria; eliminación con inventario publicado 60 días hábiles y acta del
comité; préstamo; Ley 1712 y términos de Ley 1755.

**Perfil `privado`**: reglas de retención precargadas por tipo (10 años, C.Co./Ley 962 art. 28;
5 años o firmeza, ET art. 632; 20 años SG-SST, Decreto 1072 art. 2.2.4.6.13 — este último con fuente
secundaria); control documental tipo ISO 9001 §7.5 (borrador → revisión → aprobación → vigente →
obsoleto; el autor no aprueba lo suyo); bloqueos de privacidad. PGD, FUID, transferencias regladas,
foliación y radicación ciudadana quedan apagados.

**Transversal (ambos):** Ley 1581 (consultas 10 días hábiles; reclamos 15), Ley 527 (conservación del
art. 12; integridad del art. 9), firma electrónica (Decreto 2364).

Nexdoc es un ejemplo de implementación de este modelo, no su definición (ver su `decision-perfiles.md`).

## Cómo elegir perfil

1. ¿La entidad es pública, o particular que cumple funciones públicas (Ley 594 art. 2; Acuerdo 001/2024
   art. 1.1.2 "sujetos obligados")? → **`publico`**.
2. ¿Es empresa privada sin funciones públicas? → **`privado`**.
3. ¿Es privada pero presta servicio público o recibe fondos públicos? → **caso a caso**. Ley 1712 art. 5
   literales c) a f) la alcanza solo en la información de esa función o servicio. Marcar **INCIERTO**
   (privado.md §5 punto 11; transversal.md §3 punto 14) y no imponer el perfil público a toda la instalación sin decisión explícita.
4. Un cliente privado con funciones públicas usa `publico` en toda la instalación; el perfil por tipo documental no está construido.

## Índice de flujos

Obligatoriedad: **OBLIGATORIO** = verbo imperativo de la norma; **RECOMENDADO** = guía o "podrá";
**INCIERTO** = no confirmado en texto; no es requisito duro (ver Reglas). El detalle de cada flujo
(actor, negado, precondiciones, pasos, registros, plazos, fundamento, detección en UI) está en el
archivo indicado.

### Público — `references/publico-agn.md` (33 flujos; PUB-14 no se usa)

| ID | Nombre | Perfil | Obligatoriedad |
|---|---|---|---|
| **A. Planeación e instrumentos** | | | |
| PUB-01 | Política y Programa de Gestión Documental (PGD) | publico | OBLIGATORIO |
| PUB-02 | PINAR y planes del SIC | publico | OBLIGATORIO formular; plazo INCIERTO |
| PUB-03 | Comité (CIGD) y actas de decisión | publico | OBLIGATORIO |
| **B. Instrumentos de valoración** | | | |
| PUB-04 | Cuadro de Clasificación Documental (CCD) | publico | OBLIGATORIO |
| PUB-05 | TRD: elaboración y aprobación | publico | OBLIGATORIO |
| PUB-06 | TRD/TVD: evaluación y convalidación | publico | OBLIGATORIO |
| PUB-07 | Inscripción RUSD y publicación | publico | OBLIGATORIO |
| PUB-08 | Actualización de la TRD | publico | OBLIGATORIO |
| PUB-09 | TVD y fondos acumulados | publico | OBLIGATORIO si hay fondos acumulados |
| **C. Comunicaciones oficiales** | | | |
| PUB-10 | Radicación de recibidas (ventanilla única) | publico | OBLIGATORIO |
| PUB-11 | Radicación de enviadas | publico | OBLIGATORIO |
| PUB-12 | Comunicaciones internas oficiales | publico | OBLIGATORIO (numeración anual INCIERTO) |
| PUB-13 | Anulación de radicados y numeración de actos | publico | OBLIGATORIO |
| **D. Organización de expedientes** | | | |
| PUB-15 | Conformación del expediente y unidades documentales | publico | OBLIGATORIO |
| PUB-16 | Ordenación, foliación y hoja de control | publico | OBLIGATORIO |
| PUB-17 | Cierre y cómputo del tiempo de retención | publico | OBLIGATORIO (historias laborales: RECOMENDADO) |
| **E. Expediente electrónico e híbrido** | | | |
| PUB-18 | Expediente electrónico: índice y metadatos | publico | OBLIGATORIO (elementos mínimos); S6 RECOMENDADO |
| PUB-19 | Cierre del expediente electrónico y firma del índice | publico | OBLIGATORIO |
| PUB-20 | Expediente híbrido | publico | OBLIGATORIO |
| **F. Inventario, transferencias, disposición** | | | |
| PUB-21 | Inventario documental (FUID) y entrega de cargos | publico | OBLIGATORIO |
| PUB-22 | Transferencia primaria | publico | OBLIGATORIO |
| PUB-23 | Transferencia secundaria | publico | OBLIGATORIO |
| PUB-24 | Disposición final: conservación total y selección | publico | OBLIGATORIO |
| PUB-25 | Eliminación con acta, publicación previa y aprobación | publico | OBLIGATORIO |
| PUB-26 | Reproducción por otros medios técnicos | publico | OBLIGATORIO que no sustituya la eliminación |
| **G. Consulta, préstamo y acceso** | | | |
| PUB-27 | Consulta y préstamo | publico | OBLIGATORIO acceso y reserva; préstamo INCIERTO |
| **H. Conservación** | | | |
| PUB-28 | Sistema Integrado de Conservación (SIC) | publico | OBLIGATORIO |
| **I. Requisitos del sistema y retención** | | | |
| PUB-29 | Requisitos funcionales mínimos del sistema | publico | OBLIGATORIO (decreto); S6 RECOMENDADO |
| PUB-30 | Metadatos mínimos y descripción | publico | OBLIGATORIO |
| PUB-31 | Tiempos de retención y su cómputo en el sistema | publico | OBLIGATORIO |
| **J. Otros controles** | | | |
| PUB-32 | Pérdida y reconstrucción de expedientes | publico | OBLIGATORIO |
| PUB-33 | Control interno y seguimiento | publico | OBLIGATORIO |
| PUB-34 | Particulares con funciones públicas y reglas especiales | publico | OBLIGATORIO (aplicación detallada INCIERTO) |

### Privado — `references/privado.md` (16 flujos)

| ID | Nombre | Perfil | Obligatoriedad |
|---|---|---|---|
| **Retención y soportes** | | | |
| PRIV-01 | Libros y soportes contables: 10 años desde el último asiento | privado | OBLIGATORIO |
| PRIV-02 | Soportes tributarios (facturas incluidas) | privado | OBLIGATORIO; plazo exacto INCIERTO |
| PRIV-03 | Reproducción por medio técnico y destrucción de originales | privado | OBLIGATORIO si se destruyen originales; Cámara INCIERTO |
| PRIV-04 | Conservación con integridad de mensajes de datos | privado | OBLIGATORIO si el mensaje es soporte de conservación |
| PRIV-11 | Tabla de retención por tipo y disposición con revisión | privado | Mínimo OBLIGATORIO; "tabla" formal = PRÁCTICA |
| **Laborales y SST** | | | |
| PRIV-05 | Expediente SG-SST y registros de 20 años | privado | OBLIGATORIO (fuente secundaria) |
| PRIV-06 | No conservar historia clínica ocupacional en la hoja de vida | privado | INCIERTO |
| **Control de documentos** | | | |
| PRIV-07 | Control de documentos del sistema (ISO 9001 §7.5) | privado | ESTÁNDAR VOLUNTARIO |
| PRIV-08 | Registros distinguidos de documentos (inmutables) | privado | ESTÁNDAR VOLUNTARIO |
| **Societario, contractual, cumplimiento** | | | |
| PRIV-09 | Libros de actas y decisiones societarias | privado | OBLIGATORIO (existencia); plazo INCIERTO |
| PRIV-10 | Soportes SAGRILAFT | privado | OBLIGATORIO solo sociedades obligadas; vigencia INCIERTO |
| PRIV-13 | Firma y aprobación de contratos con evidencia | privado | Firma: OBLIGATORIO para valor probatorio; matriz = PRÁCTICA |
| **Privacidad y acceso** | | | |
| PRIV-12 | Supresión de datos frente al deber de conservar | privado | OBLIGATORIO (mecánica en TRV-05/06) |
| PRIV-14 | Auditoría y trazabilidad de acceso y cambios | privado | ESTÁNDAR VOLUNTARIO / PRÁCTICA |
| PRIV-15 | Permisos por rol y segregación de funciones | privado | ESTÁNDAR VOLUNTARIO; Ley 1581 para datos personales |
| **Integraciones** | | | |
| PRIV-16 | Integración con correo y ERP | privado | PRÁCTICA DE MERCADO |

### Transversal — `references/transversal.md` (23 flujos)

| ID | Nombre | Perfil | Obligatoriedad |
|---|---|---|---|
| **2.1 Datos personales (Ley 1581, Decreto 1377/1074)** | | | |
| TRV-01 | Autorización previa e informada | ambos | OBLIGATORIO |
| TRV-02 | Tratamiento de datos sensibles | ambos | OBLIGATORIO |
| TRV-03 | Deber de informar y aviso de privacidad | ambos | OBLIGATORIO |
| TRV-04 | Consulta del titular (10 días hábiles) | ambos | OBLIGATORIO |
| TRV-05 | Reclamo: corrección, actualización, supresión (15 días hábiles) | ambos | OBLIGATORIO |
| TRV-06 | Revocatoria de autorización y supresión | ambos | OBLIGATORIO (alcance de la excepción INCIERTO) |
| TRV-07 | Rectificación, actualización y acceso gratuito | ambos | OBLIGATORIO |
| TRV-08 | Registro Nacional de Bases de Datos (RNBD) | ambos | OBLIGATORIO si aplica; criterio INCIERTO |
| TRV-09 | Transferencia internacional de datos | ambos | OBLIGATORIO |
| TRV-10 | Transmisión a encargados | ambos | OBLIGATORIO (forma del contrato INCIERTO) |
| TRV-11 | Manual interno de políticas y procedimientos | ambos | OBLIGATORIO |
| **2.2 Transparencia (Ley 1712, Decreto 103/1081)** | | | |
| TRV-12 | Registro de activos de información | publico (privado solo en su función pública) | OBLIGATORIO para sujetos obligados |
| TRV-13 | Esquema de publicación | publico (privado solo en su función pública) | OBLIGATORIO para sujetos obligados |
| TRV-14 | Programa de gestión documental (Ley 1712) | publico (privado solo en su función pública) | OBLIGATORIO para sujetos obligados |
| TRV-15 | Índice de información clasificada y reservada | publico (privado solo en su función pública) | OBLIGATORIO para sujetos obligados |
| TRV-16 | Plazo de reserva (15 años, prorrogable) | publico (privado solo en su función pública) | OBLIGATORIO; detalle Decreto 103 INCIERTO |
| TRV-17 | Respuesta a solicitud de acceso a información | publico (privado solo en su función pública) | OBLIGATORIO; plazo Ley 1712 INCIERTO |
| **2.3 Derecho de petición (Ley 1755)** | | | |
| TRV-18 | Radicación con constancia | ambos | OBLIGATORIO |
| TRV-19 | Plazos de respuesta (15 / 10 / 30 días) | ambos | OBLIGATORIO; hábiles o calendario INCIERTO |
| TRV-20 | Peticiones incompletas y desistimiento | ambos | OBLIGATORIO |
| **2.4 Mensajes de datos y firma (Ley 527, Decreto 2364)** | | | |
| TRV-21 | Conservación de documentos y mensajes de datos | ambos | OBLIGATORIO cuando una norma exige conservar |
| TRV-22 | Integridad y original | ambos | OBLIGATORIO cuando una norma exige el original |
| TRV-23 | Firma electrónica | ambos | OBLIGATORIO cuando una norma exige firma |

## Procedimiento de auditoría

Usar cuando se pide verificar si un aplicativo cumple. Ejecutar por **perfil**: cada flujo se evalúa
solo contra el perfil que lo exige.

**(a) Mapear.** Para cada flujo aplicable, anotar las pantallas y endpoints que deberían cubrir sus
pasos, leyendo el código en modo lectura si hace falta. Si no existe pantalla para un paso obligatorio,
ya es hallazgo de **FALTA**, aunque la API exista.

**(b) Recorrer en navegador, solo por la interfaz.** Usar la skill `agent-browser` (o `browser-qa` para
la pasada visual y de accesibilidad). Reglas duras:

- Entrar con un usuario normal, con sesión limpia, y solo con clics y formularios.
- Crear cada precondición por la UI: el cliente, el expediente, la TRD, el radicado. Ningún `psql`, `INSERT`
  ni `curl` para preparar o ejecutar un paso.
- **Única excepción:** sembrar la **fecha** para simular el paso del tiempo (p. ej. que un expediente ya
  venció). Documentar en el informe qué fecha se sembró y por qué. Solo la fecha; nada más.
- Si un paso requerido no puede hacerse por la UI, es un **hallazgo de producto (FALTA)**. No se rellena
  con SQL o API y no se declara "pasa".
- Lectura de consola, red o logs como ayuda de desarrollo está permitida, pero la prueba y sus pasos
  no pueden depender de una escritura que el usuario normal no puede hacer.
- No inspeccionar cookies, contraseñas, `localStorage` ni datos ajenos del navegador.
- Sin acciones destructivas en producción sin aprobación explícita. Usar un stack aislado.
- Viewport de escritorio, y móvil o estrecho para formularios y tablas tocados. Un camino de éxito, uno de error o vacío.

**(c) Probar el caso negado.** Para cada flujo que tenga un actor que **no** debe poder hacerlo (columna
"Negado" del archivo), iniciar sesión con ese rol y confirmar en la UI que la acción no aparece, está
deshabilitada o devuelve un rechazo. Si el flujo exige bitácora, confirmar que el intento queda registrado.

**(d) Registrar evidencia.** Por cada fila: pasos UI exactos (reproducibles por un usuario normal),
captura de pantalla con datos personales redactados, fecha de la prueba, perfil, versión o commit probado,
y la fecha sembrada si hubo alguna.

## Formato de salida

Matriz con una fila por flujo aplicable (plantilla: `references/auditoria-plantilla.md`):

| ID | perfil | resultado | evidencia (pasos UI + captura) | fundamento | hallazgo |
|---|---|---|---|---|---|

Resultados permitidos, solo estos cinco:

- **CUMPLE**: el paso obligatorio se ejecuta por la UI y el resultado persistido es el exigido.
- **PARCIAL**: cumple una parte. Indicar cuál falta.
- **FALTA**: no existe el camino en la UI, o el sistema permite lo que la norma prohíbe (p. ej. borrar un radicado).
- **NO APLICA**: el perfil no lo exige, o la condición no existe (p. ej. no hay fondos acumulados).
- **NO VERIFICABLE**: no se puede probar en navegador (requiere sistema externo, depende de un plazo real
  que no se puede sembrar, o la precondición no se puede crear por la UI). Anotar qué falta para verificarlo.

## Reglas

- **INCIERTO no es requisito duro.** Un incumplimiento que solo toca un punto INCIERTO no produce FALTA:
  se registra como PARCIAL o CUMPLE con observación, y el hallazgo lleva la etiqueta `INCIERTO — recomendación`.
- **RECOMENDADO** tampoco es obligatorio: se reporta como recomendación, no como incumplimiento.
- **Citar siempre norma y artículo** del archivo de referencia, con su marca VERIFICADO-PRIMARIA,
  VERIFICADO-SECUNDARIA o INCIERTO. No citar de memoria. Si una norma está en el catálogo como derogada
  (p. ej. Acuerdos 060/2001, 042/2002, 004/2019 del AGN), un software que la cite está citando normas derogadas.
- **No es asesoría legal.** Los hallazgos son de conformidad con los catálogos, y conviene validarlos
  con un archivista (público) o con contador/abogado (privado) antes de tomar una decisión.
- **Perfil y alcance primero.** Antes de auditar, declarar el perfil y el alcance (sujeto obligado o no).
  Sin perfil declarado no hay auditoría, solo lista de chequeo.
- **Fechas de vigencia.** Las normas se verificaron hasta fechas distintas (AGN a 2024-09-30; Senado con
  nota de 2026-11-15). Cambios posteriores no descartados: revisar el Diario Oficial o SUIN antes de cerrar.
- **Sin pasar la prueba por la herramienta.** Un flujo que pasa solo porque un script sembró datos o llamó
  a la API es NO VERIFICABLE, no CUMPLE.

## Referencias

- `references/publico-agn.md`: Acuerdo 001 de 2024 del AGN (PUB-xx), tabla de normas y lista de incertidumbres.
- `references/privado.md`: empresa privada (PRIV-xx), plazos por disparador, comparación con procesos AGN.
- `references/transversal.md`: Leyes 1581, 1712, 1755 y 527 con decretos reglamentarios (TRV-xx).
- `references/auditoria-plantilla.md`: matriz vacía con instrucciones de llenado.
- Insumos de origen: `/home/acris/projects/nexdoc-scaffold/docs/normativa/`. Navegador: `agent-browser`; visual y accesibilidad: `browser-qa`.
