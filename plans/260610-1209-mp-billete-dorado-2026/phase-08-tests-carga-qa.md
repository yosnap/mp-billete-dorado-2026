# Phase-08: Tests, Carga y QA

## Overview
- **Prioridad:** High
- **Estado:** pending
- **Agente:** `tester`
- **Dependencias:** phase-07
- **Estimación:** 3-4 días

## Descripción
Validar la plataforma completa mediante tests unitarios, integración, E2E y pruebas de carga antes del lanzamiento del 15-jun-2026. Objetivo: garantizar que el sistema aguanta 2.000 usuarios concurrentes sin degradación y que el flujo completo funciona sin errores.

## Contexto
- [Phase-07](./phase-07-frontend-ruleta-admin.md) — código completo disponible
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 4.3 (plan de carga k6)
- Fecha límite: todo debe pasar antes del 15-jun-2026

## Requisitos
### Funcionales
- [ ] Tests unitarios backend: dominios `codes`, `prizes`, `participants`, `fraud`, `notifications`
- [ ] Test de concurrencia: validación simultánea del mismo código (race condition)
- [ ] Test de concurrencia: spin simultáneo sobre el último premio especial
- [ ] Tests E2E con Playwright: flujo completo código → formulario → ruleta → resultado → email
- [ ] Test de carga k6: 2.000 VUs sobre hot paths críticos
- [ ] Test de regresión: verificar que todos los tests pasan tras cada cambio

### No Funcionales
- [ ] Cobertura de tests backend ≥ 80%
- [ ] p95 < 400ms para rutas SSR bajo 2.000 VUs
- [ ] p95 < 100ms para rutas SSG cacheadas (desde CDN)
- [ ] 0 errores 5xx bajo carga normal (500 VUs)

## Arquitectura de Tests

### Backend (pytest)
```
backend/tests/
├── unit/
│   ├── test_code_validation.py       — validación atómica, casos límite
│   ├── test_roulette_algorithm.py    — distribución estadística 35k spins
│   ├── test_phase_manager.py         — cambio de fase en cada umbral
│   ├── test_fraud_detector.py        — reglas de detección
│   └── test_email_templates.py       — render de las 9 plantillas
├── integration/
│   ├── test_full_participation.py    — flujo completo registro→spin→email
│   └── test_concurrent_codes.py     — race condition 10 requests simultáneos
└── conftest.py                        — fixtures DB de test
```

### Frontend (Playwright E2E)
```
frontend/tests/
├── e2e/
│   ├── landing.spec.ts               — landing carga, countdown, counter island
│   ├── participation-form.spec.ts    — formulario válido e inválido
│   ├── roulette-flow.spec.ts         — flujo completo hasta resultado
│   └── admin-panel.spec.ts           — login admin, toggle premios, fraude
```

### Carga (k6)
```
scripts/load-tests/
├── smoke-test.js                     — 10 VUs, 1 min (sanity check)
├── load-test.js                      — 500 VUs, 10 min (carga normal)
├── stress-test.js                    — 2000 VUs, 5 min (pico campaña)
└── spike-test.js                     — 0→2000 VUs en 30s (lanzamiento viral)
```

## Archivos Relacionados
### Crear
- `backend/tests/unit/test_code_validation.py`
- `backend/tests/unit/test_roulette_algorithm.py`
- `backend/tests/unit/test_phase_manager.py`
- `backend/tests/unit/test_fraud_detector.py`
- `backend/tests/integration/test_full_participation.py`
- `backend/tests/integration/test_concurrent_codes.py`
- `frontend/tests/e2e/roulette-flow.spec.ts`
- `frontend/tests/e2e/participation-form.spec.ts`
- `scripts/load-tests/stress-test.js`
- `scripts/load-tests/load-test.js`

## Pasos de Implementación
1. Configurar `conftest.py` con BD de test aislada (PostgreSQL en Docker)
2. Escribir tests unitarios del dominio `codes` (validación, uso único, rate limit)
3. Escribir test estadístico de ruleta: simular 35.000 spins, verificar distribución
4. Escribir tests de concurrencia con `asyncio.gather` (10 co-requests al mismo código)
5. Configurar Playwright con `baseURL` del entorno de staging
6. Escribir E2E del flujo completo (mock de email en staging, verificar EmailLog)
7. Ejecutar smoke test k6 (10 VUs) → corregir issues → load test (500 VUs) → stress test (2.000 VUs)
8. Documentar resultados de carga en `plans/reports/load-test-results.md`
9. Corregir todos los issues encontrados antes del go-live

## Todo List
- [ ] Tests unitarios pasan al 100% con cobertura ≥ 80%
- [ ] Test de concurrencia de código: 1 ganador de 10 simultáneos
- [ ] Test estadístico de ruleta: 4.835 ± 100 ganadores en 35.000 spins
- [ ] E2E flujo completo pasa en Chrome, Firefox y Safari mobile
- [ ] Smoke test k6 (10 VUs): 0 errores
- [ ] Load test k6 (500 VUs): p95 < 400ms, 0 errores 5xx
- [ ] Stress test k6 (2.000 VUs): p95 < 600ms, < 1% errores
- [ ] `ASTRO_KEY` compartida verificada en cluster de 4 instancias
- [ ] SPF/DKIM validados con MX Toolbox
- [ ] Resultados de carga documentados

## Criterios de Éxito
- [ ] 100% de tests unitarios e integración pasan en CI
- [ ] Flujo E2E completo pasa en 3 navegadores
- [ ] Stress test 2.000 VUs: p95 < 600ms y < 1% de errores
- [ ] 0 issues críticos o altos abiertos en el día del lanzamiento

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Tests de carga revelan cuello de botella en DB | Media | Añadir índices faltantes; escalar conexiones PostgreSQL |
| E2E flaky por animación de ruleta (timing) | Media | Usar `waitFor` de Playwright en lugar de timeouts fijos |
| Sin tiempo para corregir issues encontrados | Alta dado el deadline | Priorizar: críticos → altos → medios; lanzar con issues bajos abiertos si necesario |

## Consideraciones de Seguridad
- Tests de carga sobre entorno de staging, nunca sobre producción
- BD de test con datos sintéticos, nunca datos reales de participantes
- Credenciales de staging en variables de entorno del CI, nunca en código

## Próximos Pasos
- Go-live el 15-jun-2026 tras aprobación de todos los criterios de éxito
- Monitorización post-lanzamiento: Nginx logs, PostgreSQL slow queries, Celery task failures
