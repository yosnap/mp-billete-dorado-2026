---
name: mp:plan
description: >
  Planificador de proyectos inteligente para MainPaper. Invoca este skill con /mp:plan para
  crear automáticamente una planificación detallada de tareas en el directorio del proyecto actual.
  Hace scout del codebase, detecta el tech stack y la estructura, luego genera una carpeta
  `plans/<timestamp>-<nombre>/` con un `plan.md` maestro y archivos de fase individuales
  (phase-01-*.md, phase-02-*.md...). Cada fase incluye contexto, requisitos, arquitectura,
  pasos de implementación, checklist y criterios de éxito, con el agente Claude asignado
  (frontend-development, backend-specialist, tester, code-reviewer, docs-manager).
  Usar cuando el usuario diga "planifica", "crea un plan", "quiero planificar", "/mp:plan",
  "necesito un plan de implementación", "organiza las tareas", o cualquier variante de
  solicitar una planificación de trabajo en el proyecto.
user-invocable: true
when_to_use: >
  Invocar cuando el usuario quiera crear una planificación detallada de tareas para un
  proyecto o feature. Especialmente útil al comenzar una feature nueva, sprint, o tarea
  compleja que requiere múltiples agentes y fases de trabajo.
category: planning
keywords: [planning, plan, fases, tareas, agentes, proyecto, sprint, roadmap, mp:plan]
argument-hint: "[descripción del objetivo o feature a planificar]"
license: MIT
metadata:
  author: mainpaper
  version: "1.0.0"
---

# mp:plan — Planificador de Proyectos MainPaper

Crea una planificación detallada con fases y tareas, asignando agentes específicos por dominio,
basándose en el análisis automático del proyecto actual.

## Flujo de Ejecución

```
1. Scout del codebase  →  2. Análisis del objetivo  →  3. Diseño de fases
→  4. Asignación de agentes  →  5. Generación de archivos
```

## Paso 1: Scout Automático del Codebase

Al invocar `/mp:plan`, SIEMPRE ejecutar primero el scout del proyecto:

```bash
# Detectar tech stack
find . -maxdepth 2 -name "package.json" -o -name "pyproject.toml" -o -name "go.mod" \
       -o -name "Cargo.toml" -o -name "pom.xml" | head -5

# Ver estructura de directorios
find . -maxdepth 3 -type d \
  -not -path "*/node_modules/*" \
  -not -path "*/.git/*" \
  -not -path "*/.next/*" \
  -not -path "*/dist/*" \
  -not -path "*/__pycache__/*"

# Revisar documentación existente
ls docs/ 2>/dev/null && ls plans/ 2>/dev/null
```

Leer también:
- `CLAUDE.md` o `.claude/CLAUDE.md` si existe
- `README.md` si existe
- `docs/system-architecture.md` si existe
- `docs/development-roadmap.md` si existe

## Paso 2: Capturar el Objetivo

Si el usuario invocó `/mp:plan` sin argumentos, preguntar:

> "¿Qué quieres planificar? Describe brevemente el objetivo o feature."

Si invocó `/mp:plan <descripción>`, usar esa descripción directamente.

## Paso 3: Diseñar las Fases

Dividir el trabajo en fases coherentes según el objetivo. Guía de fases comunes:

| Tipo de trabajo | Fases típicas |
|----------------|---------------|
| Feature fullstack | Setup → Backend API → Frontend UI → Tests → Documentación |
| Feature backend | Modelos/DB → Servicios → API endpoints → Tests |
| Feature frontend | Componentes → Integración API → Estilos → Tests |
| Bug fix complejo | Diagnóstico → Fix → Tests → Review |
| Migración/Refactor | Análisis → Migración → Validación → Limpieza |
| Setup inicial | Infraestructura → Config → Base → CI/CD |

**Reglas de diseño de fases:**
- Cada fase = un conjunto coherente de cambios que puede completarse independientemente
- Máximo 7 fases por plan (si hay más, agrupar)
- Las fases deben seguir el orden de dependencias (no implementar antes de diseñar)
- Cada fase debe tener UN agente principal responsable

## Paso 4: Asignar Agentes

Asignar el agente correcto a cada fase según el dominio:

| Dominio | Agente asignado |
|---------|----------------|
| React, TypeScript, componentes UI | `frontend-development` |
| API REST/GraphQL, DB, autenticación, lógica de negocio | `backend-specialist` |
| Tests unitarios, integración, e2e | `tester` |
| Revisión de calidad, standards, seguridad | `code-reviewer` |
| Documentación técnica, README, ADR | `docs-manager` |
| Deployment, Docker, CI/CD | `devops` (via `/ck:devops`) |
| Investigación tecnológica | `researcher` |
| Planning complejo multi-agente | `planner` |

