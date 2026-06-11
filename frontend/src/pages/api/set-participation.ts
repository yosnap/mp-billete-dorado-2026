import type { APIRoute } from "astro";
import { buildParticipationCookie } from "../../lib/auth";

/**
 * POST /api/set-participation
 * Body JSON: { participation_id: string }
 *
 * Escribe el participation_id en una cookie httpOnly y responde con
 * { redirect: "/ruleta" } para que el cliente navegue server-side.
 *
 * Nunca expone el participation_id en la URL del navegador.
 */
export const POST: APIRoute = async ({ request }) => {
  let participationId: string | undefined;

  try {
    const body = await request.json() as { participation_id?: unknown };
    if (typeof body.participation_id === "string" && body.participation_id.trim()) {
      participationId = body.participation_id.trim();
    }
  } catch {
    return new Response(JSON.stringify({ error: "Body inválido." }), {
      status: 400,
      headers: { "Content-Type": "application/json" },
    });
  }

  if (!participationId) {
    return new Response(JSON.stringify({ error: "participation_id requerido." }), {
      status: 422,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(JSON.stringify({ redirect: "/ruleta" }), {
    status: 200,
    headers: {
      "Content-Type": "application/json",
      "Set-Cookie": buildParticipationCookie(participationId),
    },
  });
};
