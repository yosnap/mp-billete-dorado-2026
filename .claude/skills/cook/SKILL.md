---
name: mp:cook
description: >
  Ejecutor de planes para MainPaper. Invoca este skill con /mp:cook para implementar
  un plan o fase existente en `plans/`. Lee el archivo de fase, identifica el agente
  asignado, implementa el código, revisa la calidad y actualiza el estado en el .md.
  Usar cuando el usuario diga "cocina el plan", "ejecuta la fase", "implementa",
  "/mp:cook", "arranca la implementación", o pase una ruta a plan.md o phase-XX-*.md.
user-invocable: true
when_to_use: >
  Invocar cuando el usuario quiera ejecutar un plan o fase ya creado por /mp:plan.
  Requiere que exista al menos un archivo phase-XX-*.md en plans/.
category: implementation
keywords: [cook, implementar, ejecutar, plan, fase, agentes, mp:cook]
argument-hint: "<ruta a plan.md o phase-XX-*.md>"
metadata:
  author: mainpaper
  version: "1.0.0"
---

# mp:cook — Ejecutor de Planes MainPaper

Lee un plan o fase, delega la implementación al agente correcto y actualiza el estado.

## Flujo de Ejecución

```
1. Cargar fase  →  2. Validar prerequisitos  →  3. Implementar con agente asignado
→  4. Revisar calidad  →  5. Actualizar estado en .md
```

## Paso 1: Cargar el Objetivo

Si el usuario invocó `/mp:cook` sin argumento:
1. Buscar planes activos: `ls plans/`
2. Mostrar los planes disponibles y sus fases con estado `pending`
3. Preguntar al usuario qué fase ejecutar

Si invocó `/mp:cook <ruta>`:
- Si apunta a `plan.md` → preguntar qué fase ejecutar (mostrar tabla de fases con estado)
- Si apunta a `phase-XX-*.md` → cargar esa fase directamente

Leer el archivo de fase completo antes de continuar.

## Paso 2: Validar Prerequisitos

Antes de implementar, verificar:

1. **Dependencias satisfechas**: revisar campo `Dependencias` en la fase. Si depende de otra fase, verificar que su estado sea `completed` en el `plan.md`.
2. **Estado correcto**: la fase debe estar en `pending` o `in_progress`, nunca `completed`.
3. **Agente definido**: el campo `Agente` debe tener un valor válido.

Si alguna validación falla, reportar al usuario y detener.

## Paso 3: Implementar con el Agente Asignado

Cambiar el estado de la fase a `in_progress` en el archivo `.md`:
```
**Estado:** in_progress
```

Luego, según el agente asignado en la fase, delegar usando el Agent tool:

| Agente en fase | Tipo de agente a usar |
|----------------|----------------------|
| `backend-specialist` | `backend-specialist` |
| `frontend-development` | `fullstack-developer` |
| `tester` | `tester` |
| `code-reviewer` | `code-reviewer` |
| `docs-manager` | `docs-manager` |
| `researcher` | `researcher` |
| `devops` | `general-purpose` |
| `planner` o sin agente | `general-purpose` |

### Prompt al subagente

Incluir siempre en el prompt del subagente:

```
Tarea: <descripción de la fase>
Archivo de fase: <ruta/al/phase-XX.md>
Work context: <ruta raíz del proyecto>
Reports: <ruta>/plans/reports/

Lee el archivo de fase completo. Implementa todos los pasos listados en
"Pasos de Implementación". Al terminar, reporta:
- Archivos creados/modificados
- Tests ejecutados y resultado
- Cualquier bloqueo o decisión tomada

Status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
```

## Paso 4: Revisar Calidad

Después de que el subagente reporte `DONE` o `DONE_WITH_CONCERNS`:

1. Spawn del agente `code-reviewer` con contexto de la fase (archivos modificados, criterios de éxito)
2. Si el reviewer encuentra problemas bloqueantes → reportar al usuario con opciones concretas
3. Si el reviewer aprueba o los concerns son menores → continuar

## Paso 5: Actualizar Estado

Actualizar el archivo de fase `.md`:
```
**Estado:** completed
```

Actualizar la tabla de fases en `plan.md`, cambiando el estado de la fila correspondiente:
```
| XX | <nombre> | <agente> | completed | ... |
```

Reportar al usuario:

```
## Fase completada: phase-XX-<nombre>

**Agente:** <agente>
**Archivos modificados:** <lista>
**Tests:** <resultado>

**Próxima fase disponible:** phase-YY-<nombre> (si existe y dependencias OK)
Ejecuta: /mp:cook plans/<slug>/phase-YY-<nombre>.md
```

## Hard Gates

<HARD-GATE>
NO implementar código hasta haber leído el archivo de fase completo.
NO saltarse la verificación de dependencias.
NO marcar como completed sin haber pasado por code-reviewer.
</HARD-GATE>

## Manejo de Bloqueos

Si el subagente reporta `BLOCKED` o `NEEDS_CONTEXT`:
1. Leer el detalle del bloqueo
2. Intentar resolver con información disponible en el proyecto (leer archivos, buscar código)
3. Si no se puede resolver → reportar al usuario con:
   - Qué está bloqueado
   - Qué información o decisión se necesita
   - Qué fase o tarea desbloquearía el avance

## Seguridad y Scope

Este skill ejecuta únicamente las tareas definidas en los archivos de fase de `./plans/`.
NO modifica archivos fuera del scope definido en la fase.
NO hace commits ni push sin confirmación explícita del usuario.
