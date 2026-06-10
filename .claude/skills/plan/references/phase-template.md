# Plantilla Completa de Fase — mp:plan

Referencia para generar archivos `phase-XX-<nombre>.md` con contenido completo.

## Plantilla

```markdown
# Phase-XX: <Nombre de la Fase>

## Overview
- **Prioridad:** High | Medium | Low
- **Estado:** pending
- **Agente:** <frontend-development | backend-specialist | tester | code-reviewer | docs-manager | devops | researcher>
- **Dependencias:** phase-XX | Ninguna
- **Estimación:** <N horas | N días>

## Descripción
<1-2 oraciones explicando qué se construye o cambia en esta fase>

## Contexto
- [Plan maestro](./plan.md)
- [Phase anterior](./phase-XX-anterior.md) — si aplica
- [Arquitectura del sistema](../../docs/system-architecture.md) — si existe
- Archivos clave a leer antes de implementar: `<rutas>`

## Requisitos

### Funcionales
- [ ] <requisito concreto 1>
- [ ] <requisito concreto 2>
- [ ] <requisito concreto 3>

### No Funcionales
- [ ] Tiempo de respuesta < X ms (si aplica)
- [ ] Cobertura de tests >= X%
- [ ] Sin vulnerabilidades OWASP críticas

## Arquitectura

### Componentes involucrados
- `<ComponenteA>` — propósito
- `<ServicioB>` — propósito

### Decisiones técnicas
- <decisión y razón>
- <patrón elegido y por qué>

### Flujo de datos
<descripción breve del flujo: qué entra, qué se procesa, qué sale>

## Archivos Relacionados

### Modificar
- `src/<ruta/archivo.ts>` — <qué se cambia y por qué>

### Crear
- `src/<ruta/nuevo.ts>` — <propósito del archivo>

### Leer (solo referencia)
- `src/<ruta/referencia.ts>` — <qué información provee>

## Pasos de Implementación

1. <Paso específico y ejecutable — qué hacer exactamente>
2. <Paso específico — incluir nombre de función, componente o endpoint>
3. <Paso específico — incluir validaciones o casos borde importantes>
4. Verificar compilación sin errores
5. Correr tests relevantes

## Todo List

- [ ] <tarea atómica 1>
- [ ] <tarea atómica 2>
- [ ] <tarea atómica 3>
- [ ] Verificar que no hay errores de compilación
- [ ] Confirmar que los tests de esta fase pasan

## Criterios de Éxito

- [ ] <criterio técnico verificable — ej: "Endpoint POST /users retorna 201 con user_id">
- [ ] <criterio de calidad — ej: "Sin errores de TypeScript">
- [ ] <criterio de tests — ej: "Tests de integración pasan en CI">
- [ ] Ningún archivo supera 200 líneas
- [ ] Sin secretos hardcodeados

## Riesgos

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| <riesgo técnico> | Alta / Media / Baja | <acción concreta de mitigación> |
| Conflicto de archivos con otra fase | Media | Verificar ownership antes de iniciar |

## Consideraciones de Seguridad

- Validar inputs en boundaries del sistema (no confiar en datos del cliente)
- Variables de entorno para credenciales (nunca hardcodear)
- <auth/autorización requerida para los endpoints de esta fase>
- <sanitización de datos si aplica>

## Próximos Pasos

Una vez completada esta fase:
- **Desbloquea:** phase-XX — <nombre>
- **Entregar a:** <agente de la siguiente fase>
- **Verificar con:** `tester` antes de pasar a la siguiente fase
```

## Guía de Agentes por Dominio

| Si la fase involucra... | Usar agente |
|------------------------|-------------|
| Componentes React, TypeScript, UI, hooks, estilos | `frontend-development` |
| Rutas, páginas Next.js, SSR, RSC | `frontend-development` |
| REST API, GraphQL, lógica de negocio | `backend-specialist` |
| Base de datos, schemas, migraciones | `backend-specialist` |
| OAuth, JWT, sesiones, permisos | `backend-specialist` |
| Tests unitarios, integración, e2e | `tester` |
| Revisión de código, standards | `code-reviewer` |
| Documentación técnica, README, ADR | `docs-manager` |
| Docker, CI/CD, Kubernetes | `devops` |
| Investigación de librerías/patrones | `researcher` |

## Ejemplos de Criterios de Éxito por Tipo

### Backend
- `GET /api/users` retorna lista paginada con status 200
- Validación de inputs rechaza datos malformados con 422
- JWT se verifica correctamente en middleware
- Queries de DB usan índices (sin full table scans)

### Frontend
- Componente renderiza sin errores en casos vacíos, loading y error
- Accesibilidad: todos los inputs tienen labels asociados
- Responsive: funciona en viewport 375px y 1440px
- Sin warnings de React en consola

### Tests
- Cobertura de líneas >= 80%
- Tests de happy path y casos borde documentados
- Tests de integración usan base de datos real (no mocks)
- Ningún test ignorado con `skip` o `xfail` sin razón documentada
