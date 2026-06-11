# Phase-06: Frontend Astro 6.4 — Landing y Formulario

## Overview
- **Prioridad:** High
- **Estado:** completed
- **Agente:** `fullstack-developer`
- **Dependencias:** phase-02
- **Estimación:** 4-5 días

## Descripción
Implementar el frontend Astro 6.4 con la landing page (SSG + server islands), el formulario de participación (React 19 island, SSR) y la página de validación de código, integrados con la API FastAPI.

## Contexto
- [Phase-02](./phase-02-dominio-codigos.md) — API `POST /validate` disponible
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — secciones 2, 3 y 7.3
- `ASTRO_KEY` ya generada en phase-01
- Tipos TypeScript generados desde OpenAPI de FastAPI (`src/types/api.d.ts`)

## Requisitos
### Funcionales
- [x] Landing page `/` — SSG con hero, cómo participar, premios, countdown, footer legal
- [ ] Server island `CounterIsland` — contador de premios restantes *(no implementado en esta fase)*
- [x] Página `/participar` — SSR con formulario React 19 island (`client:load`)
- [x] Página `/validar` — SSR, acepta código via POST (nunca GET), redirige a `/ruleta` — verificado 405 en vivo
- [ ] Páginas legales `/bases-legales`, `/faq`, `/privacidad` — SSG *(pendiente)*
- [x] Formulario con campos: código, nombre, email, consentimientos *(sin apellidos/ciudad/fuente — simplificado según plan de campaña)*

### No Funcionales
- [ ] LCP < 2.5s en móvil 4G (Core Web Vitals) *(no medido aún)*
- [ ] Accesible: WCAG 2.1 AA *(no auditado aún)*
- [x] Responsive mobile-first (Tailwind CSS)
- [ ] `noindex` en `/validar`, `/ruleta`, `/resultado/*` *(pendiente)*
- [x] CSP configurado en headers Astro

## Arquitectura
```
src/pages/
├── index.astro          (prerender=true, SSG)
├── participar.astro     (SSR)
├── validar.astro        (SSR, solo POST)
├── bases-legales.astro  (prerender=true, SSG)
├── faq.astro            (prerender=true, SSG)
└── privacidad.astro     (prerender=true, SSG)

src/components/
├── ParticipationForm.tsx   (island, client:load)
├── CounterIsland.astro     (server island, server:defer)
├── Countdown.tsx           (island, client:visible)
└── ui/                     (Button, Input, Select — Tailwind)
```

## Archivos Relacionados
### Crear
- `frontend/src/pages/index.astro`
- `frontend/src/pages/participar.astro`
- `frontend/src/pages/validar.astro`
- `frontend/src/pages/bases-legales.astro`
- `frontend/src/pages/faq.astro`
- `frontend/src/pages/privacidad.astro`
- `frontend/src/components/ParticipationForm.tsx`
- `frontend/src/components/CounterIsland.astro`
- `frontend/src/components/Countdown.tsx`
- `frontend/src/layouts/Base.astro`
- `frontend/src/lib/api-client.ts`
- `frontend/src/types/api.d.ts` — generado con `openapi-typescript`

## Pasos de Implementación
1. Generar tipos TypeScript desde OpenAPI: `npx openapi-typescript $API_URL/openapi.json -o src/types/api.d.ts`
2. Crear `Base.astro` con meta tags, CSP, favicon y Tailwind
3. Implementar landing `/` con SSG + `CounterIsland` (server:defer)
4. Crear `ParticipationForm.tsx` con validación client-side (Zod) + submit a FastAPI
5. Implementar `/participar.astro` con CSRF token en SSR + island del formulario
6. Implementar `/validar.astro` — rechazar GET, validar código en SSR, redirect a `/ruleta`
7. Añadir `export const prerender = true` a páginas estáticas
8. Configurar `<meta name="robots" content="noindex">` en rutas privadas
9. Test en móvil real (Chrome DevTools 4G throttling): LCP < 2.5s

## Todo List
- [ ] Landing renderiza en SSG y pasa Lighthouse score ≥ 90 *(pendiente auditoría Lighthouse)*
- [ ] `CounterIsland` muestra datos actualizados sin recompilar *(no implementado)*
- [x] Formulario valida campos requeridos antes de enviar — consent_legal obligatorio
- [x] Formulario muestra error claro si código inválido (409→"ya usado", 422→"acepta términos")
- [x] `/validar` rechaza GET con 405 Method Not Allowed — verificado en vivo
- [ ] Páginas legales tienen `prerender=true` confirmado en build *(pendiente)*
- [ ] `noindex` presente en `/validar`, `/ruleta`, `/resultado/*` *(pendiente)*
- [ ] Responsive verificado en 320px, 768px y 1440px *(pendiente auditoría visual)*

## Criterios de Éxito
- [ ] Lighthouse Performance ≥ 90 en móvil para `/` *(pendiente)*
- [x] Formulario completo funciona end-to-end con API real (no mock) — verificado en vivo
- [ ] LCP < 2.5s en Chrome DevTools con throttling 4G *(pendiente)*
- [ ] 0 errores de consola en producción *(pendiente)*

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Código expuesto en URL via GET | Alta si no se controla | `/validar` solo acepta POST; redirect 405 en GET |
| LCP degradado por imagen hero sin optimizar | Media | Usar `astro:assets` con AVIF/WebP y `loading="eager"` en hero |
| Hidratación React island fallida en conexión lenta | Baja (Astro 6.3+ resiliente) | Mostrar skeleton/loader mientras hidrata |

## Consideraciones de Seguridad
- CSRF token en formulario SSR (cookie SameSite=Strict)
- `Content-Security-Policy` configurado en `astro.config.mjs`
- Código del billete nunca en URL, siempre en POST body
- `X-Frame-Options: DENY` para evitar clickjacking

## Próximos Pasos
- Phase-07: ruleta y panel admin dependen de las rutas SSR creadas aquí
