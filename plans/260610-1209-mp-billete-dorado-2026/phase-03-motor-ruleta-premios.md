# Phase-03: Motor de Ruleta y Premios

## Overview
- **Prioridad:** High
- **Estado:** completed
- **Agente:** `backend-specialist`
- **Dependencias:** phase-02
- **Estimación:** 4-5 días

## Descripción
Implementar el bounded context `roulette` + `prizes`: motor probabilístico con desbloqueo progresivo por fases (0-25%, 25-50%, 50-75%, 75-100% de participaciones), asignación atómica de premios y API de resultado para la ruleta.

## Contexto
- [Phase-02](./phase-02-dominio-codigos.md) — genera `participation_id` que activa la ruleta
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 4.2 (Redis caché premios)
- Estrategia de premios: 4.835 premios / 35.000 participaciones = 13,82% probabilidad base

## Requisitos
### Funcionales
- [x] Modelo `Prize` con: `id`, `name`, `category` (special/medium/small), `total_quantity`, `remaining_quantity`, `unlock_at` (1-4), `is_active`
- [x] Modelo `PrizeAssignment`: `id`, `participation_id`, `prize_id`, `assigned_at`, `audit_seed`
- [x] Endpoint `POST /api/v1/prizes/spin` — gira la ruleta para una participación válida
- [x] Endpoint `GET /api/v1/prizes/catalog` — catálogo público (sin revelar stock exacto)
- [x] Endpoint `PUT /api/v1/admin/prizes/{id}/toggle` — bloquear/liberar premio (admin)
- [x] Lógica de desbloqueo progresivo por fase según % de participaciones totales

### No Funcionales
- [x] Asignación de premio atómica con advisory lock PostgreSQL
- [x] Sin doble asignación: una participación → máximo un premio
- [x] Catálogo de premios cacheado en Redis (TTL 30s)
- [x] Algoritmo auditable: `audit_seed` (valor del random) guardado en `PrizeAssignment`

## Arquitectura

### Fases de desbloqueo
```
FASE 1 (0–25%   = 0–8.750 participaciones):  premios pequeños + parte medios
FASE 2 (25–50%  = 8.750–17.500):             medios + primeros lotes premium
FASE 3 (50–75%  = 17.500–26.250):            más medios + primer iPad + primera beca
FASE 4 (75–100% = 26.250–35.000):            liberación total de todos los restantes
```

### Flujo de spin
```
POST /roulette/spin {participation_id}
  → verificar participation_id válido y sin premio previo
  → obtener fase actual (total_participations / 35000 * 100)
  → obtener premios disponibles para fase actual (caché Redis)
  → SELECT pg_try_advisory_lock(prize_id)
  → calcular probabilidad: 4835/35000 ≈ 13,82% base, ajustada por stock restante
  → si gana: INSERT PrizeAssignment + UPDATE stock_remaining - 1
  → COMMIT + invalidar caché
  → return {won: bool, prize: Prize|null}
```

## Archivos Relacionados
### Crear
- `backend/app/domains/prizes/models.py` — modelos `Prize`, `PrizeAssignment`
- `backend/app/domains/prizes/schemas.py` — schemas Pydantic
- `backend/app/domains/prizes/service.py` — lógica de spin y desbloqueo
- `backend/app/domains/prizes/phase_manager.py` — cálculo de fase actual
- `backend/app/domains/prizes/router.py` — endpoints FastAPI
- `backend/app/domains/prizes/cache.py` — caché Redis del catálogo
- `backend/alembic/versions/002_prizes_domain.py` — migración

## Pasos de Implementación
1. Crear modelos `Prize` y `PrizeAssignment` con constraints únicos
2. Migración Alembic + seed inicial con los 4.835 premios catalogados
3. Implementar `PhaseManager.get_current_phase()` basado en count de participaciones
4. Implementar `RouletteService.spin()` con advisory lock y lógica probabilística
5. Implementar invalidación de caché al cambiar stock o fase
6. Crear endpoints REST con autenticación admin para gestión de premios
7. Test unitario del algoritmo de probabilidad (mock de 35.000 spins → verificar ~4.835 ganadores)
8. Test de concurrencia: 50 spins simultáneos sobre el último iPhone → exactamente 1 ganador

## Todo List
- [x] Modelos y migración aplicados (0001→0004)
- [x] Seed de premios listo (`alembic/seeds/seed_prizes.py` — 4.835 premios en 3 categorías)
- [x] `POST /v1/prizes/spin` devuelve resultado correcto con y sin premio
- [x] Una participación no puede ganar dos premios (UNIQUE constraint + IntegrityError fallback)
- [x] Fase actual calculada correctamente en los 4 umbrales
- [x] Premios de fase futura no asignados hasta desbloquearse
- [ ] Test de 35.000 spins simulados: 4.835 ± 50 ganadores (pendiente F8)
- [x] Advisory lock previene doble asignación del mismo premio

## Criterios de Éxito
- [ ] 50 requests concurrentes al último premio especial → exactamente 1 asignado
- [ ] Distribución estadística de premios dentro del ±2% del target (13,82%)
- [ ] Cambio de fase activa premios correctos en < 1s
- [ ] `GET /prizes/catalog` responde en < 50ms (desde caché Redis)

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Race condition en último premio de categoría especial | Alta sin lock | Advisory lock + test de concurrencia obligatorio en CI |
| Distribución de premios desbalanceada al inicio | Media | Seed de premios con pesos por fase bien calibrados |
| Admin bloquea/desbloquea premio durante pico de tráfico | Baja | Invalidación de caché Redis inmediata al toggle |

## Consideraciones de Seguridad
- Endpoint admin con autenticación de token (no expuesto públicamente)
- No revelar stock exacto en API pública (solo categoría y disponibilidad booleana)
- Algoritmo de spin auditable: loggear seed + resultado para auditorías internas
- La estrategia de desbloqueo por fases es CONFIDENCIAL: nunca en respuesta pública de API

## Próximos Pasos
- Phase-04: participantes necesitan `participation_id` vinculado al resultado del spin
- Phase-05: notificaciones se disparan con el resultado de este módulo
- Phase-07: frontend de ruleta consume `POST /spin`
