# Phase-02: Dominio de Códigos (SDD)

## Overview
- **Prioridad:** High
- **Estado:** pending
- **Agente:** `backend-specialist`
- **Dependencias:** phase-01
- **Estimación:** 3-4 días

## Descripción
Implementar el bounded context `codes`: generación/importación de los 45.000 códigos únicos, validación atómica (un solo uso por código), y API de consulta para el frontend.

## Contexto
- [Phase-01](./phase-01-setup-infraestructura.md) — DB y Alembic operativos
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 5.2 (patrón SSR → FastAPI)

## Requisitos
### Funcionales
- [ ] Modelo `Code` con campos: `id`, `code` (único), `status` (unused/used/invalid), `activated_at`, `used_at`, `created_at`
- [ ] Endpoint `POST /api/v1/codes/validate` — valida y marca como usado (atómico)
- [ ] Endpoint `GET /api/v1/codes/{code}/status` — consulta estado sin marcar
- [ ] Endpoint `POST /api/v1/admin/codes/import` — importación batch desde CSV (solo admin)
- [ ] Generación de formato de código configurable (ej: `MP-XXXX-XXXX-XXXX`)

### No Funcionales
- [ ] Validación atómica con `SELECT FOR UPDATE` o advisory lock PostgreSQL
- [ ] Redis caché del estado del código (TTL 60s) para reducir reads a DB
- [ ] Rate limiting: máx 5 intentos de validación por IP en 10 minutos
- [ ] Respuesta < 200ms en p95 bajo carga

## Arquitectura
```
POST /api/v1/codes/validate
  → rate_limit_check (Redis)
  → BEGIN TRANSACTION
  → SELECT code FOR UPDATE WHERE code=? AND status='unused'
  → UPDATE status='used', used_at=now(), participation_ip=?
  → COMMIT
  → invalidar caché Redis
  → return {valid: true, participation_id: uuid}
```

## Archivos Relacionados
### Crear
- `backend/app/domains/codes/models.py` — modelo SQLAlchemy `Code`
- `backend/app/domains/codes/schemas.py` — schemas Pydantic (request/response)
- `backend/app/domains/codes/service.py` — lógica de validación atómica
- `backend/app/domains/codes/router.py` — endpoints FastAPI
- `backend/app/domains/codes/cache.py` — helpers Redis para caché de estado
- `backend/alembic/versions/001_codes_domain.py` — migración

## Pasos de Implementación
1. Crear modelo `Code` con índice único en `code` y índice en `status`
2. Implementar `CodeService.validate_code()` con transacción atómica
3. Implementar caché Redis: leer estado → cache miss → DB → set cache
4. Crear router con los 3 endpoints (validate, status, import)
5. Añadir middleware de rate limiting por IP (slowapi o custom Redis)
6. Escribir migración Alembic para la tabla `codes`
7. Probar importación del CSV de 45.000 códigos con el script de phase-01
8. Verificar atomicidad con test de concurrencia (2 requests simultáneos al mismo código)

## Todo List
- [ ] Modelo `Code` creado con índices correctos
- [ ] Migración aplicada sin errores
- [ ] `POST /validate` devuelve 200 en código válido, 409 en código ya usado, 404 en código inexistente
- [ ] Dos requests simultáneos al mismo código → solo uno gana (test de concurrencia)
- [ ] Redis cachea correctamente el estado
- [ ] Rate limiting activo: 6º intento desde misma IP rechazado con 429
- [ ] 45.000 códigos importados correctamente

## Criterios de Éxito
- [ ] Test de concurrencia con 10 requests simultáneos al mismo código: exactamente 1 exitoso
- [ ] p95 de `POST /validate` < 200ms bajo 500 VUs concurrentes
- [ ] 0 códigos duplicados tras importación masiva

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Race condition en validación simultánea | Alta sin transacción | `SELECT FOR UPDATE` obligatorio; test de concurrencia en CI |
| Códigos expuestos en logs del servidor | Media | Enmascarar últimos 4 chars en logs; nunca loggear código completo |
| CSV con duplicados del proveedor | Baja | Script de importación verifica unicidad antes de insertar |

## Consideraciones de Seguridad
- Códigos en POST body, nunca en URL (evitar logs de Nginx/CDN)
- Enmascarar código en logs: `MP-XXXX-XXXX-****`
- IP del participante registrada en la validación (RGPD: informar en bases legales)
- Endpoint de importación solo accesible con token de admin

## Próximos Pasos
- Phase-03: el motor de ruleta necesita `participation_id` generado aquí
- Phase-06: el formulario frontend llama a `POST /validate`
