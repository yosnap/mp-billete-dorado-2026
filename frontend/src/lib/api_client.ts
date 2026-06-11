import type {
  CodeValidateResponse,
  ParticipantRegisterRequest,
  ParticipantRegisterResponse,
  PrizeItem,
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
};
