# Informe Técnico: Astro 6.4 para MP Billete Dorado 2026

**Proyecto:** MP Billete Dorado 2026 – Plataforma de campaña promocional
**Fecha:** 2026-06-10
**Autor:** Project Manager (investigación delegada)
**Stack frontend objetivo:** Astro 6.4 + React 19 (islands) + Tailwind CSS
**Backend objetivo:** FastAPI + PostgreSQL + Redis + Celery
**Ventana de campaña:** 15 jun – 30 sep 2026 (≈ 35.000 participantes, 45.000 códigos)

---

## 1. Novedades de Astro 6.4 relevantes para el proyecto

Astro 6 (estable desde finales de 2025) y la serie 6.x acumulada hasta 6.4 introduce cambios estructurales que son **directamente útiles** para una campaña promocional de alto tráfico con tramos estáticos (landing, bases legales, FAQs) y tramos altamente dinámicos (validación de código, ruleta, panel de ganadores).

### 1.1 Astro 6 (base)

- **Servidor de desarrollo rediseñado** sobre Vite Environment API: `astro dev` se ejecuta en el mismo runtime que producción, eliminando la divergencia dev/prod. Esto es crítico para una campaña con SLA: lo que pasa en dev pasará en prod.
- **Live Collections (estable):** colecciones de contenido con datos en tiempo real (sin rebuild). Útil para mostrar el **contador de Billetes Dorados restantes**, marcador de premios entregados o ganadores recientes sin recompilar el sitio.
- **Content Security Policy (estable):** Astro genera headers o `<meta>` con hashes de scripts/estilos automáticamente. Esencial para una promoción nacional con requisitos legales y de protección al consumidor.
- **Cloudflare Workers (workerd) como runtime de primera clase:** acceso a KV, R2, Durable Objects, Analytics Engine. Útil si parte del front se despliega en edge.
- **Removidos:** `Astro.glob()`, `emitESMImage()`, `<ViewTransitions />` (sustituido por `<ClientRouter />`), legacy content collections.
- **Requisitos:** Node 22+ y Zod 4 (afecta validaciones en `actions`).
- **`SSRManifest`:** `serverIslandMappings` y `sessionDriver` ahora son **async** y requieren `await`.

### 1.2 Astro 6.3

- **Hidratación resiliente de islands:** si un island falla en cargar, el resto de la página sigue interactiva. Importante en móviles con conexiones lentas (la campaña es nacional y los participantes accederán desde 4G/5G variable).
- **Routing avanzado experimental con Hono** y mejoras en redirecciones de imágenes.

### 1.3 Astro 6.4 (versión objetivo)

- **Pipeline de Markdown pluggable** y nuevo procesador Markdown basado en Rust → builds significativamente más rápidos para las páginas legales (bases, política de privacidad, FAQ extensas).
- **Helpers de Cloudflare para routing avanzado:** facilita cache rules y splits geográficos.
- **Compatibilidad confirmada con React 19.x** (vía `@astrojs/react`).

> **Recomendación para MP Billete Dorado:** congelar la versión exacta en `6.4.x` (última patch estable) con `package.json` lockfile, y usar Node 22 LTS en producción.

---

## 2. Configuración SSR para rutas dinámicas (validación, ruleta, resultados)

### 2.1 Estrategia de renderizado recomendada: **híbrida**

No conviene poner toda la app en SSR puro. Astro 6 permite mezclar:

| Tipo de ruta | Modo recomendado | Motivo |
|---|---|---|
| `/` landing | **Prerender (SSG)** + Server Islands | Tráfico masivo; estática + fragmentos dinámicos |
| `/bases-legales`, `/faq`, `/como-participar` | **Prerender (SSG)** | Contenido fijo durante toda la campaña |
| `/participar` (formulario) | **SSR** | Necesita CSRF, sesión, validación servidor |
| `/validar/[codigo]` | **SSR** | Cada código es único, requiere consulta a BD |
| `/ruleta` | **SSR** + island React `client:load` | Auth de sesión + animación cliente |
| `/resultado/[id]` | **SSR** | Resultado por participación, no cacheable |
| `/admin/*` | **SSR** | Acceso autenticado |
| `/api/*` | Endpoints SSR | Proxy ligero hacia FastAPI si hace falta |

### 2.2 `astro.config.mjs` recomendado

