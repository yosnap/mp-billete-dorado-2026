/**
 * Helpers de autenticación para admin.
 * El token admin se verifica contra ADMIN_TOKEN env var (nunca expuesto al cliente).
 */

const ADMIN_TOKEN_COOKIE = "admin_token";
const PARTICIPATION_COOKIE = "participation_id";

/**
 * Lee el valor de una cookie por nombre desde el header Cookie de la request.
 */
export function getCookie(request: Request, name: string): string | null {
  const cookieHeader = request.headers.get("cookie") ?? "";
  for (const part of cookieHeader.split(";")) {
    const [key, ...rest] = part.trim().split("=");
    if (key?.trim() === name) {
      return decodeURIComponent(rest.join("=").trim());
    }
  }
  return null;
}

/**
 * Verifica si la request tiene una cookie admin_token válida.
 * Compara contra la variable de entorno ADMIN_TOKEN (server-side).
 */
export function isAdminAuthenticated(request: Request): boolean {
  const token = getCookie(request, ADMIN_TOKEN_COOKIE);
  if (!token) return false;
  const expected = import.meta.env.ADMIN_TOKEN;
  if (!expected) return false; // sin env var configurada, nunca autenticado
  return token === expected;
}

/**
 * Construye el Set-Cookie header para la cookie de sesión admin.
 */
export function buildAdminCookie(token: string): string {
  return [
    `${ADMIN_TOKEN_COOKIE}=${encodeURIComponent(token)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Strict",
    "Max-Age=28800", // 8 horas
    ...(import.meta.env.PROD ? ["Secure"] : []),
  ].join("; ");
}

/**
 * Cookie para limpiar la sesión admin (logout).
 */
export function clearAdminCookie(): string {
  return `${ADMIN_TOKEN_COOKIE}=; Path=/; HttpOnly; SameSite=Strict; Max-Age=0`;
}

/**
 * Obtiene el participation_id de la cookie de sesión (establecida server-side).
 */
export function getParticipationId(request: Request): string | null {
  return getCookie(request, PARTICIPATION_COOKIE);
}

/**
 * Construye el Set-Cookie header para guardar el participation_id en sesión.
 */
export function buildParticipationCookie(participationId: string): string {
  return [
    `${PARTICIPATION_COOKIE}=${encodeURIComponent(participationId)}`,
    "Path=/",
    "HttpOnly",
    "SameSite=Strict",
    "Max-Age=3600", // 1 hora
    ...(import.meta.env.PROD ? ["Secure"] : []),
  ].join("; ");
}
