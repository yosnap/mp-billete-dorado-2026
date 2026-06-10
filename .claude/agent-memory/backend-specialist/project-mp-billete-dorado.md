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

## Estado de fases

- Phase-01: DONE (Setup e Infraestructura)
- Phase-02 a 08: pending