```js
// astro.config.mjs
import { defineConfig } from 'astro/config';
import node from '@astrojs/node';
import react from '@astrojs/react';
import tailwind from '@astrojs/tailwind';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://billetedorado.mainpaper.com',
  output: 'server',                 // SSR por defecto
  adapter: node({ mode: 'standalone' }),
  integrations: [
    react(),                        // React 19 islands
    tailwind({ applyBaseStyles: true }),
    sitemap(),
  ],
  server: {
    host: true,                     // necesario para Docker/contenedor
    port: 4321,
  },
  security: {
    // Tamaño máximo body server-island; subir si vamos a serializar slots grandes
    serverIslandBodySizeLimit: 2 * 1024 * 1024, // 2 MB
  },
  experimental: {
    // Habilitar CSP estable (recomendado para campaña pública)
    // (En 6.x ya no es experimental; configurar en `security.csp`)
  },
  vite: {
    ssr: {
      // Externalizar libs pesadas que no necesitan bundling SSR
      noExternal: ['@astrojs/react'],
    },
  },
});
```

Marcar como **prerender** solo las rutas estáticas:

```astro
---
// src/pages/bases-legales.astro
export const prerender = true;
---
```

### 2.3 Clave estable para Server Islands (multi-instancia)

Para despliegues en cluster (PM2, Kubernetes, multi-región) **es obligatorio** fijar una clave de cifrado estable, de lo contrario cada instancia generará claves distintas y los islands fallarán:

```bash
npx astro create-key
# exportar el resultado como variable de entorno en TODAS las instancias
export ASTRO_KEY="..."
```

---

## 3. Integración Astro 6.4 + React 19 (islands interactivos)

### 3.1 Instalación

```bash
npx astro add react
# añade @astrojs/react y configura integración
npm install react@19 react-dom@19
```

### 3.2 Patrón de uso para los islands del proyecto

| Componente | Directiva recomendada | Justificación |
|---|---|---|
| Formulario de participación | `client:load` | Necesita interactividad inmediata al cargar |
| Animación de ruleta | `client:visible` | Solo hidrata cuando el usuario llega a la ruleta |
| Contador de premios restantes (server island + island reactivo) | `server:defer` + `client:idle` | El dato viene del servidor, polling ligero después |
| Modal de cookies/consentimiento | `client:idle` | No bloquea LCP |
| Captura de foto/ticket (si aplica) | `client:only="react"` | API de cámara solo en cliente |
| Banner promocional | sin directiva | Solo HTML estático |

### 3.3 Ejemplo: island del formulario

```astro
---
// src/pages/participar.astro
import Layout from '@/layouts/Base.astro';
import ParticipationForm from '@/components/ParticipationForm.tsx';
---
<Layout title="Participar">
  <ParticipationForm
    client:load
    apiBase={import.meta.env.PUBLIC_API_URL}
  />
</Layout>
```

```tsx
// src/components/ParticipationForm.tsx
import { useState } from 'react';

export default function ParticipationForm({ apiBase }: { apiBase: string }) {
  const [status, setStatus] = useState<'idle'|'sending'|'ok'|'err'>('idle');

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus('sending');
    const fd = new FormData(e.currentTarget);
    const r = await fetch(`${apiBase}/api/v1/participations`, {
      method: 'POST',
      body: fd,
      credentials: 'include',
    });
    setStatus(r.ok ? 'ok' : 'err');
  }
  // ...JSX
}
```

### 3.4 React 19 — gotchas a considerar

- React 19 introduce el **compilador** opcional. Compatible con Astro 6.4 pero **no activarlo en producción hasta haber medido**; en una campaña con SLA, estabilidad > optimización marginal.
- `useFormStatus` y `useActionState` se pueden usar dentro de islands, pero **no atraviesan el límite Astro → React**: las server actions de Next.js no existen aquí. Usar `astro:actions` o endpoints REST a FastAPI.
- Evitar `useEffect` para fetch — preferir SWR/TanStack Query, o hacer el fetch desde el `.astro` y pasar props al island.

---

## 4. Rendimiento bajo carga (≈35.000 participantes, picos esperables)

### 4.1 Modelo de carga estimado

Con 35.000 participantes en 3.5 meses y un patrón promocional típico (picos al inicio, fines de semana, sorteo final):

- **Pico realista:** 500–2.000 usuarios concurrentes en momentos de campaña amplificada (publi en redes, TV, prensa).
- **Hot paths críticos:** landing, validación de código, formulario, ruleta.

