---
name: project-mp-billete-dorado
description: Context and architecture decisions for MP Billete Dorado 2026 promotional platform
metadata:
  type: project
---

Monorepo en `/sesion-1/` con `backend/` (FastAPI) y `frontend/` (Astro 6.4).

**Why:** Campaña promocional nacional, 45.000 billetes físicos, 35.000 participaciones esperadas. Arranca 15-jun-2026.

**How to apply:** Phase-02 en adelante depende de Alembic operativo. Astro necesita ASTRO_KEY en runtime.

## Decisiones de arquitectura (Phase-01)

- Códigos generados localmente por `scripts/load_codes.py`, NO importados de CSV externo. Formato: `MP-XXXX-XXXX-XXXX` (A-Z+0-9).
- Nginx solo HTTP (sin SSL) para desarrollo local; SSL va en producción.
- Postgres y Redis solo expuestos en red Docker interna (`expose`, no `ports`).
- Redis usa `requirepass` obligatorio.
- Alembic con branches por dominio: `codes`, `prizes`, `participants`, `fraud`.
- Celery timezone configurado a `America/Bogota`.
- FastAPI docs (`/docs`, `/redoc`) solo visibles cuando `DEBUG=true`.

## Decisiones de arquitectura (Phase-02)

- SDD: dominio `codes` en `backend/app/domains/codes/` (models, schemas, service, cache, router).
- Rate limiting custom Redis: INCR+EXPIRE por IP, ventana 10 min, máx 5 intentos. Sin slowapi (no estaba en deps).
- `SELECT FOR UPDATE` en transacción atómica garantiza exactamente 1 ganador en race condition.
- Caché Redis TTL=60s: cache hit en 'used'/'invalid' evita viaje a DB. Invalidación tras validación exitosa.
- Migración `codes_0002` añade `activated_at` y `participation_ip` sobre la `codes_0001` de Phase-01.
- `alembic.ini` corregido: `version_path_separator = space` (el formato multi-línea generaba una sola ruta inválida).
- Migración fraud corregida: `sa.JSONB()` → `postgresql.JSONB()` (SQLAlchemy no expone JSONB directamente).
- `upgrade heads` (plural) necesario para multi-branch Alembic; orden: fraud/prizes/codes → participants.
- Código enmascarado en logs: últimos 4 chars reemplazados por `****`.
- `admin_token` en config con default `"change-me-in-production"` — debe sobreescribirse con env var `ADMIN_TOKEN`.
- Script `scripts/generate_codes.py` genera CSV sin DB; `scripts/load_codes.py` inserta directamente en DB.

## Estado de fases

- Phase-01: DONE (Setup e Infraestructura)
- Phase-02: DONE (Dominio Códigos — validación atómica, caché Redis, rate limit, API admin)
- Phase-03 a 08: pending