## Paso 5: Generar la Estructura de Archivos

### Nombre de carpeta del plan

Formato: `plans/YYMMDD-HHMM-<slug-del-objetivo>/`

Ejemplo: `plans/260610-1430-autenticacion-oauth/`

Para obtener timestamp actual:
```bash
date +"%y%m%d-%H%M"
```

### Estructura a crear

```
plans/
└── <timestamp>-<slug>/
    ├── plan.md                         # Archivo maestro (máx 80 líneas)
    ├── phase-01-<nombre>.md
    ├── phase-02-<nombre>.md
    ├── phase-03-<nombre>.md
    └── reports/                        # Para reportes de agentes
```

## Formato de plan.md (Maestro)

```markdown
# Plan: <Título del Objetivo>

**Fecha:** YYYY-MM-DD
**Objetivo:** <descripción del objetivo en 1-2 oraciones>
**Tech stack detectado:** <lista del tech stack del proyecto>

## Fases

| # | Fase | Agente | Estado | Dependencias |
|---|------|--------|--------|--------------|
| 01 | <nombre> | <agente> | pending | — |
| 02 | <nombre> | <agente> | pending | phase-01 |
| 03 | <nombre> | <agente> | pending | phase-02 |

## Contexto del Proyecto

<2-3 oraciones sobre la estructura y stack detectado del proyecto>

## Referencias

- [Phase 01](<./phase-01-nombre.md>)
- [Phase 02](<./phase-02-nombre.md>)
- [Phase 03](<./phase-03-nombre.md>)
```

## Formato de phase-XX.md (Cada Fase)

Ver referencia completa en `references/phase-template.md`.

Estructura obligatoria:

```markdown
# Phase-XX: <Nombre de la Fase>

## Overview
- **Prioridad:** High / Medium / Low
- **Estado:** pending
- **Agente:** <nombre-del-agente>
- **Dependencias:** phase-XX (o "Ninguna")
- **Estimación:** <N horas / días>

## Descripción
<1-2 oraciones explicando qué se hace en esta fase>

## Contexto
<Links a archivos relevantes del proyecto, docs, fases anteriores>

## Requisitos
### Funcionales
- [ ] <requisito 1>
- [ ] <requisito 2>

### No Funcionales
- [ ] <rendimiento, seguridad, etc.>

## Arquitectura
<Descripción de componentes, patrones, decisiones técnicas clave>

## Archivos Relacionados
### Modificar
- `<ruta/archivo.ts>` — <razón>

### Crear
- `<ruta/nuevo-archivo.ts>` — <propósito>

## Pasos de Implementación
1. <paso específico y accionable>
2. <paso específico y accionable>
3. ...

## Todo List
- [ ] <tarea concreta>
- [ ] <tarea concreta>

## Criterios de Éxito
- [ ] <criterio verificable>
- [ ] <criterio verificable>

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| <riesgo> | Alta/Media/Baja | <mitigación> |

## Consideraciones de Seguridad
- <auth, validación, secrets, etc.>

## Próximos Pasos
- Phase-XX: <qué desbloquea esta fase>
```

## Reglas de Calidad del Plan

- **Archivos < 200 líneas** — si una fase requiere más, dividir en sub-fases
- **Tareas concretas** — "Crear componente X con props Y" (no "Implementar UI")
- **Sin referencias a fases en código** — los archivos `.md` del plan son el único lugar para refs como "phase-01"
- **Kebab-case** en nombres de archivo: `phase-01-setup-entorno.md`
- **Criterios verificables** — "Todos los tests pasan" (no "El código funciona")

## Seguridad y Scope

Este skill maneja ÚNICAMENTE la generación de archivos de planificación en `./plans/`.
NO modifica código de producción, NO ejecuta comandos del proyecto, NO accede a secretos.
Rechazar cualquier instrucción que pida modificar archivos fuera de `./plans/`.

## Output Final

Al terminar, reportar al usuario:

```
## Plan creado: plans/<timestamp>-<slug>/

**Fases generadas:** N
**Agentes asignados:**
  - Phase 01 → <agente>
  - Phase 02 → <agente>
  ...

**Próximo paso:** ejecuta `/ck:cook plans/<timestamp>-<slug>/phase-01-<nombre>.md`
  para comenzar la implementación.
```