### 4.2 Estrategia de optimización en capas

#### Capa 1 — CDN delante de Astro (NO opcional)

- Servir landing y páginas legales **prerenderizadas** desde Cloudflare/Fastly/CloudFront con `Cache-Control: public, max-age=300, s-maxage=86400, stale-while-revalidate=604800`.
- **Server islands** se cachean independientemente con su propio TTL: el contador de premios restantes puede tener `Cache-Control: public, max-age=10` y refrescarse cada 10s globalmente.
- **Reglas:** invalidar caché en cambios de bases legales o textos legales mediante webhook al CDN.

#### Capa 2 — Astro Node en modo cluster

```bash
# ecosystem.config.cjs (PM2)
module.exports = {
  apps: [{
    name: 'mp-billete-dorado',
    script: './dist/server/entry.mjs',
    exec_mode: 'cluster',
    instances: 'max',          // un proceso por core
    max_memory_restart: '600M',
    env: {
      NODE_ENV: 'production',
      HOST: '0.0.0.0',
      PORT: 4321,
      ASTRO_KEY: process.env.ASTRO_KEY,
      PUBLIC_API_URL: 'https://api.billetedorado.mainpaper.com',
    },
  }],
};
```

- **Stateless:** Astro Node clusterizable solo si la sesión vive fuera del proceso → usar Redis (ya está en el stack) como `sessionDriver`.
- Nunca exponer puerto Node a Internet: detrás de **Nginx** con HTTP/2, Brotli, rate-limit por IP, y SSL terminado en Nginx.

#### Capa 3 — Server Islands para contenido dinámico

Server Islands permiten cachear la página completa de la landing mientras se inyecta dinámicamente un fragmento personalizado (premios restantes, último ganador). Patrón:

```astro
---
// src/pages/index.astro
export const prerender = true;
import CounterIsland from '@/components/CounterIsland.astro';
---
<Layout>
  <Hero />
  <CounterIsland server:defer>
    <p slot="fallback">Cargando…</p>
  </CounterIsland>
  <ComoParticipar />
</Layout>
```

- El cuerpo HTML va al CDN como estático.
- El `CounterIsland` se sirve por ruta separada, cachee-able 10s.
- **Pasar solo props mínimas** al island (ID o slug) — props grandes fuerzan POST y rompen caché de browser.

#### Capa 4 — Backend FastAPI con Redis

- Validación de códigos: caché en Redis con TTL corto (ej. 60s) por código consultado para reducir lecturas a PostgreSQL.
- Ruleta: precalcular o cachear catálogo de premios.
- Celery para tareas async (envío de email de confirmación, notificación a ganadores).

#### Capa 5 — Assets

- Astro `astro:assets` para optimización de imágenes (avatares de premios, logos de patrocinadores).
- Formatos AVIF/WebP automáticos.
- Servir desde CDN con cache de 1 año (hash en nombre de archivo).

### 4.3 Test de carga obligatorio antes del 15-jun

Plan de validación:

1. **k6** o **Artillery** simulando 2.000 VUs sobre `/`, `/participar`, `/validar/[codigo]`, `/ruleta`.
2. Objetivo: p95 < 400ms para SSR, < 100ms para SSG cacheado.
3. Validar que la clave `ASTRO_KEY` es compartida en cluster (probar con 4 instancias detrás de Nginx).
4. Probar invalidación de caché de CDN.

---

## 5. Integración con API Python/FastAPI

### 5.1 Patrón arquitectónico recomendado: **BFF ligero**

```
Browser → Astro Node (SSR + BFF) → FastAPI (lógica negocio) → PostgreSQL/Redis
                  ↑
                  └── CDN cachea HTML estático y server islands
```

**No** acoplar la lógica de negocio dentro de Astro. Astro hace:
- SSR de páginas
- Endpoints `/api/*` que **proxean** o **componen** llamadas a FastAPI
- Validación de sesión (cookie httpOnly emitida por FastAPI)
- Renderizado server-side de datos sensibles ya autenticados

FastAPI hace:
- Validación real de códigos (única fuente de verdad)
- Asignación de premios (lógica transaccional con PostgreSQL)
- Auth y emisión de tokens/cookies
- Webhooks a Celery

### 5.2 Patrón de llamada SSR (servidor Astro → FastAPI)

