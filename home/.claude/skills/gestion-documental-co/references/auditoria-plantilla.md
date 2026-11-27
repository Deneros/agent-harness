# Auditoría de cumplimiento documental: plantilla

Copiar este archivo para cada auditoría. No reutilizar una matriz de otro aplicativo ni de otra fecha.

## Cabecera

| Campo | Valor |
|---|---|
| Aplicativo y versión / commit probado | |
| URL del entorno (aislado, no producción salvo aprobación) | |
| Perfil declarado | `publico` / `privado` (ver SKILL.md, "Cómo elegir perfil") |
| Alcance (sujeto obligado, función pública, fondos) | |
| Fecha de la prueba | |
| Fecha(s) sembrada(s) para simular el tiempo, si hubo | (ninguna / fecha y motivo) |
| Usuarios de prueba (rol, sin datos reales) | |
| Viewports probados | escritorio / móvil o estrecho |
| Auditor y revisor archivista o contador (si aplica) | |

## Matriz

| ID | perfil | resultado | evidencia (pasos UI + captura) | fundamento | hallazgo |
|---|---|---|---|---|---|
| PUB-01 | publico | | | | |

Una fila por flujo aplicable al perfil. Los flujos que no apliquen se listan igual con `NO APLICA`
y la razón en la columna de hallazgo.

## Instrucciones de llenado

**ID y perfil.** Usar el ID exacto del catálogo (PUB-, PRIV- o TRV-). El perfil es el que exige el flujo,
no el del aplicativo.

**resultado.** Exactamente uno de estos cinco valores:

- `CUMPLE`: el paso obligatorio se ejecuta por la UI y el resultado persistido es el exigido.
- `PARCIAL`: cumple una parte. En hallazgo, indicar qué falta.
- `FALTA`: no existe el camino en la UI, o el sistema permite lo que la norma prohíbe.
- `NO APLICA`: el perfil no lo exige o la condición no existe. En hallazgo, indicar cuál.
- `NO VERIFICABLE`: no se puede probar en navegador. En hallazgo, indicar qué falta (sistema externo,
  plazo real no sembrable, precondición sin camino en la UI).

**evidencia.** Pasos numerados, solo acciones que un usuario normal puede hacer en la interfaz, desde
una sesión limpia. Ejemplo: "1. Entrar como Contador. 2. Menú Documentos > Nuevo. 3. Subir factura.xml.
4. Verificar fecha de vencimiento en la ficha." Captura con datos personales redactados, con ruta
relativa al informe. Si se sembró una fecha, decirlo aquí.

**Prohibido en evidencia:** `psql`, `INSERT`, `UPDATE`, `curl` o cualquier llamada directa para crear
una precondición o ejecutar un paso. Si fue necesario, el resultado no puede ser CUMPLE: anotar
`FALTA` (si el camino de UI no existe) o `NO VERIFICABLE`.

**Lectura permitida:** consola, red o logs como ayuda de desarrollo, citados como tal.

**fundamento.** Norma y artículo, tomados del catálogo, con su marca de verificación
(VERIFICADO-PRIMARIA, VERIFICADO-SECUNDARIA o INCIERTO). Ejemplo: "Acuerdo 001/2024, art. 4.2.3 (VERIFICADO-PRIMARIA)".

**hallazgo.** Describir el comportamiento observado y el esperado. Etiquetar:

- `INCIERTO — recomendación` si el punto que falla está marcado INCIERTO en el catálogo. No es FALTA.
- `RECOMENDADO` si el punto es guía o "podrá". No es incumplimiento.
- Sin etiqueta: incumplimiento de un punto OBLIGATORIO.

**Negado.** Para cada flujo con actor negado, registrar en la evidencia la prueba con el rol que no debe
poder hacerlo: captura del rechazo y, si el flujo exige bitácora, el registro del intento.

**Registros de cierre.** Al final de la matriz, contar los resultados por perfil. Un cierre sin conteo
no es un informe.

## Cierre

- Lista de sujetos a validar con archivista o contador (puntos INCIERTO que bloquean una decisión).
- Lista de precondiciones que no se pudieron crear por la UI (son hallazgos de producto).
- Lista de fechas sembradas, con motivo.
- Riesgo residual: qué no se probó y por qué.
