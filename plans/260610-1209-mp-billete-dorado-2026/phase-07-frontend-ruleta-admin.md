# Phase-07: Frontend Astro 6.4 — Ruleta y Panel Admin

## Overview
- **Prioridad:** High
- **Estado:** pending
- **Agente:** `fullstack-developer`
- **Dependencias:** phase-03, phase-06
- **Estimación:** 4-5 días

## Descripción
Implementar la animación de la Ruleta MP (React 19 island con Canvas/CSS), la página de resultado, y el panel admin interno para gestión de premios, visualización de fraude y seguimiento de campaña.

## Contexto
- [Phase-03](./phase-03-motor-ruleta-premios.md) — API `POST /roulette/spin` disponible
- [Phase-06](./phase-06-frontend-landing-formulario.md) — layouts y rutas SSR base creados
- [Informe Astro 6.4](../reports/astro-6-research-report.md) — sección 3.2 (directiva `client:visible`)

## Requisitos
### Funcionales
- [ ] Página `/ruleta` — SSR + island `RouletteWheel` (`client:load`)
- [ ] Animación de ruleta: giro progresivo, desaceleración, revelación del resultado
- [ ] Página `/resultado/[id]` — SSR, muestra premio ganado o mensaje de ánimo
- [ ] Panel admin `/admin` — SSR con autenticación básica (token en cookie httpOnly)
- [ ] Admin: tabla de participaciones en tiempo real
- [ ] Admin: gestión de premios (toggle activo/inactivo, stock restante)
- [ ] Admin: listado de flags de fraude con acción de invalidar
- [ ] Admin: contador global de participaciones y ganadores por categoría

### No Funcionales
- [ ] Animación de ruleta accesible: `prefers-reduced-motion` respetado
- [ ] `/admin/*` con `noindex` y protección de ruta (redirect si no autenticado)
- [ ] Panel admin usable en tablet (mínimo 768px)
- [ ] Ruleta no bloquea el hilo principal (Web Worker o requestAnimationFrame)

## Arquitectura
```
src/pages/
├── ruleta.astro              (SSR — verifica sesión válida)
├── resultado/[id].astro      (SSR — muestra resultado por ID)
└── admin/
    ├── index.astro           (SSR — dashboard)
    ├── premios.astro         (SSR — gestión de premios)
    └── fraude.astro          (SSR — flags y auditoría)

src/components/
├── RouletteWheel.tsx         (island, client:load)
├── ResultCard.tsx            (island, client:load)
└── admin/
    ├── PrizesTable.tsx       (island, client:load)
    ├── FraudTable.tsx        (island, client:load)
    └── StatsBar.tsx          (island, client:idle)
```

## Archivos Relacionados
### Crear
- `frontend/src/pages/ruleta.astro`
- `frontend/src/pages/resultado/[id].astro`
- `frontend/src/pages/admin/index.astro`
- `frontend/src/pages/admin/premios.astro`
- `frontend/src/pages/admin/fraude.astro`
- `frontend/src/components/RouletteWheel.tsx`
- `frontend/src/components/ResultCard.tsx`
- `frontend/src/components/admin/PrizesTable.tsx`
- `frontend/src/components/admin/FraudTable.tsx`
- `frontend/src/components/admin/StatsBar.tsx`
- `frontend/src/lib/auth.ts` — helper de verificación de sesión admin

## Pasos de Implementación
1. Crear `/ruleta.astro` en SSR: verificar `participation_id` en sesión, llamar `POST /spin`
2. Implementar `RouletteWheel.tsx` con animación CSS `@keyframes` + `requestAnimationFrame`
3. Añadir soporte `prefers-reduced-motion`: mostrar resultado directamente sin animación
4. Crear `/resultado/[id].astro` en SSR: fetch del resultado, renderizar `ResultCard`
5. Implementar middleware de auth admin en `src/middleware.ts` (cookie httpOnly)
6. Crear dashboard admin con stats globales (TanStack Query para polling cada 30s)
7. Implementar `PrizesTable` con toggle activo/inactivo via API admin
8. Implementar `FraudTable` con paginación y botón de invalidar participación
9. Test manual del flujo completo: código → formulario → ruleta → resultado → email

## Todo List
- [ ] Animación de ruleta gira y se detiene en el resultado correcto
- [ ] `prefers-reduced-motion` muestra resultado sin animación
- [ ] `/resultado/[id]` renderiza premio correcto para ganadores
- [ ] `/resultado/[id]` renderiza mensaje de ánimo para no ganadores
- [ ] `/admin` redirige a login si no hay cookie de sesión
- [ ] Admin puede toggle activo/inactivo en cualquier premio
- [ ] Admin puede invalidar participación fraudulenta
- [ ] Stats del dashboard se actualizan cada 30s sin recargar página

## Criterios de Éxito
- [ ] Flujo completo end-to-end funciona sin errores en móvil y escritorio
- [ ] Animación de ruleta completa en 3-5s con desaceleración suave
- [ ] Admin puede gestionar premios y fraude sin conocimientos técnicos
- [ ] 0 errores de consola en flujo de ruleta

## Riesgos
| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| Animación pesada en móviles antiguos | Media | CSS transforms GPU-accelerated; fallback `prefers-reduced-motion` |
| `/ruleta` accesible sin código válido (URL directa) | Alta sin control | Verificar `participation_id` en sesión SSR; redirect a `/participar` si ausente |
| Panel admin expuesto a Internet | Alta sin auth | Middleware de auth obligatorio; considerar restricción por IP en Nginx |

## Consideraciones de Seguridad
- Sesión admin con cookie `httpOnly`, `Secure`, `SameSite=Strict`
- `/admin/*` nunca indexable (noindex + Nginx deny por IP si posible)
- `participation_id` en sesión server-side, nunca en URL
- Resultado del spin obtenido server-side, no client-side (evita manipulación)

## Próximos Pasos
- Phase-08: tests E2E del flujo completo y test de carga sobre ruleta