```astro
---
// src/pages/validar/[codigo].astro
const { codigo } = Astro.params;
const apiUrl = import.meta.env.API_INTERNAL_URL; // URL interna, no pública
const res = await fetch(`${apiUrl}/api/v1/codes/${codigo}`, {
  headers: {
    'X-Internal-Token': import.meta.env.INTERNAL_TOKEN,
    'Accept': 'application/json',
  },
});

if (!res.ok) {
  return Astro.redirect('/codigo-invalido');
}
const data = await res.json();
---
<Layout>
  <ResultadoValidacion data={data} client:load />
</Layout>
```

### 5.3 CORS y cookies

- Si Astro y FastAPI están bajo el mismo dominio (recomendado: `*.billetedorado.mainpaper.com` con subdominio `api.`), **usar cookies httpOnly con `SameSite=Lax`**.
- CORS en FastAPI:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://billetedorado.mainpaper.com"],
    allow_credentials=True,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)
```

- **Nunca `allow_origins=["*"]` con `allow_credentials=True`** — el navegador lo rechaza.

### 5.4 Validación de schema compartida

- Definir contratos OpenAPI en FastAPI.
- Generar tipos TypeScript con `openapi-typescript`:

```bash
npx openapi-typescript https://api.billetedorado.mainpaper.com/openapi.json -o src/types/api.d.ts
```

- Esto garantiza que cualquier cambio de schema en FastAPI rompa la build Astro antes de producción → alineado con SDD.

### 5.5 Astro Actions: usar o no

- Astro Actions resuelven validación con Zod, type-safety y RPC. **Útiles** para validaciones del lado Astro (formularios triviales), pero **la lógica de negocio debe vivir en FastAPI**, no en actions.
- Recomendación: usar Actions solo como capa fina de validación pre-envío y delegar a FastAPI.

---

## 6. Problemas identificados y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Server Islands no cacheables si props son grandes (>2KB en URL) | Media | Alto (saturación de origen) | Pasar IDs, no objetos; revisar URL en DevTools |
| `ASTRO_KEY` distinta entre instancias del cluster | Alta si no se gestiona | Alto (islands fallan) | Inyectar como secret en todas las instancias; documentar en runbook |
| Pico de tráfico al lanzamiento (15-jun) | Alta | Alto | Test de carga 1 semana antes; pre-warm de CDN |
| React 19 + bibliotecas no compatibles | Media | Medio | Auditar dependencias React antes de fase 2 |
| Migración Zod 3 → Zod 4 | Alta | Bajo | Refactor temprano; cambios menores |
| Sesiones perdidas al reiniciar Node | Alta sin Redis | Alto | `sessionDriver` con Redis desde día 1 |
| URLs públicas exponen códigos en logs | Alta | Crítico (privacidad) | Códigos en POST body, nunca en path GET indexable; `noindex` en `/validar/*` |
| Compilador React 19 inestable | Baja | Medio | NO activar en producción inicial |
| Build time creciente con muchas páginas legales | Baja | Bajo | Markdown Rust pipeline de 6.4 lo mitiga |
| CSP bloqueando scripts de analytics/píxeles | Media | Medio | Configurar `security.csp.directives` con hashes y dominios permitidos desde el inicio |

---

## 7. Recomendación de configuración inicial completa

### 7.1 `package.json` (extracto)

```json
{
  "engines": { "node": ">=22.0.0" },
  "dependencies": {
    "astro": "^6.4.0",
    "@astrojs/node": "^10.0.0",
    "@astrojs/react": "^5.0.0",
    "@astrojs/tailwind": "^7.0.0",
    "@astrojs/sitemap": "^4.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "tailwindcss": "^3.4.0",
    "zod": "^4.0.0"
  }
}
```

> Verificar versiones exactas en npm en la fase de bootstrapping; estos son los rangos esperables a junio 2026.

### 7.2 Variables de entorno mínimas

```bash
# .env.production
NODE_ENV=production
HOST=0.0.0.0
PORT=4321
ASTRO_KEY=<generado con `astro create-key`>
PUBLIC_API_URL=https://api.billetedorado.mainpaper.com
API_INTERNAL_URL=http://fastapi-internal:8000      # solo SSR
INTERNAL_TOKEN=<secreto compartido Astro↔FastAPI>
SESSION_DRIVER=redis
REDIS_URL=redis://redis:6379/0
```

### 7.3 Estructura de carpetas sugerida (SDD-friendly)

```
src/
├── pages/
│   ├── index.astro               # SSG + server islands
│   ├── bases-legales.astro       # SSG
│   ├── faq.astro                 # SSG
│   ├── participar.astro          # SSR
│   ├── validar/[codigo].astro    # SSR
│   ├── ruleta.astro              # SSR
│   ├── resultado/[id].astro      # SSR
│   ├── admin/                    # SSR + auth
│   └── api/
│       ├── proxy/[...path].ts    # BFF hacia FastAPI
│       └── health.ts
├── components/
│   ├── ParticipationForm.tsx     # island React 19
│   ├── RouletteWheel.tsx         # island React 19
│   ├── CounterIsland.astro       # server island
│   └── ui/                       # tailwind primitives
├── layouts/
│   └── Base.astro
├── lib/
│   ├── api-client.ts             # fetch tipado a FastAPI
│   └── session.ts
├── types/
│   └── api.d.ts                  # generado de OpenAPI
└── content/                      # markdown legal
    └── legal/
```

---

## 8. Próximos pasos accionables

1. **Bootstrap del proyecto** (Día 1–2): `npm create astro@latest` con plantilla mínima, fijar versiones, configurar `astro.config.mjs` propuesto.
2. **Contrato API** (Día 2–5): definir OpenAPI en FastAPI; generar `src/types/api.d.ts`.
3. **Skeleton de rutas** (Día 3–7): crear todas las páginas con placeholders y verificar matriz SSG/SSR.
4. **Integración React 19 island piloto** (Día 5–10): formulario de participación como primer island end-to-end con FastAPI.
5. **Cluster + Redis + Nginx** (Día 10–14): infraestructura productiva clonable.
6. **Test de carga** (Día 60+): k6 antes del lanzamiento 15-jun-2026.
7. **CSP y headers seguridad** (paralelo a desarrollo): configurar desde la primera build.

---

## Fuentes consultadas

- [Astro Docs — Server islands](https://docs.astro.build/en/guides/server-islands/)
- [Astro Docs — Islands architecture](https://docs.astro.build/en/concepts/islands/)
- [Astro Docs — Front-end frameworks](https://docs.astro.build/en/guides/framework-components/)
- [Astro Docs — Build forms with API routes](https://docs.astro.build/en/recipes/build-forms-api/)
- [Astro Docs — Actions](https://docs.astro.build/en/guides/actions/)
- [Astro Docs — Data fetching](https://docs.astro.build/en/guides/data-fetching/)
- [@astrojs/node adapter](https://docs.astro.build/en/guides/integrations-guide/node/)
- [Astro 6 Beta release notes](https://astro.build/blog/astro-6-beta/)
- [What's new in Astro – May 2026](https://astro.build/blog/whats-new-may-2026/)
- [What's new in Astro – March 2026](https://astro.build/blog/whats-new-march-2026/)
- [Astro 4.12: Server Islands](https://astro.build/blog/astro-4120/)
- [Astro 5.0 release](https://astro.build/blog/astro-5/)
- [Upgrade to Astro v6 guide](https://docs.astro.build/en/guides/upgrade-to/v6/)
- [Astro changelog](https://astro-changelog.netlify.app/)
- [PM2 Cluster Mode](https://pm2.keymetrics.io/docs/usage/cluster-mode/)
- [FastAPI Behind a Proxy](https://fastapi.tiangolo.com/advanced/behind-a-proxy/)
- [Astro Cloudflare deployment + SSR config](https://eastondev.com/blog/en/posts/dev/20251203-astro-cloudflare-deploy/)
- [Implementing ISR in Astro](https://logsnag.com/blog/implementing-isr-in-astro)
- [Server Islands cacheability issue #12975](https://github.com/withastro/astro/issues/12975)

---

**Status:** DONE
**Summary:** Informe técnico Astro 6.4 completo para MP Billete Dorado 2026, con 5 ejes investigados, configuración inicial, matriz SSG/SSR, riesgos y plan de acción.
**Concerns:** Las versiones exactas de `@astrojs/*` para Astro 6.4 deben confirmarse contra npm en el momento del bootstrap (junio 2026); los rangos están basados en la trayectoria de major bumps. Validar también compatibilidad de React 19.x con cualquier librería UI adicional que se elija (shadcn, Headless UI, etc.) antes de cerrar la fase de diseño.
