# Plan: MP Billete Dorado 2026 — Plataforma Promocional

**Fecha:** 2026-06-10
**Objetivo:** Construir la plataforma web completa para la campaña promocional nacional "MP Billete Dorado 2026", con validación de códigos únicos, ruleta de premios con desbloqueo progresivo y sistema de comunicación automatizada.
**Tech stack detectado:** Python/FastAPI · PostgreSQL · Redis · Celery · Astro 6.4 · React 19 · Tailwind CSS · Docker · pnpm 11 · SDD

## Fases

| #  | Fase                              | Agente               | Estado  | Dependencias       |
|----|-----------------------------------|----------------------|---------|--------------------|
| 01 | Setup e Infraestructura           | `backend-specialist` | completed | —                |
| 02 | Dominio de Códigos (SDD)          | `backend-specialist` | pending | phase-01           |
| 03 | Motor de Ruleta y Premios         | `backend-specialist` | pending | phase-02           |
| 04 | Participantes, Auth y Fraude      | `backend-specialist` | pending | phase-02           |
| 05 | Notificaciones y Email Automation | `backend-specialist` | pending | phase-03, phase-04 |
| 06 | Frontend Astro 6.4 (Landing + Formulario) | `fullstack-developer` | pending | phase-02        |
| 07 | Frontend Ruleta + Panel Admin     | `fullstack-developer` | pending | phase-03, phase-06 |
| 08 | Tests, Carga y QA                 | `tester`             | pending | phase-07           |

## Contexto del Proyecto

Proyecto nuevo sin código fuente aún. El stack es Python/FastAPI como backend con dominio SDD (8 bounded contexts), y Astro 6.4 en modo híbrido SSG/SSR como frontend con React 19 islands. La campaña arranca el 15-jun-2026; hay 45.000 billetes físicos con códigos únicos ya impresos (a confirmar) y se esperan 35.000 participaciones en 3.5 meses.

## Referencias

- [Phase 01 — Setup e Infraestructura](./phase-01-setup-infraestructura.md)
- [Phase 02 — Dominio de Códigos](./phase-02-dominio-codigos.md)
- [Phase 03 — Motor de Ruleta y Premios](./phase-03-motor-ruleta-premios.md)
- [Phase 04 — Participantes, Auth y Fraude](./phase-04-participantes-auth-fraude.md)
- [Phase 05 — Notificaciones y Email Automation](./phase-05-notificaciones-email.md)
- [Phase 06 — Frontend Landing y Formulario](./phase-06-frontend-landing-formulario.md)
- [Phase 07 — Frontend Ruleta y Panel Admin](./phase-07-frontend-ruleta-admin.md)
- [Phase 08 — Tests, Carga y QA](./phase-08-tests-carga-qa.md)
- [Informe Astro 6.4](../reports/astro-6-research-report.md)
