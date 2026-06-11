import { defineMiddleware } from "astro:middleware";
import { isAdminAuthenticated } from "./lib/auth";

/**
 * Middleware global de Astro.
 * - Protege todas las rutas /admin/* excepto /admin/login.
 * - Si no hay cookie admin_token válida, redirige a /admin/login.
 */
export const onRequest = defineMiddleware(async (context, next) => {
  const { url, request } = context;
  const pathname = url.pathname;

  // Solo aplica protección a rutas admin (excluye la página de login)
  if (pathname.startsWith("/admin") && pathname !== "/admin/login") {
    if (!isAdminAuthenticated(request)) {
      return context.redirect("/admin/login", 302);
    }
  }

  return next();
});
