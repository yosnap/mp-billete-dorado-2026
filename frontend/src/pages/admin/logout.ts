import type { APIRoute } from "astro";
import { clearAdminCookie } from "../../lib/auth";

/**
 * GET /admin/logout — invalida la cookie admin_token y redirige al login.
 */
export const GET: APIRoute = () => {
  return new Response(null, {
    status: 302,
    headers: {
      Location: "/admin/login",
      "Set-Cookie": clearAdminCookie(),
    },
  });
};
