import type { APIRoute } from "astro";

export const GET: APIRoute = () => {
  return new Response(
    JSON.stringify({ status: "ok", service: "astro" }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }
  );
};
