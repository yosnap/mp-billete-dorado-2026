import type {
  CodeValidateResponse,
  ParticipantRegisterRequest,
  ParticipantRegisterResponse,
  PrizeItem,
  SpinResult,
  AdminStats,
  AdminPrize,
  FraudListResponse,
} from "../types/api";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const BASE_URL = import.meta.env.PUBLIC_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      message = body?.detail ?? body?.message ?? message;
    } catch {
      // respuesta sin JSON — mantener mensaje genérico
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

export const apiClient = {
  validateCode(code: string): Promise<CodeValidateResponse> {
    return request<CodeValidateResponse>("/api/v1/codes/validate", {
      method: "POST",
      body: JSON.stringify({ code }),
    });
  },

  registerParticipant(
    data: ParticipantRegisterRequest,
  ): Promise<ParticipantRegisterResponse> {
    return request<ParticipantRegisterResponse>("/api/v1/participants/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getPrizesCatalog(): Promise<PrizeItem[]> {
    return request<PrizeItem[]>("/api/v1/prizes/catalog");
  },

  // --- Spin (server-side only; duplicado aquí para uso en SSR o islands) ---
  spinRoulette(participationId: string): Promise<SpinResult> {
    return request<SpinResult>("/api/v1/roulette/spin", {
      method: "POST",
      body: JSON.stringify({ participation_id: participationId }),
    });
  },

  getSpinResult(spinId: string): Promise<SpinResult> {
    return request<SpinResult>(`/api/v1/roulette/result/${spinId}`);
  },

  // --- Admin (requiere cookie admin_token en la request) ---
  adminGetStats(headers?: HeadersInit): Promise<AdminStats> {
    return request<AdminStats>("/api/v1/admin/stats", { headers });
  },

  adminGetPrizes(headers?: HeadersInit): Promise<AdminPrize[]> {
    return request<AdminPrize[]>("/api/v1/admin/prizes", { headers });
  },

  adminTogglePrize(
    prizeId: string,
    isActive: boolean,
    headers?: HeadersInit,
  ): Promise<AdminPrize> {
    return request<AdminPrize>(`/api/v1/admin/prizes/${prizeId}`, {
      method: "PATCH",
      body: JSON.stringify({ is_active: isActive }),
      headers,
    });
  },

  adminGetFraudFlags(
    page = 1,
    pageSize = 20,
    headers?: HeadersInit,
  ): Promise<FraudListResponse> {
    return request<FraudListResponse>(
      `/api/v1/admin/fraud?page=${page}&page_size=${pageSize}`,
      { headers },
    );
  },

  adminInvalidateFraud(flagId: string, headers?: HeadersInit): Promise<void> {
    return request<void>(`/api/v1/admin/fraud/${flagId}/invalidate`, {
      method: "POST",
      headers,
    });
  },
};
