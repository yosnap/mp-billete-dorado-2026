# Phase-01: Setup e Infraestructura

## Overview
- **Prioridad:** High
- **Estado:** completed
- **Agente:** `backend-specialist`
- **Dependencias:** Ninguna
- **Estimación:** 3-4 días

## Descripción
Configurar el repositorio, entornos Docker, esquema base de datos inicial (SDD), CI/CD y variables de entorno para que todos los demás dominios puedan arrancar sobre una base sólida.

## Contexto
- Stack: Python 3.12+, FastAPI 0.115+, PostgreSQL 16, Redis 7, Celery, Astro 6.4, Node 22
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 2.2 y 7.2

## Requisitos
### Funcionales
- [ ] Repositorio Git con estructura monorepo (`backend/`, `frontend/`)
- [ ] Docker Compose con servicios: fastapi, postgres, redis, celery-worker, astro
- [ ] Variables de entorno documentadas por servicio (`.env.example`)
- [ ] Migraciones Alembic iniciales (una por dominio SDD)
- [ ] Script de carga inicial de los 45.000 códigos desde CSV

### No Funcionales
- [ ] Node 22 LTS en el contenedor Astro
- [ ] `ASTRO_KEY` generada y compartida entre todas las instancias
- [ ] Secrets nunca en repositorio (uso de `.env` local + CI secrets)
- [ ] Health-check endpoints en FastAPI y Astro

## Arquitectura
```
docker-compose
├── nginx (reverse proxy, SSL, rate-limit)
├── astro (Node 22, standalone, cluster PM2)
├── fastapi (uvicorn, 4 workers)
├── postgres:16
├── redis:7
└── celery-worker (mismo imagen que fastapi)
```

## Archivos Relacionados
### Crear
- `docker-compose.yml` — orquestación de todos los servicios
- `backend/pyproject.toml` — dependencias Python
- `backend/alembic.ini` + `backend/alembic/` — migraciones por dominio
- `backend/app/main.py` — entrada FastAPI
- `frontend/package.json` — Astro 6.4 + React 19 + Tailwind
- `frontend/astro.config.mjs` — config híbrida SSG/SSR
- `.env.example` — variables documentadas
- `scripts/load_codes.py` — carga de 45k códigos desde CSV
- `nginx/nginx.conf` — proxy, SSL, rate-limit

## Pasos de Implementación
1. Crear estructura de carpetas del monorepo
2. Inicializar `backend/` con FastAPI + SQLAlchemy async + Alembic
3. Inicializar `frontend/` con `npm create astro@latest` (plantilla mínima, Node 22)
4. Configurar `astro.config.mjs` con output `server`, adapter `node`, integrations React + Tailwind
5. Ejecutar `npx astro create-key` y guardar `ASTRO_KEY` como secret
6. Crear `docker-compose.yml` con los 5 servicios + volúmenes persistentes
7. Configurar Alembic con carpetas por dominio: `codes/`, `prizes/`, `participants/`, `fraud/`
8. Crear script `load_codes.py` que importe CSV → tabla `codes`
9. Configurar Nginx con rate-limit 100 req/s por IP, SSL, HTTP/2
10. Verificar que `docker-compose up` levanta todos los servicios sin errores

## Todo List
- [ ] Estructura de carpetas creada
- [ ] FastAPI arranca en Docker con `/health` OK
- [ ] Astro arranca en Docker con `/health` OK
- [ ] PostgreSQL accesible y migraciones iniciales aplicadas
- [ ] Redis accesible y Celery worker conectado
- [ ] Script de carga de códigos testeado con muestra de 100 códigos
- [ ] `.env.example` completo y documentado
- [ ] Nginx sirve tráfico a ambos servicios

## Criterios de Éxito
- [ ] `docker-compose up --build` levanta sin errores en entorno limpio
- [ ] `GET /health` devuelve 200 en FastAPI y Astro
- [ ] Alembic aplica todas las migraciones sin error
- [ ] Script de carga importa 45.000 códigos en < 30 segundos

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| CSV de códigos en formato inesperado del proveedor gráfico | Media | Pedir muestra de 10 códigos antes de imprimir |
| `ASTRO_KEY` olvidada en alguna instancia de producción | Alta | Documentar en runbook; CI falla si no está definida |
| Versiones exactas de `@astrojs/*` incompatibles | Media | Verificar contra npm en el momento del bootstrap |

## Consideraciones de Seguridad
- Secrets en variables de entorno, nunca hardcodeados
- Postgres no expuesto al exterior (solo red Docker interna)
- Redis con contraseña (`requirepass`)
- Nginx termina SSL; FastAPI y Astro solo escuchan en red interna

## Próximos Pasos
- Phase-02: dominio `codes` requiere que DB y Alembic estén operativos
- Phase-06: frontend requiere que `astro.config.mjs` base esté configurado
